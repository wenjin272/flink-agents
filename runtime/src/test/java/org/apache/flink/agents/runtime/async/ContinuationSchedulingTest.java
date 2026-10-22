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

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assumptions.assumeTrue;

/** Exercises the actual JDK 21 executor, including its queued single and batch calls. */
@Timeout(15)
class ContinuationSchedulingTest {
    @BeforeEach
    void requireContinuations() {
        assumeTrue(ContinuationActionExecutor.isContinuationSupported());
    }

    @ParameterizedTest
    @ValueSource(booleans = {false, true})
    void earlierInputFollowUpOvertakesQueuedLaterInput(boolean batch) throws Exception {
        ContinuationActionExecutor executor = new ContinuationActionExecutor(1);
        CountDownLatch blockerStarted = new CountDownLatch(1);
        CountDownLatch releaseBlocker = new CountDownLatch(1);
        CompletableFuture<Void> allowFollowUp = new CompletableFuture<>();
        AtomicBoolean firstCallFinished = new AtomicBoolean();
        List<String> calls = Collections.synchronizedList(new ArrayList<>());
        ContinuationContext early = context(0, 0);
        ContinuationContext blocker = context(1, 0);
        ContinuationContext late = context(2, 0);
        Runnable earlyAction =
                () -> {
                    try {
                        executor.executeAsync(early, () -> calls.add("early-first"));
                        firstCallFinished.set(true);
                        executor.awaitFuture(early, allowFollowUp);
                        call(executor, early, batch, "early-follow-up", calls);
                    } catch (Exception e) {
                        throw new RuntimeException(e);
                    }
                };
        Runnable blockingAction =
                () -> {
                    try {
                        executor.executeAsync(
                                blocker,
                                () -> {
                                    blockerStarted.countDown();
                                    await(releaseBlocker);
                                    return null;
                                });
                    } catch (Exception e) {
                        throw new RuntimeException(e);
                    }
                };
        Runnable lateAction = () -> call(executor, late, batch, "late-first", calls);
        try {
            long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5);
            while (!firstCallFinished.get()) {
                executor.executeAction(early, earlyAction);
                assertThat(System.nanoTime()).isLessThan(deadline);
                Thread.sleep(1);
            }
            assertThat(executor.executeAction(blocker, blockingAction)).isFalse();
            assertThat(blockerStarted.await(5, TimeUnit.SECONDS)).isTrue();
            assertThat(executor.executeAction(late, lateAction)).isFalse();
            allowFollowUp.complete(null);
            assertThat(executor.executeAction(early, earlyAction)).isFalse();
            releaseBlocker.countDown();
            finish(executor, early, earlyAction);
            finish(executor, late, lateAction);
            finish(executor, blocker, blockingAction);
            if (batch) {
                assertThat(calls)
                        .containsExactly(
                                "early-first",
                                "early-follow-up-1",
                                "early-follow-up-2",
                                "late-first-1",
                                "late-first-2");
            } else {
                assertThat(calls).containsExactly("early-first", "early-follow-up", "late-first");
            }
        } finally {
            releaseBlocker.countDown();
            executor.close();
        }
    }

    @Test
    void queuedTasksUseTaskPriorityThenSubmissionOrder() throws Exception {
        ContinuationActionExecutor executor = new ContinuationActionExecutor(1);
        CountDownLatch started = new CountDownLatch(1);
        CountDownLatch release = new CountDownLatch(1);
        List<String> calls = Collections.synchronizedList(new ArrayList<>());
        ContinuationContext blocker = context(0, 0);
        Runnable blocking =
                () -> {
                    try {
                        executor.executeAsync(
                                blocker,
                                () -> {
                                    started.countDown();
                                    await(release);
                                    return null;
                                });
                    } catch (Exception e) {
                        throw new RuntimeException(e);
                    }
                };
        ContinuationContext laterTask = context(1, 2);
        ContinuationContext firstTask = context(1, 1);
        ContinuationContext samePriority = context(1, 1);
        Runnable later = () -> call(executor, laterTask, false, "later-task", calls);
        Runnable first = () -> call(executor, firstTask, false, "first-task", calls);
        Runnable tied = () -> call(executor, samePriority, false, "same-priority", calls);
        try {
            executor.executeAction(blocker, blocking);
            assertThat(started.await(5, TimeUnit.SECONDS)).isTrue();
            executor.executeAction(laterTask, later);
            executor.executeAction(firstTask, first);
            executor.executeAction(samePriority, tied);
            release.countDown();
            finish(executor, laterTask, later);
            finish(executor, firstTask, first);
            finish(executor, samePriority, tied);
            finish(executor, blocker, blocking);
            assertThat(calls).containsExactly("first-task", "same-priority", "later-task");
        } finally {
            release.countDown();
            executor.close();
        }
    }

    private static ContinuationContext context(long record, long task) {
        ContinuationContext context = new ContinuationContext();
        context.setPriority(record, task);
        return context;
    }

    private static void call(
            ContinuationActionExecutor executor,
            ContinuationContext context,
            boolean batch,
            String name,
            List<String> calls) {
        try {
            if (batch) {
                executor.executeAllAsync(
                        context,
                        List.of(() -> calls.add(name + "-1"), () -> calls.add(name + "-2")),
                        null,
                        2);
            } else {
                executor.executeAsync(context, () -> calls.add(name));
            }
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    private static void finish(
            ContinuationActionExecutor executor, ContinuationContext context, Runnable action)
            throws Exception {
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5);
        while (!executor.executeAction(context, action)) {
            assertThat(System.nanoTime()).isLessThan(deadline);
            Thread.sleep(1);
        }
    }

    private static void await(CountDownLatch latch) {
        try {
            if (!latch.await(5, TimeUnit.SECONDS)) {
                throw new IllegalStateException("Timed out waiting for test release");
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException(e);
        }
    }
}
