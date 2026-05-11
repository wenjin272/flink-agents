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

package org.apache.flink.agents.runtime.skill;

import org.apache.flink.agents.runtime.skill.repository.ClasspathSkillRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ClasspathSkillRepositoryTest {

    private static Path resourcesRoot() {
        return Path.of("src/test/resources/skills").toAbsolutePath();
    }

    private static void zipDirIntoJarUnderPrefix(Path src, Path jar, String prefix)
            throws IOException {
        try (JarOutputStream jos = new JarOutputStream(Files.newOutputStream(jar));
                Stream<Path> walk = Files.walk(src)) {
            walk.filter(Files::isRegularFile)
                    .forEach(
                            file -> {
                                try {
                                    String name = prefix + "/" + src.relativize(file).toString();
                                    jos.putNextEntry(new JarEntry(name));
                                    Files.copy(file, jos);
                                    jos.closeEntry();
                                } catch (IOException e) {
                                    throw new RuntimeException(e);
                                }
                            });
        }
    }

    @Test
    void loadFromDirectoryResource() throws IOException {
        // src/test/resources/skills is on the test classpath as a directory.
        ClasspathSkillRepository repo = new ClasspathSkillRepository("skills");
        assertEquals(
                List.of("github", "nano-banana-pro"),
                repo.getSkills().stream()
                        .map(AgentSkill::getName)
                        .sorted()
                        .collect(Collectors.toList()));
    }

    @Test
    void loadFromJarResource(@TempDir Path tempDir) throws IOException {
        Path jar = tempDir.resolve("skills-as-jar.jar");
        zipDirIntoJarUnderPrefix(resourcesRoot(), jar, "embedded-skills");
        URLClassLoader loader =
                new URLClassLoader(new URL[] {jar.toUri().toURL()}, /* parent */ null);
        ClasspathSkillRepository repo = new ClasspathSkillRepository("embedded-skills", loader);
        assertEquals(
                List.of("github", "nano-banana-pro"),
                repo.getSkills().stream()
                        .map(AgentSkill::getName)
                        .sorted()
                        .collect(Collectors.toList()));
    }

    @Test
    void missingResource() {
        IllegalArgumentException ex =
                assertThrows(
                        IllegalArgumentException.class,
                        () -> new ClasspathSkillRepository("no-such-thing"));
        assertTrue(
                ex.getMessage().contains("Classpath resource not found"),
                "expected 'Classpath resource not found' in message, got: " + ex.getMessage());
    }
}
