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
package org.apache.flink.agents.runtime.actionstate;

import org.apache.flink.agents.api.Event;
import org.apache.flink.agents.api.InputEvent;
import org.apache.flink.agents.api.OutputEvent;
import org.apache.flink.agents.api.agents.AgentExecutionOptions;
import org.apache.flink.agents.api.context.RunnerContext;
import org.apache.flink.agents.plan.AgentConfiguration;
import org.apache.flink.agents.plan.AgentPlan;
import org.apache.flink.agents.plan.JavaFunction;
import org.apache.flink.agents.plan.actions.Action;
import org.apache.flink.agents.runtime.operator.ActionExecutionOperator;
import org.apache.flink.agents.runtime.operator.ActionExecutionOperatorFactory;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.apache.flink.api.common.typeutils.base.LongSerializer;
import org.apache.flink.api.java.functions.KeySelector;
import org.apache.flink.runtime.checkpoint.OperatorSubtaskState;
import org.apache.flink.streaming.runtime.streamrecord.StreamRecord;
import org.apache.flink.streaming.util.KeyedOneInputStreamOperatorTestHarness;
import org.apache.fluss.client.Connection;
import org.apache.fluss.client.ConnectionFactory;
import org.apache.fluss.client.admin.Admin;
import org.apache.fluss.metadata.TablePath;
import org.apache.fluss.server.testutils.FlussClusterExtension;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.extension.RegisterExtension;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.testcontainers.DockerClientFactory;
import org.testcontainers.kafka.KafkaContainer;
import org.testcontainers.utility.DockerImageName;

import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;

import static org.apache.flink.agents.api.configuration.AgentConfigOptions.*;
import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assumptions.assumeTrue;

/** Real backend logs and recovery markers across repeated operator checkpoints/restores. */
public class ActionStateDivergenceIntegrationTest {
    private static final AtomicInteger CALLS = new AtomicInteger();
    private static KafkaContainer kafka;

    @RegisterExtension
    static final FlussClusterExtension FLUSS =
            FlussClusterExtension.builder().setNumOfTabletServers(1).build();

    @AfterAll
    static void stopKafka() {
        if (kafka != null) kafka.close();
    }

    @ParameterizedTest
    @CsvSource({"kafka,false", "kafka,true", "fluss,false", "fluss,true"})
    void completedCascadeSurvivesCheckpointBeforeReplayingRecoveredInputs(
            String backend, boolean parallel) throws Exception {
        CALLS.set(0);
        AgentConfiguration config = config(backend);
        AgentPlan plan = plan(parallel);
        OperatorSubtaskState checkpoint;
        try (var harness = harness(plan, store(backend, config))) {
            harness.open();
            checkpoint = harness.snapshot(1L, 1L);
            input(harness, "one");
            input(harness, "two");
            assertThat(CALLS.get()).isEqualTo(4);
        }
        try (var harness = harness(plan, store(backend, config))) {
            harness.initializeState(checkpoint);
            harness.open();
            // All future completions are cached, but the operator has not replayed their inputs.
            // Fluss must refresh these rounds in sequence order; Kafka must retain their offsets.
            checkpoint = harness.snapshot(2L, 2L);
            harness.notifyOfCompletedCheckpoint(2L);
        }
        try (var harness = harness(plan, store(backend, config))) {
            harness.initializeState(checkpoint);
            harness.open();
            input(harness, "one");
            input(harness, "two");
            assertThat(harness.extractOutputValues()).containsExactly("one", "two");
            assertThat(CALLS.get()).as("all four saved completions must be reused").isEqualTo(4);
        }
    }

    @ParameterizedTest
    @CsvSource({"kafka,false", "kafka,true", "fluss,false", "fluss,true"})
    void changedRootCannotReuseChildComputedAgainstAnotherMemoryHistory(
            String backend, boolean parallel) throws Exception {
        CALLS.set(0);
        AgentConfiguration config = config(backend);
        AgentPlan plan = plan(parallel);
        OperatorSubtaskState checkpoint;
        try (var harness = harness(plan, store(backend, config))) {
            harness.open();
            checkpoint = harness.snapshot(1L, 1L);
            input(harness, "A");
            assertThat(harness.extractOutputValues()).containsExactly("A");
        }
        for (String branch : List.of("B", "A")) {
            try (var harness = harness(plan, store(backend, config))) {
                harness.initializeState(checkpoint);
                harness.open();
                input(harness, branch);
                assertThat(harness.extractOutputValues()).containsExactly(branch);
            }
        }
        assertThat(CALLS.get()).isEqualTo(6);
    }

