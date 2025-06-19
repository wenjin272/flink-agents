package org.apache.flink.agents.runtime.context;

import org.apache.flink.agents.api.Event;
import org.apache.flink.agents.api.context.RunnerContext;
import org.apache.flink.util.Preconditions;

import java.util.ArrayList;
import java.util.List;

/**
 * The implementation class of {@link RunnerContext}, which serves as the execution context for
 * Java-based actions.
 */
public class RunnerContextImpl implements RunnerContext {

    protected final List<Event> events = new ArrayList<>();

    @Override
    public void sendEvent(Event event) {
        events.add(event);
    }

    public List<Event> drainEvents() {
        List<Event> list = new ArrayList<>(this.events);
        this.events.clear();
        return list;
    }

    public void checkNoPendingEvents() {
        Preconditions.checkState(
                this.events.isEmpty(), "There are pending events remaining in the context.");
    }
}
