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
package org.apache.flink.agents.plan;

import org.apache.flink.agents.api.InputEvent;
import org.apache.flink.agents.api.OutputEvent;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Test Action. */
public class TestAction {
    public static void legal(InputEvent event) {}

    public static void illegal(int a, int b) {}

//    @Test
//    public void testActionSignatureLegal() throws Exception {
//        Function func =
//                new JavaFunction(
//                        "org.apache.flink.agents.plan.TestAction",
//                        "legal",
//                        new Class[] {InputEvent.class});
//
//        new Action("legal", func, List.of(InputEvent.class));
//    }
//
//    @Test
//    public void testActionSignatureIllegal() throws Exception {
//        Function func =
//                new JavaFunction(
//                        "org.apache.flink.agents.plan.TestAction",
//                        "illegal",
//                        new Class[] {int.class, int.class});
//
//        Assertions.assertThrows(
//                IllegalArgumentException.class,
//                () -> new Action("illegal", func, List.of(InputEvent.class)));
//    }

    @Test
    public void testActionSerializable() throws Exception {
        JavaFunction func =
                new JavaFunction(
                        "org.apache.flink.agents.plan.TestAction",
                        "legal",
                        new Class[] {InputEvent.class});

        Action action = new Action("legal", func, List.of(InputEvent.class));
        ObjectMapper mapper = new ObjectMapper();
        String value = mapper.writeValueAsString(action);
        Action serializedAction = mapper.readValue(value, Action.class);
        Assertions.assertEquals(action, serializedAction);

        Map<String, List<Action>> actions = new HashMap<>();
        actions.put("org.apache.flink.agents.api.InputEvent", Collections.singletonList(action));
        WorkflowPlan plan = new WorkflowPlan(actions);
        String planJson = mapper.writeValueAsString(plan);
        System.out.println(planJson);
        WorkflowPlan plan1 = mapper.readValue(planJson, WorkflowPlan.class);
    }
}
