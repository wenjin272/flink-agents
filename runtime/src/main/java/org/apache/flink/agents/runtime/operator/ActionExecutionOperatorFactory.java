package org.apache.flink.agents.runtime.operator;

import org.apache.flink.agents.plan.WorkflowPlan;
import org.apache.flink.agents.runtime.message.EventMessage;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.apache.flink.streaming.api.operators.ChainingStrategy;
import org.apache.flink.streaming.api.operators.OneInputStreamOperatorFactory;
import org.apache.flink.streaming.api.operators.StreamOperator;
import org.apache.flink.streaming.api.operators.StreamOperatorParameters;
import org.apache.flink.util.OutputTag;

/**
 * Operator factory for {@link ActionExecutionOperator}.
 *
 * <p>NOTE: This code is adapted from the <a
 * href="https://github.com/apache/flink-statefun">flink-statefun</a>.
 */
public class ActionExecutionOperatorFactory<K>
        implements OneInputStreamOperatorFactory<EventMessage<K>, EventMessage<K>> {

    private final OutputTag<EventMessage<K>> outputTag;

    private final WorkflowPlan workflowPlan;

    private final TypeInformation<EventMessage<K>> eventMessageTypeInfo;

    private static final long DEFAULT_PROCESS_PENDING_INPUT_EVENTS_INTERVAL_MS = 3000;

    public ActionExecutionOperatorFactory(
            OutputTag<EventMessage<K>> outputTag,
            WorkflowPlan workflowPlan,
            TypeInformation<EventMessage<K>> eventMessageTypeInfo) {
        this.outputTag = outputTag;
        this.workflowPlan = workflowPlan;
        this.eventMessageTypeInfo = eventMessageTypeInfo;
    }

    public <T extends StreamOperator<EventMessage<K>>> T createStreamOperator(
            StreamOperatorParameters<EventMessage<K>> streamOperatorParameters) {
        ActionExecutionOperator<K> op =
                new ActionExecutionOperator<>(
                        outputTag,
                        streamOperatorParameters.getMailboxExecutor(),
                        streamOperatorParameters.getProcessingTimeService(),
                        workflowPlan,
                        eventMessageTypeInfo,
                        DEFAULT_PROCESS_PENDING_INPUT_EVENTS_INTERVAL_MS);
        op.setup(
                streamOperatorParameters.getContainingTask(),
                streamOperatorParameters.getStreamConfig(),
                streamOperatorParameters.getOutput());

        return (T) op;
    }

    @Override
    public void setChainingStrategy(ChainingStrategy chainingStrategy) {}

    @Override
    public ChainingStrategy getChainingStrategy() {
        return ChainingStrategy.ALWAYS;
    }

    @Override
    public Class<? extends StreamOperator> getStreamOperatorClass(ClassLoader classLoader) {
        return FeedbackOperator.class;
    }
}
