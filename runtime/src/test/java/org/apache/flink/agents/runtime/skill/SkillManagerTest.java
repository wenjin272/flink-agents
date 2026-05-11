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

import com.sun.net.httpserver.HttpServer;
import org.apache.flink.agents.api.skills.Skills;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class SkillManagerTest {

    private static Skills configFromResources() {
        return Skills.fromLocalDir(
                Path.of("src/test/resources/skills").toAbsolutePath().toString());
    }

    @Test
    void sizeAndAllSkillNames() {
        SkillManager manager = new SkillManager(configFromResources());
        assertEquals(2, manager.size());
        assertEquals(List.of("github", "nano-banana-pro"), manager.getAllSkillNames());
    }

    @Test
    void getSkillThrowsWithAvailableNames() {
        SkillManager manager = new SkillManager(configFromResources());
        IllegalArgumentException ex =
                assertThrows(IllegalArgumentException.class, () -> manager.getSkill("missing"));
        assertTrue(ex.getMessage().contains("github"));
        assertTrue(ex.getMessage().contains("nano-banana-pro"));
    }

    @Test
    void generateDiscoveryPromptMatchesGoldenFile() throws IOException {
        SkillManager manager = new SkillManager(configFromResources());
        String prompt = manager.generateDiscoveryPrompt(List.of("github", "nano-banana-pro"));
        String expected =
                Files.readString(
                        Path.of("src/test/resources/skill_discovery_prompt.txt"),
                        StandardCharsets.UTF_8);
        assertEquals(expected, prompt);
    }

    @Test
    void getSkillDirsEmptyArgumentReturnsAllFsBacked() {
        SkillManager manager = new SkillManager(configFromResources());
        List<String> dirs = manager.getSkillDirs(List.of());
        assertEquals(2, dirs.size());
        assertTrue(dirs.get(0).endsWith("github") || dirs.get(0).endsWith("nano-banana-pro"));
    }

    @Test
    void getSkillDirsReturnsNamedSkillsInOrder() {
        SkillManager manager = new SkillManager(configFromResources());
        List<String> dirs = manager.getSkillDirs(List.of("github"));
        assertEquals(1, dirs.size());
        assertTrue(dirs.get(0).endsWith("github"));
    }

    @Test
    void resolveResourcePathLocatesBundledFile() {
        SkillManager manager = new SkillManager(configFromResources());
        Path resolved = manager.resolveResourcePath("nano-banana-pro", "scripts/generate_image.py");
        assertNotNull(resolved);
        assertTrue(Files.isRegularFile(resolved));
    }

    private static void zipDir(Path src, Path dstZip) throws IOException {
        try (ZipOutputStream zos = new ZipOutputStream(Files.newOutputStream(dstZip));
                Stream<Path> walk = Files.walk(src)) {
            walk.filter(Files::isRegularFile)
                    .forEach(
                            file -> {
                                try {
                                    String name = src.relativize(file).toString();
                                    zos.putNextEntry(new ZipEntry(name));
                                    Files.copy(file, zos);
                                    zos.closeEntry();
                                } catch (IOException e) {
                                    throw new RuntimeException(e);
                                }
                            });
        }
    }

    private static HttpServer startZipServer(byte[] zipBytes) throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext(
                "/",
                exchange -> {
                    exchange.getResponseHeaders().add("Content-Type", "application/zip");
                    exchange.sendResponseHeaders(200, zipBytes.length);
                    exchange.getResponseBody().write(zipBytes);
                    exchange.close();
                });
        server.setExecutor(null);
        server.start();
        return server;
    }

    @Test
    void urlOnlyLoadsSkills(@TempDir Path tempDir) throws IOException {
        Path src = Path.of("src/test/resources/skills").toAbsolutePath();
        Path zip = tempDir.resolve("skills.zip");
        zipDir(src, zip);
        HttpServer server = startZipServer(Files.readAllBytes(zip));
        try {
            int port = server.getAddress().getPort();
            Skills config = Skills.fromUrl("http://127.0.0.1:" + port + "/skills.zip");
            SkillManager manager = new SkillManager(config);
            assertEquals(
                    List.of("github", "nano-banana-pro"),
                    manager.getAllSkillNames().stream().sorted().collect(Collectors.toList()));
        } finally {
            server.stop(0);
        }
    }

    @Test
    void classpathOnlyLoadsSkills() {
        // src/test/resources/skills is on the test classpath.
        Skills config = Skills.fromClasspath("skills");
        SkillManager manager = new SkillManager(config);
        assertEquals(
                List.of("github", "nano-banana-pro"),
                manager.getAllSkillNames().stream().sorted().collect(Collectors.toList()));
    }

    @Test
    void mixedSourcesAllBranchesExecute(@TempDir Path tempDir) throws IOException {
        Path src = Path.of("src/test/resources/skills").toAbsolutePath();
        Path zip = tempDir.resolve("skills.zip");
        zipDir(src, zip);
        HttpServer server = startZipServer(Files.readAllBytes(zip));
        try {
            int port = server.getAddress().getPort();
            Skills config =
                    new Skills(
                            List.of(src.toString()),
                            List.of("http://127.0.0.1:" + port + "/skills.zip"),
                            List.of("skills"));
            SkillManager manager = new SkillManager(config);
            assertEquals(
                    List.of("github", "nano-banana-pro"),
                    manager.getAllSkillNames().stream().sorted().collect(Collectors.toList()));
            // Dispatch order is paths -> urls -> classpathResources, so the last-wins
            // dispatch makes every final repo a ClasspathSkillRepository if all three
            // branches actually ran. In the test classpath, "skills" resolves to
            // target/test-classes/skills (a directory on disk); the paths branch would
            // point at src/test/resources/skills instead. Asserting the resolved dir is
            // under "target/test-classes" proves the classpath branch ran last.
            for (String name : manager.getAllSkillNames()) {
                Path dir = manager.getSkillDir(name);
                assertNotNull(dir);
                assertTrue(
                        dir.toString().contains("target/test-classes"),
                        "expected " + dir + " to be under target/test-classes");
            }
        } finally {
            server.stop(0);
        }
    }
}
