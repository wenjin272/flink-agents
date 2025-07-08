package org.apache.flink.agents.runtime.utils;

import org.apache.flink.agents.api.Event;
import org.apache.flink.agents.api.InputEvent;
import org.apache.flink.agents.api.OutputEvent;
import org.apache.flink.agents.runtime.python.event.PythonEvent;

/** Utilities related to the {@link Event}. */
public class EventUtil {

    public static final String PYTHON_INPUT_EVENT_NAME = "flink_agents.api.event.InputEvent";

    public static final String PYTHON_OUTPUT_EVENT_NAME = "flink_agents.api.event.OutputEvent";

    public static boolean isInputEvent(Event event) {
        if (event instanceof InputEvent) {
            return true;
        }
        return event instanceof PythonEvent
                && ((PythonEvent) event).getEventType().equals(PYTHON_INPUT_EVENT_NAME);
    }

    public static boolean isOutputEvent(Event event) {
        if (event instanceof OutputEvent) {
            return true;
        }
        return event instanceof PythonEvent
                && ((PythonEvent) event).getEventType().equals(PYTHON_OUTPUT_EVENT_NAME);
    }
}
