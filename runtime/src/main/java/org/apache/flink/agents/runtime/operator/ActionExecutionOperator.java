/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.apache.flink.agents.runtime.operator;

import org.apache.flink.agents.api.Event;
import org.apache.flink.agents.api.InputEvent;
import org.apache.flink.agents.api.OutputEvent;
import org.apache.flink.agents.plan.Action;
import org.apache.flink.agents.plan.JavaFunction;
import org.apache.flink.agents.plan.PythonFunction;
import org.apache.flink.agents.plan.WorkflowPlan;
import org.apache.flink.agents.runtime.context.RunnerContextImpl;
import org.apache.flink.agents.runtime.env.PythonEnvironmentManager;
import org.apache.flink.agents.runtime.memory.MemoryObjectImpl;
import org.apache.flink.agents.runtime.python.event.PythonEvent;
import org.apache.flink.agents.runtime.python.utils.PythonActionExecutor;
import org.apache.flink.agents.runtime.utils.EventUtil;
import org.apache.flink.api.common.state.*;
import org.apache.flink.api.common.state.MapStateDescriptor;
import org.apache.flink.api.common.typeinfo.TypeHint;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.apache.flink.python.env.PythonDependencyInfo;
import org.apache.flink.streaming.api.operators.AbstractStreamOperator;
import org.apache.flink.streaming.api.operators.ChainingStrategy;
import org.apache.flink.streaming.api.operators.OneInputStreamOperator;
import org.apache.flink.streaming.runtime.streamrecord.StreamRecord;
import org.apache.flink.streaming.runtime.tasks.ProcessingTimeService;
import org.apache.flink.types.Row;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;

import static org.apache.flink.util.Preconditions.checkState;

/**
 * An operator that executes the actions defined in the workflow. Upon receiving data from the
 * upstream, it first wraps the data into an {@link InputEvent}. It then invokes the corresponding
 * action that is interested in the {@link InputEvent}, and collects the output event produced by
 * the action.
 *
 * <p>For events of type {@link OutputEvent}, the data contained in the event is sent downstream.
 * For all other event types, the process is repeated: the event triggers the corresponding action,
 * and the resulting output event is collected for further processing.
 */
