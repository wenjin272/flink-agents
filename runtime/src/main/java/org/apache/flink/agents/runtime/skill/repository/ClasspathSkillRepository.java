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
import java.net.URISyntaxException;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Enumeration;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;

/**
 * Skill repository backed by a classpath resource — either a directory under {@code
 * src/main/resources} (typical dev / Maven layout) or a path inside a JAR on the classpath (typical
 * deployment).
 *
 * <p>For directory resources the underlying {@link FileSystemSkillRepository} uses the real on-disk
 * path. For JAR-entry resources, the matching entries are extracted into a process-local temp
 * directory (cleaned up at JVM exit).
 *
 * <p>When a {@link URLClassLoader} is used and the JAR does not contain an explicit directory entry
 * for the resource prefix, this class falls back to scanning the classloader's URLs directly to
 * synthesize the correct {@code jar:} URL.
 */
public class ClasspathSkillRepository extends FileSystemSkillRepository {

    public ClasspathSkillRepository(String resource) throws IOException {
        this(resource, Thread.currentThread().getContextClassLoader());
    }

    /**
     * Constructor that accepts an explicit classloader. Useful in tests to inject a {@code
     * URLClassLoader} pointing at a freshly-built jar.
     */
    public ClasspathSkillRepository(String resource, ClassLoader classLoader) throws IOException {
        super(materialize(resource, classLoader));
    }

    private static Path materialize(String resource, ClassLoader classLoader) throws IOException {
        URL url = classLoader.getResource(resource);
        if (url == null) {
            // Fallback for URLClassLoader: JARs without explicit directory entries will not return
            // a URL for a prefix via getResource(). Scan the classloader's URLs directly to find
            // any JAR entry that starts with the resource prefix.
            url = findInUrlClassLoader(resource, classLoader);
        }
        if (url == null) {
            throw new IllegalArgumentException("Classpath resource not found: " + resource);
        }
        String protocol = url.getProtocol();
        if ("file".equals(protocol)) {
            Path p;
            try {
                p = Paths.get(url.toURI());
            } catch (URISyntaxException e) {
                throw new IOException("Bad classpath URL: " + url, e);
            }
            if (Files.isDirectory(p)) {
                return p;
            }
            if (Files.isRegularFile(p) && p.toString().toLowerCase().endsWith(".zip")) {
                return SkillMaterializer.extractZipSafely(p);
            }
            throw new IllegalArgumentException(
                    "Classpath resource must be a directory or a .zip: " + p);
        }
        if ("jar".equals(protocol)) {
            return SkillMaterializer.extractClasspathFromJar(url, resource);
        }
        throw new IllegalArgumentException(
                "Unsupported classpath URL protocol: " + protocol + " for " + resource);
    }

    /**
     * Scans the URLs of a {@link URLClassLoader} for any JAR that contains at least one entry under
     * the given resource prefix. Returns a synthesized {@code jar:} URL for the prefix if found, or
     * {@code null} if not found or if the classloader is not a {@link URLClassLoader}.
     */
    private static URL findInUrlClassLoader(String resource, ClassLoader classLoader)
            throws IOException {
        if (!(classLoader instanceof URLClassLoader)) {
            return null;
        }
        String prefix = resource.endsWith("/") ? resource : resource + "/";
        for (URL u : ((URLClassLoader) classLoader).getURLs()) {
            String uStr = u.toString();
            if (!uStr.endsWith(".jar")) {
                continue;
            }
            File jarFileObj;
            try {
                jarFileObj = new File(u.toURI());
            } catch (URISyntaxException e) {
                continue;
            }
            try (JarFile jf = new JarFile(jarFileObj)) {
                Enumeration<JarEntry> entries = jf.entries();
                while (entries.hasMoreElements()) {
                    JarEntry entry = entries.nextElement();
                    if (entry.getName().startsWith(prefix)) {
                        return new URL("jar:" + uStr + "!/" + resource);
                    }
                }
            }
        }
        return null;
    }
}
