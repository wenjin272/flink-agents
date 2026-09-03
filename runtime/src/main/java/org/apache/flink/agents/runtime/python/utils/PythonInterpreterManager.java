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
package org.apache.flink.agents.runtime.python.utils;

import org.apache.flink.util.ExceptionUtils;
import pemja.core.PythonInterpreter;

import java.util.List;
import java.util.Objects;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.locks.ReentrantReadWriteLock;
import java.util.function.Consumer;
import java.util.function.Function;
import java.util.function.Supplier;

/**
 * Owns the Pemja interpreters used by one operator subtask.
 *
 * <p>A {@link PythonInterpreter} is never shared by concurrently executing threads. The first
 * bridge call on a thread creates an interpreter and binds it to that thread for the lifetime of
 * this manager. Nested Python-to-Java-to-Python calls therefore reuse the same interpreter and run
 * inline, while calls made by different async workers use different interpreters.
 *
 * <p>Pemja's {@code MULTI_THREAD} interpreters share the same CPython main interpreter, so Python
 * resource objects can still be initialized once and passed as opaque handles to calls made by any
 * of these thread-confined interpreters. Each interpreter has its own globals, however, so the
 * bridge modules must be imported for every newly created interpreter.
 */
public final class PythonInterpreterManager implements AutoCloseable {

    static final String PYTHON_IMPORTS =
            "from flink_agents.plan import function\n"
                    + "from flink_agents.runtime import flink_runner_context\n"
                    + "from flink_agents.runtime import python_java_utils";

    private final Supplier<PythonInterpreter> interpreterFactory;
    private final Consumer<PythonInterpreter> interpreterInitializer;
    private final List<PythonInterpreter> interpreters = new CopyOnWriteArrayList<>();
    private final ThreadLocal<PythonInterpreter> threadInterpreter = new ThreadLocal<>();
    private final ReentrantReadWriteLock lifecycleLock = new ReentrantReadWriteLock();

    private volatile boolean closed;

    public PythonInterpreterManager(
            PythonInterpreter ownerInterpreter, Supplier<PythonInterpreter> interpreterFactory) {
        this(ownerInterpreter, interpreterFactory, PythonInterpreterManager::initializeInterpreter);
    }

    PythonInterpreterManager(
            PythonInterpreter ownerInterpreter,
            Supplier<PythonInterpreter> interpreterFactory,
            Consumer<PythonInterpreter> interpreterInitializer) {
        this.interpreterFactory = Objects.requireNonNull(interpreterFactory);
        this.interpreterInitializer = Objects.requireNonNull(interpreterInitializer);

        PythonInterpreter initializedOwner = initialize(Objects.requireNonNull(ownerInterpreter));
        interpreters.add(initializedOwner);
        threadInterpreter.set(initializedOwner);
    }

    /** Executes an operation using the interpreter bound to the calling thread. */
    public <T> T withInterpreter(Function<PythonInterpreter, T> operation) {
        lifecycleLock.readLock().lock();
        try {
            if (closed) {
                throw new IllegalStateException("Python interpreter manager is already closed.");
            }
            return Objects.requireNonNull(operation).apply(currentInterpreter());
        } finally {
            lifecycleLock.readLock().unlock();
        }
    }

    public void exec(String code) {
        withInterpreter(
                interpreter -> {
                    interpreter.exec(code);
                    return null;
                });
    }

    public Object invoke(String name, Object... args) {
        return withInterpreter(interpreter -> interpreter.invoke(name, args));
    }

    public Object get(String name) {
        return withInterpreter(interpreter -> interpreter.get(name));
    }

    public void set(String name, Object value) {
        withInterpreter(
                interpreter -> {
                    interpreter.set(name, value);
                    return null;
                });
    }

    private PythonInterpreter currentInterpreter() {
        PythonInterpreter interpreter = threadInterpreter.get();
        if (interpreter != null) {
            return interpreter;
        }

        PythonInterpreter created = initialize(interpreterFactory.get());
        interpreters.add(created);
        threadInterpreter.set(created);
        return created;
    }

    private PythonInterpreter initialize(PythonInterpreter interpreter) {
        Objects.requireNonNull(interpreter);
        try {
            interpreterInitializer.accept(interpreter);
            return interpreter;
        } catch (Throwable initializationFailure) {
            try {
                interpreter.close();
            } catch (Throwable closeFailure) {
                initializationFailure.addSuppressed(closeFailure);
            }
            throw initializationFailure;
        }
    }

    private static void initializeInterpreter(PythonInterpreter interpreter) {
        interpreter.exec(PYTHON_IMPORTS);
    }

    @Override
    public void close() throws Exception {
        lifecycleLock.writeLock().lock();
        try {
            if (closed) {
                return;
            }
            closed = true;
            threadInterpreter.remove();

            Throwable firstFailure = null;
            for (int i = interpreters.size() - 1; i >= 0; i--) {
                try {
                    interpreters.get(i).close();
                } catch (Throwable closeFailure) {
                    firstFailure = ExceptionUtils.firstOrSuppressed(closeFailure, firstFailure);
                }
            }
            interpreters.clear();

            if (firstFailure != null) {
                ExceptionUtils.rethrowException(firstFailure);
            }
        } finally {
            lifecycleLock.writeLock().unlock();
        }
    }
}
