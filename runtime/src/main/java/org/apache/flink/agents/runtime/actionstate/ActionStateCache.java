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
package org.apache.flink.agents.runtime.actionstate;

import org.apache.flink.agents.api.Event;
import org.apache.flink.agents.runtime.utils.EventUtil;

import java.util.AbstractMap;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.NavigableMap;
import java.util.Set;
import java.util.TreeMap;
import java.util.UUID;
import java.util.function.Consumer;

/**
 * Action completions and replay evidence, indexed by business key and input sequence.
 *
 * <p>All mutations must go through put/remove/clear, including tombstones and checkpoint pruning.
 * Map views are read-only. Like the stores, this cache is confined to the operator's serialized
 * state-access path. It does not add a durable identity or change the persisted key format.
 *
 * <p>Lookup costs O(log R) for R cached rounds of the requested key. Invalidation visits only
 * removed rounds/states. Indexing a record costs O(log R + E), where E is its completed output
 * event count. Neither lookup nor replay scans other keys or every action in the current round.
 */
final class ActionStateCache extends AbstractMap<String, ActionState> {
    private final Map<String, ActionState> states;
    private final Map<String, IndexedState> indexedStates = new HashMap<>();
    private final Map<String, NavigableMap<Long, Round>> roundsByKey = new HashMap<>();

    ActionStateCache() {
        this(new HashMap<>());
    }

    private ActionStateCache(Map<String, ActionState> states) {
        this.states = states;
        states.forEach(this::index);
    }

    /** Test constructors may supply preloaded state; the supplied map must not be mutated later. */
    static ActionStateCache wrap(Map<String, ActionState> states) {
        return states instanceof ActionStateCache
                ? (ActionStateCache) states
                : new ActionStateCache(states);
    }

    @Override
    public ActionState get(Object key) {
        return states.get(key);
    }

    @Override
    public boolean containsKey(Object key) {
        return states.containsKey(key);
    }

    @Override
    public int size() {
        return states.size();
    }

    @Override
    public Set<Entry<String, ActionState>> entrySet() {
        return Collections.unmodifiableMap(states).entrySet();
    }

    @Override
    public Set<String> keySet() {
        return Collections.unmodifiableMap(states).keySet();
    }

    @Override
    public ActionState put(String key, ActionState state) {
        ActionState previous = remove(key);
        states.put(key, state);
        index(key, state);
        return previous;
    }

    private void index(String key, ActionState state) {
        IndexedState indexed = new IndexedState(key, state);
        indexedStates.put(key, indexed);
        Round round =
                roundsByKey
                        .computeIfAbsent(indexed.identity, ignored -> new TreeMap<>())
                        .computeIfAbsent(indexed.sequence, ignored -> new Round());
        round.stateKeys.add(key);
        if (indexed.inputFingerprint != null) {
            round.inputs.merge(indexed.inputFingerprint, 1, Integer::sum);
        }
        indexed.outputIds.forEach(id -> round.outputs.merge(id, 1, Integer::sum));
    }

    @Override
    public ActionState remove(Object key) {
        IndexedState indexed = indexedStates.remove(key);
        if (indexed != null) {
            NavigableMap<Long, Round> rounds = roundsByKey.get(indexed.identity);
            Round round = rounds.get(indexed.sequence);
            round.stateKeys.remove(key);
            if (indexed.inputFingerprint != null) {
                decrement(round.inputs, indexed.inputFingerprint);
            }
            indexed.outputIds.forEach(id -> decrement(round.outputs, id));
            if (round.stateKeys.isEmpty()) {
                rounds.remove(indexed.sequence);
                if (rounds.isEmpty()) {
                    roundsByKey.remove(indexed.identity);
                }
            }
        }
        return states.remove(key);
    }

    private static <T> void decrement(Map<T, Integer> counts, T key) {
        counts.computeIfPresent(key, (ignored, count) -> count == 1 ? null : count - 1);
    }

    @Override
    public void clear() {
        states.clear();
        indexedStates.clear();
        roundsByKey.clear();
    }

