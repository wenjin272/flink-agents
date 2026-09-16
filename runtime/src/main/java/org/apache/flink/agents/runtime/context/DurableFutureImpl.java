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
package org.apache.flink.agents.runtime.context;

import org.apache.flink.agents.api.context.DurableCallable;
import org.apache.flink.agents.api.context.DurableFuture;
import org.apache.flink.agents.api.context.Outcome;
import org.apache.flink.util.Preconditions;

import java.util.ArrayList;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Set;

/** Runtime-owned implementation of a deferred durable call handle. */
abstract class DurableFutureImpl<T> implements DurableFuture<T> {
    private final RunnerContextImpl owner;
    private boolean resolving;
    private boolean done;
    private T value;
    private Exception error;

    DurableFutureImpl(RunnerContextImpl owner) {
        this.owner = owner;
    }

    final RunnerContextImpl getOwner() {
        return owner;
    }

    final boolean isDone() {
        return done;
    }

    @Override
    public final T await() throws Exception {
        if (done) {
            return completedValue();
        }
        if (resolving) {
            throw new IllegalStateException("A durable future cannot await itself recursively");
        }

        resolving = true;
        try {
            value = resolveValue();
            done = true;
            return value;
        } catch (Exception e) {
            error = e;
            done = true;
            throw e;
        } finally {
            resolving = false;
        }
    }

    final void complete(Outcome<T> outcome) {
        if (done) {
            throw new IllegalStateException("Durable future has already been resolved");
        }
        value = outcome.getValue();
        error = outcome.getError();
        done = true;
    }

    private T completedValue() throws Exception {
        if (error != null) {
            throw error;
        }
        return value;
    }

    abstract T resolveValue() throws Exception;
}

/** Deferred handle for one durable callable. */
final class SingleDurableFuture<T> extends DurableFutureImpl<T> {
    private final DurableCallable<T> callable;

    SingleDurableFuture(RunnerContextImpl owner, DurableCallable<T> callable) {
        super(owner);
        this.callable = callable;
    }

    DurableCallable<T> getCallable() {
        return callable;
    }

    @Override
    T resolveValue() throws Exception {
        return getOwner().resolveDurableAsync(callable);
    }
}

/** Deferred handle for a batch of durable call handles. */
final class GatherDurableFuture<T> extends DurableFutureImpl<List<Outcome<T>>> {
    private final List<SingleDurableFuture<T>> futures;

    GatherDurableFuture(RunnerContextImpl owner, List<? extends DurableFuture<T>> durableFutures) {
        super(owner);
        Preconditions.checkNotNull(durableFutures, "futures must not be null");

        List<SingleDurableFuture<T>> singleFutures = new ArrayList<>(durableFutures.size());
        Set<DurableFuture<T>> seen = Collections.newSetFromMap(new IdentityHashMap<>());
        for (DurableFuture<T> future : durableFutures) {
            Preconditions.checkNotNull(future, "future must not be null");
            if (!seen.add(future)) {
                throw new IllegalArgumentException(
                        "The same durable future cannot appear more than once in gather");
            }
            if (!(future instanceof DurableFutureImpl)) {
                throw new IllegalArgumentException(
                        "The durable future was not created by a Flink Agents runner context");
            }
            DurableFutureImpl<?> internalFuture = (DurableFutureImpl<?>) future;
            if (internalFuture.getOwner() != owner) {
                throw new IllegalArgumentException(
                        "All durable futures passed to gather must be created by this runner context");
            }
            if (!(internalFuture instanceof SingleDurableFuture)) {
                throw new IllegalArgumentException(
                        "gather only accepts futures returned by durableExecuteAsync");
            }
            if (internalFuture.isDone()) {
                throw new IllegalArgumentException(
                        "gather only accepts durable futures that have not been resolved");
            }
            @SuppressWarnings("unchecked")
            SingleDurableFuture<T> singleFuture = (SingleDurableFuture<T>) internalFuture;
            singleFutures.add(singleFuture);
        }
        this.futures = List.copyOf(singleFutures);
    }

    @Override
    List<Outcome<T>> resolveValue() throws Exception {
        List<DurableCallable<T>> callables = new ArrayList<>(futures.size());
        for (SingleDurableFuture<T> future : futures) {
            if (future.isDone()) {
                throw new IllegalStateException(
                        "A durable future passed to gather has already been resolved");
            }
            callables.add(future.getCallable());
        }

        List<Outcome<T>> outcomes = getOwner().resolveDurableBatch(callables);
        for (int i = 0; i < futures.size(); i++) {
            futures.get(i).complete(outcomes.get(i));
        }
        return outcomes;
    }
}
