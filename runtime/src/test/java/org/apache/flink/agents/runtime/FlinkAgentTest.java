package org.apache.flink.agents.runtime;

import org.apache.flink.agents.api.Event;
import org.apache.flink.agents.api.InputEvent;
import org.apache.flink.agents.api.OutputEvent;
import org.apache.flink.agents.api.context.RunnerContext;
import org.apache.flink.agents.plan.Action;
import org.apache.flink.agents.plan.JavaFunction;
import org.apache.flink.agents.plan.WorkflowPlan;
import org.apache.flink.agents.runtime.message.EventMessage;
import org.apache.flink.api.common.RuntimeExecutionMode;
import org.apache.flink.api.common.typeinfo.TypeHint;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.junit.jupiter.api.Test;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class FlinkAgentTest {
    @Test
    public void testConnectToWorkflow() throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.setRuntimeMode(RuntimeExecutionMode.STREAMING);
        WorkflowPlan workflowPlan = MockedWorkflow.getWorkflowPlan();

        DataStream<Long> workflowInputDataStream =
                env.fromData(
                        0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L,
                        0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L,
                        0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L,
                        0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L,
                        0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L,
                        0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L,
                        0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L,
                        0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L,
                        0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L,
                        0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L,
                        0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L,
                        0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L,
                        0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L,
                        0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L,
                        0L, 0L);
        DataStream<EventMessage<Long>> runtimeInputDataStream =
                workflowInputDataStream
                        .map(
                                num ->
                                        (EventMessage<Long>)
                                                new EventMessage<Long>(
                                                        num % 3, new InputEvent(num)))
                        .returns(new TypeHint<EventMessage<Long>>() {});

        DataStream<?> outputDataStream =
                FlinkAgent.connectToWorkflow(
                        runtimeInputDataStream, TypeInformation.of(Long.class), workflowPlan);
        outputDataStream.print();
        env.execute();
    }

    public static class MockedEvent extends Event {
        public Long num;

        public MockedEvent(Long num) {
            super();
            this.num = num;
        }

        public Long getNum() {
            return num;
        }
    }

    public static class MockedWorkflow {
        public static void processInputEvent(InputEvent event, RunnerContext context) {
            Long inputData = (Long) event.getInput();
            context.sendEvent(new MockedEvent(inputData + 1));
        }

        public static void processMockedEvent(MockedEvent event, RunnerContext context) {
            context.sendEvent(new OutputEvent(event.getNum() * 2));
        }

        public static WorkflowPlan getWorkflowPlan() throws Exception {
            Map<String, List<Action>> eventTriggerActions = new HashMap<>();
            Action action1 =
                    new Action(
                            "processInputEvent",
                            new JavaFunction(
                                    MockedWorkflow.class,
                                    "processInputEvent",
                                    new Class<?>[] {InputEvent.class, RunnerContext.class}),
                            Collections.singletonList(InputEvent.class.getName()));
            Action action2 =
                    new Action(
                            "processMockedEvent",
                            new JavaFunction(
                                    MockedWorkflow.class,
                                    "processMockedEvent",
                                    new Class<?>[] {MockedEvent.class, RunnerContext.class}),
                            Collections.singletonList(MockedEvent.class.getName()));
            eventTriggerActions.put(InputEvent.class.getName(), Collections.singletonList(action1));
            eventTriggerActions.put(MockedEvent.class.getName(), Collections.singletonList(action2));
            Map<String, Action> actions = new HashMap<>();
            actions.put(action1.getName(), action1);
            actions.put(action2.getName(), action2);
            return new WorkflowPlan(actions, eventTriggerActions);
        }
    }
}
