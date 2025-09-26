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
package org.apache.flink.agents.integration.test;

import org.apache.flink.agents.api.AgentsExecutionEnvironment;
import org.apache.flink.api.java.functions.KeySelector;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.datastream.DataStreamSource;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;

import java.util.HashMap;
import java.util.Map;

/**
 * Example to test MemoryObject in a complete Java Flink execution environment. This job triggers
 * the {@link MemoryObjectAgent} to test storing and retrieving complex data structures.
 */
public class AgentWithResourceExample {

    public static void main(String[] args) throws Exception {
        // Create the execution environment
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.setParallelism(1);

        Map<String, Integer> element = new HashMap<>();
        element.put("a", 1);
        element.put("b", 2);
        DataStreamSource<Map<String, Integer>> inputStream = env.fromElements(element);

        // Create agents execution environment
        AgentsExecutionEnvironment agentsEnv =
                AgentsExecutionEnvironment.getExecutionEnvironment(env);

        // Apply agent to the DataStream and use the integer itself as the key
        DataStream<Object> outputStream =
                agentsEnv
                        .fromDataStream(
                                inputStream,
                                (KeySelector<Map<String, Integer>, Integer>)
                                        value -> value.get("a"))
                        .apply(new AgentWithResource())
                        .toDataStream();

        // Print the results
        outputStream.print();

        // Execute the pipeline
        agentsEnv.execute();
    }
}
