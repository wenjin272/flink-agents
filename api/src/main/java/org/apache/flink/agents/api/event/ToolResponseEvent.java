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

package org.apache.flink.agents.api.event;

import org.apache.flink.agents.api.Event;
import org.apache.flink.agents.api.tools.ToolResponse;

import java.util.Map;
import java.util.UUID;

/** Event representing a result from tool call */
public class ToolResponseEvent extends Event {
    private final UUID requestId;
    private final Map<String, ToolResponse> responses;
    private final Map<String, String> externalIds;
    private final Map<String, Boolean> success;
    private final Map<String, String> error;
    private final long timestamp;

    public ToolResponseEvent(
            UUID requestId,
            Map<String, ToolResponse> responses,
            Map<String, Boolean> success,
            Map<String, String> error,
            Map<String, String> externalIds) {
        this.requestId = requestId;
        this.responses = responses;
        this.success = success;
        this.error = error;
        this.externalIds = externalIds;
        this.timestamp = System.currentTimeMillis();
    }

    public ToolResponseEvent(
            UUID requestId,
            Map<String, ToolResponse> responses,
            Map<String, Boolean> success,
            Map<String, String> error) {
        this(requestId, responses, success, error, Map.of());
    }

    public UUID getRequestId() {
        return requestId;
    }

    public Map<String, ToolResponse> getResponses() {
        return responses;
    }

    public Map<String, String> getExternalIds() {
        return externalIds;
    }

    public Map<String, Boolean> getSuccess() {
        return success;
    }

    public Map<String, String> getError() {
        return error;
    }

    public long getTimestamp() {
        return timestamp;
    }

    @Override
    public String toString() {
        return "ToolResponseEvent{"
                + "requestId="
                + requestId
                + ", response="
                + responses
                + ", success=true"
                + ", timestamp="
                + timestamp
                + '}';
    }
}