public class ActionExecutionOperator<IN, OUT> extends AbstractStreamOperator<OUT>
        implements OneInputStreamOperator<IN, OUT> {

    private static final long serialVersionUID = 1L;

    private static final Logger LOG = LoggerFactory.getLogger(ActionExecutionOperator.class);

    private final WorkflowPlan workflowPlan;

    private final Boolean inputIsJava;

    private transient StreamRecord<OUT> reusedStreamRecord;

    private transient MapState<String, MemoryObjectImpl.ValueWrapper> pendingMemoryStoreState;

    // RunnerContext for Java actions
    private final RunnerContextImpl runnerContext;

    // PythonActionExecutor for Python actions
    private transient PythonActionExecutor pythonActionExecutor;

    public ActionExecutionOperator(
            WorkflowPlan workflowPlan,
            Boolean inputIsJava,
            ProcessingTimeService processingTimeService) {
        this.workflowPlan = workflowPlan;
        this.inputIsJava = inputIsJava;
        this.processingTimeService = processingTimeService;
        this.runnerContext = new RunnerContextImpl();
        this.chainingStrategy = ChainingStrategy.ALWAYS;
    }

    @Override
    public void open() throws Exception {
        super.open();

        reusedStreamRecord = new StreamRecord<>(null);

        // init state
        MapStateDescriptor<String, MemoryObjectImpl.ValueWrapper> pendingMemoryStoreDescriptor =
                new MapStateDescriptor<>(
                        "pendingMemoryStore",
                        TypeInformation.of(new TypeHint<String>() {}),
                        TypeInformation.of(new TypeHint<MemoryObjectImpl.ValueWrapper>() {}));
        pendingMemoryStoreState = getRuntimeContext().getMapState(pendingMemoryStoreDescriptor);
        runnerContext.setStore(pendingMemoryStoreState);

        // init PythonActionExecutor
        initPythonActionExecutor();
    }

    @Override
    public void processElement(StreamRecord<IN> record) throws Exception {
        IN input = record.getValue();
        LOG.debug("Receive an element {}", input);

        // 1. wrap to InputEvent first
        Event inputEvent = wrapToInputEvent(input);

        // 2. execute action
        LinkedList<Event> events = new LinkedList<>();
        events.push(inputEvent);
        while (!events.isEmpty()) {
            Event event = events.pop();
            List<Action> actions = getEventTriggerActions(event);
            if (actions != null && !actions.isEmpty()) {
                for (Action action : actions) {
                    // TODO: Support multi-action execution for a single event. Example: A Java
                    // event
                    // should be processable by both Java and Python actions.
                    // TODO: Implement asynchronous action execution.

                    // execute action and collect output events
                    LOG.debug("Try execute action {} for event {}.", action.getName(), event);
                    List<Event> actionOutputEvents;
                    if (action.getExec() instanceof JavaFunction) {
                        action.getExec().call(event, runnerContext);
                        actionOutputEvents = runnerContext.drainEvents();
                    } else if (action.getExec() instanceof PythonFunction) {
                        checkState(event instanceof PythonEvent);
                        actionOutputEvents =
                                pythonActionExecutor.executePythonFunction(
                                        (PythonFunction) action.getExec(), (PythonEvent) event);
                    } else {
                        throw new RuntimeException("Unsupported action type: " + action.getClass());
                    }

                    for (Event actionOutputEvent : actionOutputEvents) {
                        if (EventUtil.isOutputEvent(actionOutputEvent)) {
                            OUT outputData = getOutputFromOutputEvent(actionOutputEvent);
                            LOG.debug(
                                    "Collect output data {} for input {} in action {}.",
                                    outputData,
                                    input,
                                    action.getName());
                            output.collect(reusedStreamRecord.replace(outputData));
                        } else {
                            LOG.debug(
                                    "Collect event {} for event {} in action {}.",
                                    actionOutputEvent,
                                    event,
                                    action.getName());
                            events.add(actionOutputEvent);
                        }
                    }
                }
            }
        }
    }

    private void initPythonActionExecutor() throws Exception {
        boolean containPythonAction =
                workflowPlan.getActions().values().stream()
                        .anyMatch(action -> action.getExec() instanceof PythonFunction);
        if (containPythonAction) {
            LOG.debug("Begin initialize PythonActionExecutor.");
            PythonDependencyInfo dependencyInfo =
                    PythonDependencyInfo.create(
                            getExecutionConfig().toConfiguration(),
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
            pythonActionExecutor.open(pendingMemoryStoreState);
        }
    }

    private Event wrapToInputEvent(IN input) {
        if (inputIsJava) {
            return new InputEvent(input);
        } else {
            // the input data must originate from Python and be of type Row with two fields — the
            // first representing the key, and the second representing the actual data payload.
            checkState(input instanceof Row && ((Row) input).getArity() == 2);
            return pythonActionExecutor.wrapToInputEvent(((Row) input).getField(1));
        }
    }

    private OUT getOutputFromOutputEvent(Event event) {
        checkState(EventUtil.isOutputEvent(event));
        if (event instanceof OutputEvent) {
            return (OUT) ((OutputEvent) event).getOutput();
        } else {
            Object outputFromOutputEvent =
                    pythonActionExecutor.getOutputFromOutputEvent(((PythonEvent) event).getEvent());
            return (OUT) outputFromOutputEvent;
        }
    }

    private List<Action> getEventTriggerActions(Event event) {
        if (event instanceof PythonEvent) {
            return workflowPlan.getEventTriggerActions(((PythonEvent) event).getEventType());
        } else {
            return workflowPlan.getEventTriggerActions(event.getClass().getName());
        }
    }
}
