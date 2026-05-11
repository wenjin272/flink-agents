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

package org.apache.flink.agents.api.skills;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import org.apache.flink.agents.api.resource.ResourceType;
import org.apache.flink.agents.api.resource.SerializableResource;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/**
 * Configuration resource describing where to load agent skills from.
 *
 * <p>Use one of the factory methods to construct:
 *
 * <ul>
 *   <li>{@link #fromLocalDir(String...)} for local directories or {@code .zip} files
 *   <li>{@link #fromUrl(String...)} for http(s) URLs pointing to a {@code .zip}
 *   <li>{@link #fromClasspath(String...)} for resources on the classpath (a directory under {@code
 *       src/main/resources} or a path inside a JAR on the classpath)
 * </ul>
 *
 * <p>Multiple {@code @Skills} declarations on the same agent are merged at plan-build time.
 */
@JsonIgnoreProperties(
        ignoreUnknown = true,
        value = {"metricGroup", "resourceType"})
public class Skills extends SerializableResource {

    /** Reserved resource name under which AgentPlan registers the merged Skills config. */
    public static final String SKILLS_CONFIG = "_skills_config";

    /** Reserved name of the built-in skill loader tool. */
    public static final String LOAD_SKILL_TOOL = "load_skill";

    /** Reserved name of the built-in bash tool used to execute skill scripts. */
    public static final String BASH_TOOL = "bash";

    private final List<String> paths;
    private final List<String> urls;
    private final List<String> classpathResources;

    /** Required by Jackson. */
    public Skills() {
        this.paths = Collections.emptyList();
        this.urls = Collections.emptyList();
        this.classpathResources = Collections.emptyList();
    }

    @JsonCreator
    public Skills(
            @JsonProperty("paths") List<String> paths,
            @JsonProperty("urls") List<String> urls,
            @JsonProperty("classpathResources") List<String> classpathResources) {
        this.paths = paths == null ? Collections.emptyList() : List.copyOf(paths);
        this.urls = urls == null ? Collections.emptyList() : List.copyOf(urls);
        this.classpathResources =
                classpathResources == null
                        ? Collections.emptyList()
                        : List.copyOf(classpathResources);
    }

    /**
     * Create a {@link Skills} resource from one or more local paths.
     *
     * <p>Each path may be a directory whose immediate subdirectories each contain a {@code
     * SKILL.md} file, or a {@code .zip} file whose top-level entries are the skill subdirectories.
     */
    public static Skills fromLocalDir(String... paths) {
        return new Skills(Arrays.asList(paths), Collections.emptyList(), Collections.emptyList());
    }

    /**
     * Create a {@link Skills} resource from one or more http(s) URLs.
     *
     * <p>Each URL must point to a {@code .zip} whose top level is the baseDir.
     */
    public static Skills fromUrl(String... urls) {
        return new Skills(Collections.emptyList(), Arrays.asList(urls), Collections.emptyList());
    }

    /**
     * Create a {@link Skills} resource from one or more classpath resource paths.
     *
     * <p>Each resource may be a directory (e.g. under {@code src/main/resources/skills}) or a
     * {@code .zip} file. When packaged into a JAR, the resource is loaded via the thread context
     * class loader and materialized to a temp directory at runtime.
     */
    public static Skills fromClasspath(String... resources) {
        return new Skills(
                Collections.emptyList(), Collections.emptyList(), Arrays.asList(resources));
    }

    @JsonProperty("paths")
    public List<String> getPaths() {
        return paths;
    }

    @JsonProperty("urls")
    public List<String> getUrls() {
        return urls;
    }

    @JsonProperty("classpathResources")
    public List<String> getClasspathResources() {
        return classpathResources;
    }

    @JsonIgnore
    @Override
    public ResourceType getResourceType() {
        return ResourceType.SKILLS;
    }
}