    /** Validate a lookup without scanning unrelated states, rounds, or keys. */
    ActionState lookup(String stateKey, Event event, Consumer<String> onRemoval) {
        List<String> fields = ActionStateUtil.parseKey(stateKey);
        String identity = fields.get(4);
        long sequence = Long.parseLong(fields.get(1));
        Round round = round(identity, sequence);
        ActionState cached = states.get(stateKey);
        // Only saved completed producers establish occurrence identity. Reconstructed inputs
        // and subgraph bootstraps may legitimately get fresh random IDs during recovery.
        if (round != null
                && cached != null
                && cached.getTaskEvent() != null
                && !EventUtil.isInputEvent(event)
                && !cached.getTaskEvent().getId().equals(event.getId())
                && round.outputs.containsKey(event.getId())) {
            remove(stateKey);
            onRemoval.accept(stateKey);
        }
        boolean conflict = hasConflictingInput(round, event, fields.get(2));
        if (conflict || !states.containsKey(stateKey)) {
            invalidateFrom(identity, sequence, conflict, onRemoval);
        }
        return states.get(stateKey);
    }

    /**
     * Replay one non-tombstone record in partition/bucket order. A rewrite of an earlier round
     * invalidates its old suffix even if the next checkpoint skips that round's input lookup.
     */
    void replay(String stateKey, ActionState state, Consumer<String> onRemoval) {
        List<String> fields = ActionStateUtil.parseKey(stateKey);
        String identity = fields.get(4);
        long sequence = Long.parseLong(fields.get(1));
        boolean conflict =
                hasConflictingInput(round(identity, sequence), state.getTaskEvent(), fields.get(2));
        invalidateFrom(identity, sequence, conflict, onRemoval);
        put(stateKey, state);
    }

    private Round round(String identity, long sequence) {
        NavigableMap<Long, Round> rounds = roundsByKey.get(identity);
        return rounds == null ? null : rounds.get(sequence);
    }

    private static boolean hasConflictingInput(Round round, Event event, String fingerprint) {
        return round != null
                && (round.inputs.size() > 1
                        || (event != null
                                && EventUtil.isInputEvent(event)
                                && !round.inputs.isEmpty()
                                && !round.inputs.containsKey(fingerprint)));
    }

    private void invalidateFrom(
            String identity, long sequence, boolean inclusive, Consumer<String> onRemoval) {
        NavigableMap<Long, Round> rounds = roundsByKey.get(identity);
        if (rounds == null) {
            return;
        }
        Iterator<Round> iterator = rounds.tailMap(sequence, inclusive).values().iterator();
        while (iterator.hasNext()) {
            Round round = iterator.next();
            for (String key : round.stateKeys) {
                states.remove(key);
                indexedStates.remove(key);
                onRemoval.accept(key);
            }
            iterator.remove();
        }
        if (rounds.isEmpty()) {
            roundsByKey.remove(identity);
        }
    }

    /** Only visits the prefix that checkpoint completion can prune. */
    List<String> keysThrough(String identity, long sequence) {
        List<String> keys = new ArrayList<>();
        NavigableMap<Long, Round> rounds = roundsByKey.get(identity);
        if (rounds != null) {
            rounds.headMap(sequence, true).values().forEach(round -> keys.addAll(round.stateKeys));
        }
        return keys;
    }

    /**
     * Checkpoint refresh must append each key's rounds in order, including recovered future work.
     */
    List<String> keysInReplayOrder() {
        List<String> keys = new ArrayList<>(size());
        roundsByKey
                .values()
                .forEach(rounds -> rounds.values().forEach(round -> keys.addAll(round.stateKeys)));
        return keys;
    }

    private static final class Round {
        final Set<String> stateKeys = new HashSet<>();
        final Map<String, Integer> inputs = new HashMap<>();
        final Map<UUID, Integer> outputs = new HashMap<>();
    }

    private static final class IndexedState {
        final String identity;
        final long sequence;
        final String inputFingerprint;
        final Set<UUID> outputIds = new HashSet<>();

        IndexedState(String key, ActionState state) {
            List<String> fields = ActionStateUtil.parseKey(key);
            identity = fields.get(4);
            sequence = Long.parseLong(fields.get(1));
            Event input = state.getTaskEvent();
            inputFingerprint =
                    input != null && EventUtil.isInputEvent(input) ? fields.get(2) : null;
            // Snapshot the evidence: callers mutate ActionState in place before the next put.
            if (state.isCompleted()) {
                state.getOutputEvents().forEach(event -> outputIds.add(event.getId()));
            }
        }
    }
}
