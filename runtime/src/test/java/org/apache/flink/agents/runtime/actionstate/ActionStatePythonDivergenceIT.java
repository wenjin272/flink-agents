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

import org.apache.flink.agents.api.InputEvent;
import org.apache.flink.agents.plan.AgentPlan;
import org.apache.flink.agents.plan.PythonFunction;
import org.apache.flink.agents.plan.actions.Action;
import org.apache.flink.runtime.checkpoint.OperatorSubtaskState;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

import static org.apache.flink.agents.runtime.actionstate.ActionStateDivergenceRecoveryTest.*;
import static org.assertj.core.api.Assertions.assertThat;

/**
 * Native Python/Pemja recovery check. Run explicitly with -Dtest=ActionStatePythonDivergenceIT, a
 * supported Python executable on PATH, and PYTHONPATH containing its site-packages, the checkout's
 * python directory, and runtime/src/test/resources. Backend transport is simulated; the operator,
 * Python bridge, serialization, cache reconstruction and lookups are real.
 */
class ActionStatePythonDivergenceIT {
    @TempDir Path directory;

    @ParameterizedTest
    @ValueSource(strings = {"kafka", "fluss", "kafka-parallel", "fluss-parallel"})
    void completedPythonCascadeIsReusedForEveryInput(String backend) throws Exception {
        Action root =
                new Action(
                        "root",
                        new PythonFunction("action_state_recovery", "root"),
                        List.of(InputEvent.EVENT_TYPE));
        Action child =
                new Action(
                        "child",
                        new PythonFunction("action_state_recovery", "child"),
                        List.of("step"));
        AgentPlan plan = plan(backend, Map.of("root", root, "child", child));
        Journal journal = new Journal(backend);
        Path first = directory.resolve("first.calls");
        Path second = directory.resolve("second.calls");
        OperatorSubtaskState checkpoint;
        try (var harness = harness(plan, journal)) {
            harness.open();
            checkpoint = harness.snapshot(1L, 1L);
            input(harness, first.toString());
            input(harness, second.toString());
            assertThat(harness.extractOutputValues()).containsExactly("ok", "ok");
        }
        try (var harness = restored(plan, journal, checkpoint)) {
            input(harness, first.toString());
            input(harness, second.toString());
            assertThat(harness.extractOutputValues()).containsExactly("ok", "ok");
        }
        assertThat(Files.readAllLines(first)).containsExactly("root", "child");
        assertThat(Files.readAllLines(second)).containsExactly("root", "child");
    }
}
