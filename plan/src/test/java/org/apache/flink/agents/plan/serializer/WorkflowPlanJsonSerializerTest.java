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
import org.apache.flink.agents.api.OutputEvent;
import org.apache.flink.agents.plan.Action;
import org.apache.flink.agents.plan.JavaFunction;
import org.apache.flink.agents.plan.WorkflowPlan;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertTrue;

/** Test for {@link WorkflowPlanJsonSerializer}. */
public class WorkflowPlanJsonSerializerTest {
    @Test
    public void testSerializeWorkflowPlanWithActions() throws Exception {
        // Create a JavaFunction
        JavaFunction function =
                new JavaFunction(
                        "org.apache.flink.agents.plan.TestAction",
                        "legal",
                        new Class[] {InputEvent.class});

        // Create an Action
        Action action = new Action("testAction", function, List.of(InputEvent.class));

        // Create a map of actions
        Map<String, Action> actions = new HashMap<>();
        actions.put(action.getName(), action);

        // Create a WorkflowPlan with actions but no event trigger actions
        WorkflowPlan workflowPlan = new WorkflowPlan(actions, new HashMap<>());

        // Serialize the workflow plan to JSON
        String json = new ObjectMapper().writeValueAsString(workflowPlan);

        // Verify the JSON contains the expected fields
        assertTrue(json.contains("\"actions\":{"), "JSON should contain the actions field");
        assertTrue(json.contains("\"testAction\":{"), "JSON should contain the action name");
        assertTrue(json.contains("\"name\":\"testAction\""), "JSON should contain the action name");
        assertTrue(json.contains("\"exec\":{"), "JSON should contain the exec field");
        assertTrue(
                json.contains("\"func_type\":\"JavaFunction\""),
                "JSON should contain the function type");
        assertTrue(
                json.contains("\"qualname\":\"org.apache.flink.agents.plan.TestAction\""),
                "JSON should contain the function's qualified name");
        assertTrue(
                json.contains("\"method_name\":\"legal\""), "JSON should contain the method name");
        assertTrue(
                json.contains("\"listenEventTypes\":["),
                "JSON should contain the listen event types");
        assertTrue(
                json.contains("\"org.apache.flink.agents.api.InputEvent\""),
                "JSON should contain the event type class name");
        assertTrue(
                json.contains("\"event_trigger_actions\":{}"),
                "JSON should contain empty event trigger actions");
    }

    @Test
    public void testSerializeWorkflowPlanWithEventTriggerActions() throws Exception {
        // Create a JavaFunction
        JavaFunction function =
                new JavaFunction(
                        "org.apache.flink.agents.plan.TestAction",
                        "legal",
                        new Class[] {InputEvent.class});

        // Create an Action
        Action action = new Action("testAction", function, List.of(InputEvent.class));

        // Create a map of event trigger actions
        Map<Class<? extends Event>, List<Action>> eventTriggerActions = new HashMap<>();
        eventTriggerActions.put(InputEvent.class, List.of(action));

        // Create a WorkflowPlan with event trigger actions but no regular actions
        WorkflowPlan workflowPlan = new WorkflowPlan(new HashMap<>(), eventTriggerActions);

        // Serialize the workflow plan to JSON
        String json = new ObjectMapper().writeValueAsString(workflowPlan);

        // Verify the JSON contains the expected fields
        assertTrue(json.contains("\"actions\":{}"), "JSON should contain empty actions");
        assertTrue(
                json.contains("\"event_trigger_actions\":{"),
                "JSON should contain the event trigger actions field");
        assertTrue(
                json.contains("\"org.apache.flink.agents.api.InputEvent\":["),
                "JSON should contain the event class name and an array of action names");
        assertTrue(
                json.contains("\"testAction\""),
                "JSON should contain the action name in event triggers");
    }

    @Test
    public void testSerializeWorkflowPlanWithBothActionsAndEventTriggerActions() throws Exception {
        // Create JavaFunctions
        JavaFunction function1 =
                new JavaFunction(
                        "org.apache.flink.agents.plan.TestAction",
                        "legal",
                        new Class[] {InputEvent.class});
        JavaFunction function2 =
                new JavaFunction(
                        "org.apache.flink.agents.plan.TestAction",
                        "legal",
                        new Class[] {InputEvent.class});

        // Create Actions
        Action action1 = new Action("action1", function1, List.of(InputEvent.class));
        Action action2 = new Action("action2", function2, List.of(OutputEvent.class));

        // Create a map of actions
        Map<String, Action> actions = new HashMap<>();
        actions.put(action1.getName(), action1);
        actions.put(action2.getName(), action2);

        // Create a map of event trigger actions
        Map<Class<? extends Event>, List<Action>> eventTriggerActions = new HashMap<>();
        eventTriggerActions.put(InputEvent.class, List.of(action1));
        eventTriggerActions.put(OutputEvent.class, List.of(action2));

        // Create a WorkflowPlan with both actions and event trigger actions
        WorkflowPlan workflowPlan = new WorkflowPlan(actions, eventTriggerActions);

        // Serialize the workflow plan to JSON
        String json = new ObjectMapper().writeValueAsString(workflowPlan);

        // Verify the JSON contains the expected fields
        assertTrue(json.contains("\"actions\":{"), "JSON should contain the actions field");
        assertTrue(json.contains("\"action1\":{"), "JSON should contain the first action name");
        assertTrue(json.contains("\"action2\":{"), "JSON should contain the second action name");
        assertTrue(
                json.contains("\"event_trigger_actions\":{"),
                "JSON should contain the event trigger actions field");
        assertTrue(
                json.contains("\"org.apache.flink.agents.api.InputEvent\":["),
                "JSON should contain the InputEvent class name and an array of action names");
        assertTrue(
                json.contains("\"org.apache.flink.agents.api.OutputEvent\":["),
                "JSON should contain the OutputEvent class name and an array of action names");
        assertTrue(
                json.contains("\"action1\""),
                "JSON should contain the first action name in event triggers");
        assertTrue(
                json.contains("\"action2\""),
                "JSON should contain the second action name in event triggers");
    }

    @Test
    public void testSerializeEmptyWorkflowPlan() throws Exception {
        // Create an empty WorkflowPlan
        WorkflowPlan workflowPlan = new WorkflowPlan(new HashMap<>(), new HashMap<>());

        // Serialize the workflow plan to JSON
        String json = new ObjectMapper().writeValueAsString(workflowPlan);

        // Verify the JSON contains the expected fields
        assertTrue(json.contains("\"actions\":{}"), "JSON should contain empty actions");
        assertTrue(
                json.contains("\"event_trigger_actions\":{}"),
                "JSON should contain empty event trigger actions");
    }
}
