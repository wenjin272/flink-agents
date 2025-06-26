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

import org.apache.flink.agents.api.Event;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.annotation.JsonCreator;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;
import java.util.Map;

/** Workflow plan compiled from user defined workflow. */
public class WorkflowPlan {
    static final String FIELD_NAME_ACTIONS = "actions";
    @JsonProperty(FIELD_NAME_ACTIONS)
    private final Map<String, List<Action>> actions;

    @JsonCreator
    public WorkflowPlan(@JsonProperty(FIELD_NAME_ACTIONS) Map<String, List<Action>> actions) {
        this.actions = actions;
    }

    public List<Action> getAction(String type) {
        return actions.get(type);
    }

    public Map<String, List<Action>> getActions() {
        return actions;
    }
}
