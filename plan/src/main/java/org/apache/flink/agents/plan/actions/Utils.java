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
package org.apache.flink.agents.plan.actions;

import org.apache.flink.runtime.util.EnvironmentInformation;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.StringTokenizer;

public class Utils {
    private static final Logger LOG = LoggerFactory.getLogger(Utils.class);

    /**
     * Check whether the current Flink version supports the async execution for cross-language
     * resource.
     *
     * <p>The async execution for java resource is supported only on flink with the pemja 0.6.2
     * dependency. See <a href="https://github.com/apache/flink-agents/pull/571">flink-agents</a>
     * for details.
     */
    public static boolean supportAsync() {
        String version = EnvironmentInformation.getVersion();
        StringTokenizer st = new StringTokenizer(version, ".");
        int major = Integer.parseInt(st.nextToken());
        int minor = Integer.parseInt(st.nextToken());
        int micro = Integer.parseInt(st.nextToken());

        if ((major == 1 && (minor < 20 || micro <= 3))
                || (major == 2 && minor == 0 && micro <= 1)
                || (major == 2 && minor == 1 && micro <= 1)
                || (major == 2 && minor == 2 && micro <= 0)) {
            LOG.debug(
                    "Flink {} doesn't support async execution for java resource, will fallback to sync execution.",
                    version);
            return false;
        }

        return true;
    }
}
