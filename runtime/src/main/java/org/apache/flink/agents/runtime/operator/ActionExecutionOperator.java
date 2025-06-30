package org.apache.flink.agents.runtime.operator;

import org.apache.flink.agents.api.Event;
import org.apache.flink.agents.api.InputEvent;
import org.apache.flink.agents.api.OutputEvent;
import org.apache.flink.agents.plan.Action;
import org.apache.flink.agents.plan.JavaFunction;
import org.apache.flink.agents.plan.PythonFunction;
import org.apache.flink.agents.plan.WorkflowPlan;
import org.apache.flink.agents.runtime.PythonActionExecutor;
import org.apache.flink.agents.runtime.PythonEvent;
import org.apache.flink.agents.runtime.context.RunnerContextImpl;
import org.apache.flink.agents.runtime.env.PythonEnvironmentManager;
import org.apache.flink.agents.runtime.message.EventMessage;
import org.apache.flink.api.common.operators.MailboxExecutor;
import org.apache.flink.api.common.state.ListState;
import org.apache.flink.api.common.state.ListStateDescriptor;
import org.apache.flink.api.common.state.ValueState;
import org.apache.flink.api.common.state.ValueStateDescriptor;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.apache.flink.python.PythonOptions;
import org.apache.flink.python.env.PythonDependencyInfo;
import org.apache.flink.streaming.api.operators.AbstractStreamOperator;
import org.apache.flink.streaming.api.operators.ChainingStrategy;
import org.apache.flink.streaming.api.operators.OneInputStreamOperator;
import org.apache.flink.streaming.runtime.streamrecord.StreamRecord;
import org.apache.flink.streaming.runtime.tasks.ProcessingTimeService;
import org.apache.flink.util.OutputTag;
import org.apache.flink.util.Preconditions;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Objects;

/**
 * An operator that executes the actions defined in the workflow plan. It receives {@link
 * EventMessage} from the {@link FeedbackOperator}, invokes the corresponding action, and collects
 * the action output event. For events of type {@link OutputEvent}, the output will be sent to a
 * side output; for all other event types, it will be forwarded to the {@link FeedbackSinkOperator}.
 *
 * <p>Note that this operator ensures that only one {@link Event} is processed at a time per
 * key.
 *
 * <p>NOTE: This code is adapted from the <a
 * href="https://github.com/apache/flink-statefun">flink-statefun</a>.
 *
 * @param <K> The type of the key of input event.
 */
