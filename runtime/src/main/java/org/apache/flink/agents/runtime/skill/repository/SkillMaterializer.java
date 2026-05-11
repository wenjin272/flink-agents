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

package org.apache.flink.agents.runtime.skill.repository;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URISyntaxException;
import java.net.URL;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.Comparator;
import java.util.Enumeration;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.stream.Stream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

/**
 * Internal helpers for materializing skill sources (zip files, URL downloads, classpath JAR
 * entries) into a local temp directory. Cleanup is registered as a JVM shutdown hook so the temp
 * directories are removed when the process exits.
 */
public final class SkillMaterializer {

    private static final String TEMP_DIR_PREFIX = "flink-agents-skills-";

    private SkillMaterializer() {}

    /**
     * Register a JVM shutdown hook that removes {@code path} recursively. Failures during deletion
     * are silently ignored (best-effort cleanup).
     */
    public static void registerCleanup(Path path) {
        Thread hook =
                new Thread(() -> deleteRecursively(path), "skill-cleanup-" + path.getFileName());
        Runtime.getRuntime().addShutdownHook(hook);
    }

    /**
     * Extract a zip into a fresh temp directory and return that directory. Validates every entry
     * against zip-slip (paths must resolve inside the extraction directory). Registers a JVM
     * shutdown hook to remove the extraction directory at process exit.
     *
     * @throws IOException if any zip entry resolves outside the extraction directory.
     */
    public static Path extractZipSafely(Path zipPath) throws IOException {
        Path extractDir = Files.createTempDirectory(TEMP_DIR_PREFIX);
        // Register cleanup before validation so the empty tempdir is always reclaimed,
        // even if validation raises.
        registerCleanup(extractDir);
        try (ZipFile zf = new ZipFile(zipPath.toFile())) {
            // First pass: zip-slip validation.
            Enumeration<? extends ZipEntry> entries = zf.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                Path resolved = extractDir.resolve(entry.getName()).normalize();
                if (!resolved.startsWith(extractDir)) {
                    throw new IOException("Unsafe zip entry: " + entry.getName());
                }
            }
            // Second pass: extract.
            entries = zf.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                Path target = extractDir.resolve(entry.getName()).normalize();
                if (entry.isDirectory()) {
                    Files.createDirectories(target);
                } else {
                    Files.createDirectories(target.getParent());
                    try (InputStream in = zf.getInputStream(entry)) {
                        Files.copy(in, target);
                    }
                }
            }
        }
        return extractDir;
    }

    /**
     * Extract every JAR entry whose name starts with {@code resourcePrefix + "/"} into a fresh temp
     * directory. The prefix itself is stripped (so entries under {@code skills/skill-a/...} extract
     * as {@code skill-a/...}).
     *
     * <p>Registers a JVM shutdown hook for cleanup. Rejects entries that would resolve outside the
     * extraction directory (zip-slip).
     */
    public static Path extractClasspathFromJar(URL jarUrl, String resourcePrefix)
            throws IOException {
        // Parse the JAR file URL from the jar: URL. The format is jar:<jar-file-url>!/[entry].
        // We extract just the inner jar-file URL so we can open the whole JarFile and enumerate
        // all entries — JarURLConnection.getJarFile() would fail when the entry specifier names a
        // prefix that has no corresponding stored directory entry.
        String spec = jarUrl.toString();
        int sep = spec.indexOf("!/");
        String innerSpec = sep >= 0 ? spec.substring(4, sep) : spec.substring(4);
        URL innerUrl = new URL(innerSpec);
        Path extractDir = Files.createTempDirectory(TEMP_DIR_PREFIX);
        registerCleanup(extractDir);
        File jarFileObj;
        try {
            jarFileObj = new File(innerUrl.toURI());
        } catch (URISyntaxException | IllegalArgumentException e) {
            // IllegalArgumentException is thrown by File(URI) when the URI scheme is not "file"
            // (e.g. a JAR nested behind http://). Surface both as IOException so callers that
            // catch IOException for graceful failure handling see them.
            throw new IOException("Invalid JAR URL: " + jarUrl, e);
        }
        try (JarFile jarFile = new JarFile(jarFileObj)) {
            String prefix = resourcePrefix.endsWith("/") ? resourcePrefix : resourcePrefix + "/";
            Enumeration<JarEntry> entries = jarFile.entries();
            while (entries.hasMoreElements()) {
                JarEntry entry = entries.nextElement();
                if (!entry.getName().startsWith(prefix)) {
                    continue;
                }
                String rel = entry.getName().substring(prefix.length());
                if (rel.isEmpty()) {
                    continue;
                }
                Path target = extractDir.resolve(rel).normalize();
                if (!target.startsWith(extractDir)) {
                    throw new IOException("Unsafe jar entry: " + entry.getName());
                }
                if (entry.isDirectory()) {
                    Files.createDirectories(target);
                } else {
                    Files.createDirectories(target.getParent());
                    try (InputStream in = jarFile.getInputStream(entry)) {
                        Files.copy(in, target);
                    }
                }
            }
        }
        return extractDir;
    }

    /**
     * Download {@code url} to a temp file with the {@code .zip} suffix and return its path.
     *
     * <p>The {@code .zip} suffix is load-bearing: {@link FileSystemSkillRepository} uses {@code
     * path.endsWith(".zip")} to detect zip input. Do not change it.
     *
     * @throws IOException on connect / read failures or HTTP error responses.
     */
    public static Path downloadToTempFile(String url, int timeoutMs) throws IOException {
        URL u = new URL(url);
        HttpURLConnection conn = (HttpURLConnection) u.openConnection();
        conn.setConnectTimeout(timeoutMs);
        conn.setReadTimeout(timeoutMs);
        conn.setRequestMethod("GET");
        Path tmpZip = Files.createTempFile(TEMP_DIR_PREFIX, ".zip");
        try (InputStream in = conn.getInputStream()) {
            Files.copy(in, tmpZip, StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException e) {
            Files.deleteIfExists(tmpZip);
            throw e;
        } finally {
            conn.disconnect();
        }
        return tmpZip;
    }

    private static void deleteRecursively(Path path) {
        if (!Files.exists(path)) {
            return;
        }
        try (Stream<Path> walk = Files.walk(path)) {
            walk.sorted(Comparator.reverseOrder())
                    .forEach(
                            p -> {
                                try {
                                    Files.delete(p);
                                } catch (IOException ignored) {
                                    // Cleanup is best-effort.
                                }
                            });
        } catch (IOException ignored) {
            // Cleanup is best-effort.
        }
    }
}