    public static void root(Event event, RunnerContext context) throws Exception {
        CALLS.incrementAndGet();
        context.getShortTermMemory().set("value", event.getAttr("input"));
        context.sendEvent(new Event("child", Map.of("payload", "same-on-every-branch")));
    }

    public static void child(Event event, RunnerContext context) throws Exception {
        CALLS.incrementAndGet();
        context.sendEvent(new OutputEvent(context.getShortTermMemory().get("value").getValue()));
    }

    private static AgentPlan plan(boolean parallel) throws Exception {
        Action root = action("root", InputEvent.EVENT_TYPE);
        Action child = action("child", "child");
        AgentPlan plan = new AgentPlan(Map.of(root.getName(), root, child.getName(), child));
        plan.getConfig().set(AgentExecutionOptions.PARALLEL_EXECUTION_ENABLED, parallel);
        return plan;
    }

    private static Action action(String name, String type) throws Exception {
        return new Action(
                name,
                new JavaFunction(
                        ActionStateDivergenceIntegrationTest.class,
                        name,
                        new Class<?>[] {Event.class, RunnerContext.class}),
                List.of(type));
    }

    private static AgentConfiguration config(String backend) {
        AgentConfiguration config = new AgentConfiguration();
        String name = "divergence_" + UUID.randomUUID().toString().replace('-', '_');
        if (backend.equals("kafka")) {
            assumeTrue(
                    DockerClientFactory.instance().isDockerAvailable(),
                    "Docker is required for Kafka integration");
            if (kafka == null) {
                kafka = new KafkaContainer(DockerImageName.parse("apache/kafka-native:3.8.0"));
                kafka.start();
            }
            config.set(KAFKA_BOOTSTRAP_SERVERS, kafka.getBootstrapServers());
            config.set(KAFKA_ACTION_STATE_TOPIC, name);
            config.set(KAFKA_ACTION_STATE_TOPIC_NUM_PARTITIONS, 2);
        } else {
            config.set(FLUSS_BOOTSTRAP_SERVERS, FLUSS.getBootstrapServers());
            config.set(FLUSS_ACTION_STATE_DATABASE, "divergence");
            config.set(FLUSS_ACTION_STATE_TABLE, name);
            config.set(FLUSS_ACTION_STATE_TABLE_BUCKETS, 2);
        }
        return config;
    }

    private static ActionStateStore store(String backend, AgentConfiguration config)
            throws Exception {
        ActionStateKeyEncoder encoder = new ActionStateKeyEncoder(128, LongSerializer.INSTANCE);
        if (backend.equals("kafka")) return new KafkaActionStateStore(config, encoder);
        FlussActionStateStore store = new FlussActionStateStore(config, encoder);
        try (Connection connection = ConnectionFactory.createConnection(FLUSS.getClientConfig());
                Admin admin = connection.getAdmin()) {
            TablePath path =
                    TablePath.of(
                            config.get(FLUSS_ACTION_STATE_DATABASE),
                            config.get(FLUSS_ACTION_STATE_TABLE));
            FLUSS.waitUntilTableReady(admin.getTableInfo(path).get().getTableId());
        }
        return store;
    }

    private static KeyedOneInputStreamOperatorTestHarness<Long, String, String> harness(
            AgentPlan plan, ActionStateStore store) throws Exception {
        return new KeyedOneInputStreamOperatorTestHarness<>(
                new ActionExecutionOperatorFactory<>(plan, true, store),
                (KeySelector<String, Long>) value -> 7L,
                TypeInformation.of(Long.class),
                128,
                1,
                0);
    }

    @SuppressWarnings("unchecked")
    private static void input(
            KeyedOneInputStreamOperatorTestHarness<Long, String, String> harness, String value)
            throws Exception {
        harness.processElement(new StreamRecord<>(value));
        ((ActionExecutionOperator<String, String>) harness.getOperator())
                .waitInFlightEventsFinished();
    }
}
