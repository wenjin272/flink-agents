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

package org.apache.flink.agents.plan.serializer;

import org.apache.flink.agents.api.Event;
import org.apache.flink.agents.api.InputEvent;
import org.apache.flink.agents.api.context.RunnerContext;
import org.apache.flink.agents.plan.Action;
import org.apache.flink.agents.plan.AgentPlan;
import org.apache.flink.agents.plan.JavaFunction;
import org.apache.flink.agents.plan.PythonFunction;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class AgentPlanJsonDeserializerTest {
    @Test
    public void testDeserialize() throws Exception {
        // Read JSON for an Action with JavaFunction from resource file
        String json = readJsonFromResource("agent_plans/agent_plan.json");
        AgentPlan agentPlan = new ObjectMapper().readValue(json, AgentPlan.class);
        assertEquals(2, agentPlan.getActions().size());

        // Check the first action
        assertTrue(agentPlan.getActions().containsKey("first_action"));
        Action firstAction = agentPlan.getActions().get("first_action");
        assertInstanceOf(JavaFunction.class, firstAction.getExec());
        assertEquals(List.of(InputEvent.class.getName()), firstAction.getListenEventTypes());

        // Check the second action
        assertTrue(agentPlan.getActions().containsKey("second_action"));
        Action secondAction = agentPlan.getActions().get("second_action");
        assertInstanceOf(JavaFunction.class, secondAction.getExec());
        assertEquals(
                List.of(InputEvent.class.getName(), MyEvent.class.getName()),
                secondAction.getListenEventTypes());

        // Check event trigger actions
        assertEquals(2, agentPlan.getActionsByEvent().size());
        assertTrue(agentPlan.getActionsByEvent().containsKey(InputEvent.class.getName()));
        assertEquals(
                List.of(firstAction, secondAction),
                agentPlan.getActionsByEvent().get(InputEvent.class.getName()));
        assertEquals(
                List.of(secondAction), agentPlan.getActionsByEvent().get(MyEvent.class.getName()));
    }

    @Test
    public void testDeserializePythonAgentPlanJson() throws Exception {
        // Read JSON for an Action with JavaFunction from resource file
        String testRootPath = System.getProperty("user.dir"); // the path is flink-agents/plan
        String json =
                Files.readString(
                        Paths.get(
                                testRootPath,
                                "/../python/flink_agents/plan/tests/resources/agent_plan.json"));
        AgentPlan agentPlan = new ObjectMapper().readValue(json, AgentPlan.class);
        assertEquals(2, agentPlan.getActions().size());

        // Check the first action
        assertTrue(agentPlan.getActions().containsKey("first_action"));
        Action firstAction = agentPlan.getActions().get("first_action");
        assertInstanceOf(PythonFunction.class, firstAction.getExec());
        assertEquals(
                List.of("flink_agents.api.event.InputEvent"), firstAction.getListenEventTypes());

        // Check the second action
        assertTrue(agentPlan.getActions().containsKey("second_action"));
        Action secondAction = agentPlan.getActions().get("second_action");
        assertInstanceOf(PythonFunction.class, secondAction.getExec());
        assertEquals(
                List.of(
                        "flink_agents.api.event.InputEvent",
                        "flink_agents.plan.tests.test_agent_plan.MyEvent"),
                secondAction.getListenEventTypes());

        // Check event trigger actions
        assertEquals(2, agentPlan.getActionsByEvent().size());
        assertTrue(agentPlan.getActionsByEvent().containsKey("flink_agents.api.event.InputEvent"));
        assertTrue(
                agentPlan
                        .getActionsByEvent()
                        .containsKey("flink_agents.plan.tests.test_agent_plan.MyEvent"));
        assertEquals(
                List.of(firstAction, secondAction),
                agentPlan.getActionsByEvent().get("flink_agents.api.event.InputEvent"));
        assertEquals(
                List.of(secondAction),
                agentPlan
                        .getActionsByEvent()
                        .get("flink_agents.plan.tests.test_agent_plan.MyEvent"));
    }

    /**
     * Reads a JSON file from the resources directory.
     *
     * @param resourcePath the path to the resource file
     * @return the content of the file as a string
     * @throws IOException if an I/O error occurs
     */
    private String readJsonFromResource(String resourcePath) throws IOException {
        try (InputStream inputStream =
                getClass().getClassLoader().getResourceAsStream(resourcePath)) {
            if (inputStream == null) {
                throw new IOException("Resource not found: " + resourcePath);
            }
            byte[] bytes = inputStream.readAllBytes();
            return new String(bytes, StandardCharsets.UTF_8);
        }
    }

    private static class MyEvent extends Event {}

    private static class MyAction extends Action {

        public static void doNothing(Event event, RunnerContext context) {
            // No operation
        }

        public MyAction() throws Exception {
            super(
                    "MyAction",
                    new JavaFunction(
                            MyAction.class.getName(),
                            "doNothing",
                            new Class[] {Event.class, RunnerContext.class}),
                    List.of(InputEvent.class.getName(), MyEvent.class.getName()));
        }
    }
}
