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
package org.apache.flink.agents.api.memory;

import java.time.LocalDateTime;
import java.util.Map;

public class MemorySetItem {
    private final String memorySetName;
    private final String id;
    private final Object value;
    private final boolean compacted;
    private final Object createdTime;
    private final LocalDateTime lastAccessedTime;
    private final Map<String, Object> metadata;

    public MemorySetItem(
            String memorySetName,
            String id,
            Object value,
            boolean compacted,
            Object createdTime,
            LocalDateTime lastAccessedTime,
            Map<String, Object> metadata) {
        this.memorySetName = memorySetName;
        this.id = id;
        this.value = value;
        this.compacted = compacted;
        this.createdTime = createdTime;
        this.lastAccessedTime = lastAccessedTime;
        this.metadata = metadata;
    }

    public String getMemorySetName() {
        return memorySetName;
    }

    public String getId() {
        return id;
    }

    public Object getValue() {
        return value;
    }

    public boolean isCompacted() {
        return compacted;
    }

    public Object getCreatedTime() {
        return createdTime;
    }

    public LocalDateTime getLastAccessedTime() {
        return lastAccessedTime;
    }

    public Map<String, Object> getMetadata() {
        return metadata;
    }

    public static class DateTimeRange {
        private final LocalDateTime start;
        private final LocalDateTime end;

        public DateTimeRange(LocalDateTime start, LocalDateTime end) {
            this.start = start;
            this.end = end;
        }

        public LocalDateTime getStart() {
            return start;
        }

        public LocalDateTime getEnd() {
            return end;
        }
    }
}