public class ActionExecutionOperator<K> extends AbstractStreamOperator<EventMessage<K>>
        implements OneInputStreamOperator<EventMessage<K>, EventMessage<K>> {

    private static final Logger LOG = LoggerFactory.getLogger(ActionExecutionOperator.class);

    private static final long serialVersionUID = 1L;

    private final OutputTag<EventMessage<K>> sideOutputTag;

    private final transient MailboxExecutor mailboxExecutor;

    private transient StreamRecord<EventMessage<K>> reusedStreamRecord;

    private transient StreamRecord<EventMessage<K>> reusedSideOutputStreamRecord;

    private final WorkflowPlan workflowPlan;

    /**
     * If an event with the same key is currently being processed, the newly received {@link
     * InputEvent} should not be processed immediately. It will be added to the pending queue and
     * processed during a periodic timer trigger.
     */
    private transient ListState<EventMessage<K>> pendingInputEventsState;

    /** The number of actions that are still pending to be executed for the current key. */
    private transient ValueState<Integer> pendingActionCountState;

    private final TypeInformation<EventMessage<K>> eventMessageTypeInfo;

    private final long pendingEventProcessInterval;

    private final RunnerContextImpl runnerContext;

    private transient PythonActionExecutor pythonActionExecutor;

    public ActionExecutionOperator(
            OutputTag<EventMessage<K>> sideOutputTag,
            MailboxExecutor mailboxExecutor,
            ProcessingTimeService processingTimeService,
            WorkflowPlan workflowPlan,
            TypeInformation<EventMessage<K>> eventMessageTypeInfo,
            long pendingEventProcessInterval) {
        this.sideOutputTag = sideOutputTag;
        this.mailboxExecutor = Objects.requireNonNull(mailboxExecutor);
        this.processingTimeService = processingTimeService;
        this.workflowPlan = workflowPlan;
        this.eventMessageTypeInfo = eventMessageTypeInfo;
        this.pendingEventProcessInterval = pendingEventProcessInterval;
        this.runnerContext = new RunnerContextImpl();
        this.chainingStrategy = ChainingStrategy.ALWAYS;
    }

    @Override
    public void open() throws Exception {
        super.open();

        Objects.requireNonNull(mailboxExecutor, "MailboxExecutor is unexpectedly NULL");

        reusedStreamRecord = new StreamRecord<>(null);

        reusedSideOutputStreamRecord = new StreamRecord<>(null);

        ValueStateDescriptor<Integer> pendingActionCountDescriptor =
                new ValueStateDescriptor<>(
                        "pendingActionCount", TypeInformation.of(Integer.class), 0);
        pendingActionCountState = getRuntimeContext().getState(pendingActionCountDescriptor);

        ListStateDescriptor<EventMessage<K>> pendingInputEventsDescriptor =
                new ListStateDescriptor<>("pendingInputEvents", eventMessageTypeInfo);
        pendingInputEventsState = getRuntimeContext().getListState(pendingInputEventsDescriptor);

        initPythonActionExecutor();

        processingTimeService.registerTimer(
                processingTimeService.getCurrentProcessingTime() + pendingEventProcessInterval,
                (long timestamp) -> {
                    processPendingInputEventsAndRegisterTimer();
                });
    }

    @Override
    public void processElement(StreamRecord<EventMessage<K>> record) throws Exception {
        EventMessage<K> eventMessage = record.getValue();
        System.out.printf("FunctionGroupOperator receive element %s%n", eventMessage);

        if (eventMessage.isInputEvent() && !canProcessInputEvent()) {
            // If the event is an InputEvent and there is already another event with the same key
            // being processed, it will be added to pendingInputEvents and processed later.
            LOG.debug("Add element {} to pending list.", eventMessage);
            pendingInputEventsState.add(eventMessage);
            return;
        }

        processEventMessage(eventMessage);
    }

    private void processEventMessage(EventMessage<K> eventMessage) throws Exception {
        Event event = eventMessage.getEvent();
        System.out.println("Event type: " + event.getEventType());
        List<Action> actions = workflowPlan.getEventTriggerActions(event.getEventType());
        if (actions != null && !actions.isEmpty()) {
            addPendingActionCount(actions.size());
            for (Action action : actions) {
                System.out.println("Action: " + action.getName());
                List<Event> actionOutputEvents;
                if (action.getExec() instanceof JavaFunction) {
                    action.getExec().call(event, runnerContext);
                    actionOutputEvents = runnerContext.drainEvents();
                } else if (action.getExec() instanceof PythonFunction) {
                    Preconditions.checkState(event instanceof PythonEvent);
                    actionOutputEvents =
                            pythonActionExecutor.executePythonFunction(
                                    (PythonFunction) action.getExec(), (PythonEvent) event);
                } else {
                    throw new RuntimeException("Unsupported action type: " + action.getClass());
                }

                for (Event actionOutputEvent : actionOutputEvents) {
                    EventMessage<K> actionOutputEventMessage =
                            new EventMessage<>(eventMessage.getKey(), actionOutputEvent);
                    if (actionOutputEvent.isOutputEvent()) {
                        output.collect(
                                sideOutputTag,
                                reusedSideOutputStreamRecord.replace(actionOutputEventMessage));
                    } else {
                        List<Action> pendingActions =
                                workflowPlan.getEventTriggerActions(actionOutputEvent.getEventType());
                        addPendingActionCount(pendingActions == null ? 0 : pendingActions.size());
                        output.collect(reusedStreamRecord.replace(actionOutputEventMessage));
                    }
                }

                addPendingActionCount(-1);
            }
        }
    }

    private boolean canProcessInputEvent() throws Exception {
        if (pendingInputEventsState.get().iterator().hasNext()) {
            // If there is already a pending input event with the same key, the subsequent input
            // event should not be processed immediately.
            return false;
        }

        // If there is some actions in progress with the same key, the subsequent input event should
        // not be processed immediately.
        return pendingActionCountState.value() == 0;
    }

    private void processPendingInputEventsAndRegisterTimer() throws Exception {
        List<EventMessage<K>> continuePendingInputEvents = new ArrayList<>();
        // To ensure that pending input events are processed in order, if an event cannot be
        // processed at the moment, subsequent events will also be held back and not processed.
        // Therefore, we use a flag to indicate whether subsequent events can be processed.
        boolean canProcess = true;
        for (EventMessage<K> dataMessage : pendingInputEventsState.get()) {
            if (canProcess && canProcessInputEvent()) {
                processEventMessage(dataMessage);
            } else {
                canProcess = false;
                continuePendingInputEvents.add(dataMessage);
            }
        }
        pendingInputEventsState.update(continuePendingInputEvents);

        processingTimeService.registerTimer(
                processingTimeService.getCurrentProcessingTime() + pendingEventProcessInterval,
                (long timestamp) -> {
                    processPendingInputEventsAndRegisterTimer();
                });
    }

    private void addPendingActionCount(int delta) throws IOException {
        if (delta == 0) {
            return;
        }

        Integer pendingActionCount = pendingActionCountState.value();
        pendingActionCountState.update(pendingActionCount + delta);
    }

    private void initPythonActionExecutor() throws Exception {
        boolean containPythonAction =
                workflowPlan.getActions().values().stream()
                        .anyMatch(action -> action.getExec() instanceof PythonFunction);
        if (containPythonAction) {
            PythonDependencyInfo dependencyInfo =
                    PythonDependencyInfo.create(
                            getExecutionConfig().toConfiguration().set(PythonOptions.PYTHON_PATH, "/Users/jhin/Repo/oss/flink-agents/python/.venv1/bin/python"),
                            getRuntimeContext().getDistributedCache());
            PythonEnvironmentManager pythonEnvironmentManager =
                    new PythonEnvironmentManager(
                            dependencyInfo,
                            getContainingTask()
                                    .getEnvironment()
                                    .getTaskManagerInfo()
                                    .getTmpDirectories(),
                            new HashMap<>(System.getenv()),
                            getRuntimeContext().getJobInfo().getJobId());
            pythonActionExecutor = new PythonActionExecutor(pythonEnvironmentManager);
            pythonActionExecutor.open();
        }
    }
}
