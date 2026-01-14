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
package org.apache.flink.agents.runtime.async;

import jdk.internal.vm.Continuation;
import jdk.internal.vm.ContinuationScope;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Supplier;

/**
 * Executor for Java actions that supports asynchronous execution using JDK 21+ Continuation API.
 *
 * <p>This version uses {@code jdk.internal.vm.Continuation} to implement true async execution.
 */
public class ContinuationActionExecutor {

    private static final ContinuationScope SCOPE = new ContinuationScope("FlinkAgentsAction");

    private final ExecutorService asyncExecutor;

    // The current continuation being executed
    private Continuation currentContinuation;

    // The pending async Future - volatile for memory visibility across yield/resume
    private volatile Future<?> pendingFuture;

    // Holds the result of async execution
    private final AtomicReference<Object> asyncResult = new AtomicReference<>();

    // Holds any exception from async execution
    private final AtomicReference<Throwable> asyncException = new AtomicReference<>();

    public ContinuationActionExecutor(ExecutorService asyncExecutor) {
        this.asyncExecutor = asyncExecutor;
    }

    /**
     * Executes the action inside a Continuation.
     *
     * <p>If the action calls executeAsync and yields, this method checks if the async Future is
     * done. If not done, returns false to indicate the action is not finished. If done, resumes the
     * Continuation.
     *
     * @param action the action to execute
     * @return true if the action completed, false if waiting for async execution
     */
    public boolean executeAction(Runnable action) {
        // Check if we have a pending async Future from previous yield
        Future<?> pending = pendingFuture;
        if (pending != null) {
            if (!pending.isDone()) {
                // Async task not done yet, return false to wait
                return false;
            }
            // Async task done, clear the pending future and resume
            pendingFuture = null;
        }

        if (currentContinuation == null) {
            // First invocation: create new Continuation
            currentContinuation = new Continuation(SCOPE, action);
        }

        // Run the continuation
        currentContinuation.run();

        if (currentContinuation.isDone()) {
            // Continuation completed
            currentContinuation = null;
            return true;
        } else {
            // Continuation yielded, waiting for async task
            // pendingFuture should have been set by executeAsync
            return false;
        }
    }

    /**
     * Asynchronously executes the provided supplier using Continuation.
     *
     * <p>This method submits the task to a thread pool and yields the Continuation. The next call
     * to executeAction will check if the Future is done and resume accordingly.
     *
     * @param supplier the supplier to execute
     * @param <T> the result type
     * @return the result of the supplier
     * @throws Exception if the async execution fails
     */
    @SuppressWarnings("unchecked")
    public <T> T executeAsync(Supplier<T> supplier) throws Exception {
        // Clear previous state
        asyncResult.set(null);
        asyncException.set(null);

        // Submit task to thread pool and store the Future
        Future<?> future =
                asyncExecutor.submit(
                        () -> {
                            try {
                                T result = supplier.get();
                                asyncResult.set(result);
                            } catch (Throwable t) {
                                asyncException.set(t);
                            }
                        });

        // Store the future reference before yielding (volatile write ensures visibility)
        pendingFuture = future;

        // Yield until the future is done
        while (!future.isDone()) {
            Continuation.yield(SCOPE);
        }

        // Check for exception from the async task
        Throwable exception = asyncException.get();
        if (exception != null) {
            if (exception instanceof Exception) {
                throw (Exception) exception;
            } else if (exception instanceof Error) {
                throw (Error) exception;
            } else {
                throw new RuntimeException(exception);
            }
        }

        return (T) asyncResult.get();
    }

    /**
     * Returns whether continuation-based async execution is supported.
     *
     * @return true (this is the JDK 21+ version)
     */
    public static boolean isContinuationSupported() {
        return true;
    }
}
