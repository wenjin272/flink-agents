# Python Event Processing

<cite>
**Referenced Files in This Document**
- [Event.java](file://api/src/main/java/org/apache/flink/agents/api/Event.java)
- [InputEvent.java](file://api/src/main/java/org/apache/flink/agents/api/InputEvent.java)
- [OutputEvent.java](file://api/src/main/java/org/apache/flink/agents/api/OutputEvent.java)
- [ChatRequestEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ChatRequestEvent.java)
- [ChatResponseEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ChatResponseEvent.java)
- [ToolRequestEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ToolRequestEvent.java)
- [ToolResponseEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ToolResponseEvent.java)
- [ContextRetrievalRequestEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ContextRetrievalRequestEvent.java)
- [ContextRetrievalResponseEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ContextRetrievalResponseEvent.java)
- [event.py](file://python/flink_agents/api/events/event.py)
- [chat_event.py](file://python/flink_agents/api/events/chat_event.py)
- [tool_event.py](file://python/flink_agents/api/events/tool_event.py)
- [context_retrieval_event.py](file://python/flink_agents/api/events/context_retrieval_event.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)

## Introduction
This document explains Python event processing in Flink Agents, focusing on the Python event model and its relationship with the Java event system. It covers event types, event handling patterns, and cross-language execution. It also documents chat events, tool events, and context retrieval events, including their data structures and processing workflows. Topics include event subscription, filtering, transformation, custom event processing, logging, debugging, performance considerations, and best practices for building event-driven Python agents.

## Project Structure
Flink Agents defines a unified event model across Java and Python:
- Java base event types and concrete event types live under the Java API package.
- Python event types mirror the Java event semantics and are defined under the Python API’s events module.
- Both sides share common concepts: base event with identity and attributes, input/output events for framework-generated and agent-emitted results, and domain-specific events for chat, tool use, and context retrieval.

```mermaid
graph TB
subgraph "Java API"
J_Event["Event (base)"]
J_Input["InputEvent"]
J_Output["OutputEvent"]
J_ChatReq["ChatRequestEvent"]
J_ChatResp["ChatResponseEvent"]
J_ToolReq["ToolRequestEvent"]
J_ToolResp["ToolResponseEvent"]
J_ContextReq["ContextRetrievalRequestEvent"]
J_ContextResp["ContextRetrievalResponseEvent"]
end
subgraph "Python API"
P_Event["Event (base)"]
P_Input["InputEvent"]
P_Output["OutputEvent"]
P_ChatReq["ChatRequestEvent"]
P_ChatResp["ChatResponseEvent"]
P_ToolReq["ToolRequestEvent"]
P_ToolResp["ToolResponseEvent"]
P_ContextReq["ContextRetrievalRequestEvent"]
P_ContextResp["ContextRetrievalResponseEvent"]
end
J_Event --> J_Input
J_Event --> J_Output
J_Event --> J_ChatReq
J_Event --> J_ChatResp
J_Event --> J_ToolReq
J_Event --> J_ToolResp
J_Event --> J_ContextReq
J_Event --> J_ContextResp
P_Event --> P_Input
P_Event --> P_Output
P_Event --> P_ChatReq
P_Event --> P_ChatResp
P_Event --> P_ToolReq
P_Event --> P_ToolResp
P_Event --> P_ContextReq
P_Event --> P_ContextResp
```

**Diagram sources**
- [Event.java](file://api/src/main/java/org/apache/flink/agents/api/Event.java#L29-L90)
- [InputEvent.java](file://api/src/main/java/org/apache/flink/agents/api/InputEvent.java#L27-L49)
- [OutputEvent.java](file://api/src/main/java/org/apache/flink/agents/api/OutputEvent.java#L27-L52)
- [ChatRequestEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ChatRequestEvent.java#L28-L58)
- [ChatResponseEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ChatResponseEvent.java#L26-L43)
- [ToolRequestEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ToolRequestEvent.java#L26-L63)
- [ToolResponseEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ToolResponseEvent.java#L27-L95)
- [ContextRetrievalRequestEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ContextRetrievalRequestEvent.java#L23-L70)
- [ContextRetrievalResponseEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ContextRetrievalResponseEvent.java#L27-L65)
- [event.py](file://python/flink_agents/api/events/event.py#L33-L114)
- [chat_event.py](file://python/flink_agents/api/events/chat_event.py#L26-L57)
- [tool_event.py](file://python/flink_agents/api/events/tool_event.py#L24-L56)
- [context_retrieval_event.py](file://python/flink_agents/api/events/context_retrieval_event.py#L25-L57)

**Section sources**
- [Event.java](file://api/src/main/java/org/apache/flink/agents/api/Event.java#L29-L90)
- [InputEvent.java](file://api/src/main/java/org/apache/flink/agents/api/InputEvent.java#L27-L49)
- [OutputEvent.java](file://api/src/main/java/org/apache/flink/agents/api/OutputEvent.java#L27-L52)
- [event.py](file://python/flink_agents/api/events/event.py#L33-L114)

## Core Components
- Base event model
  - Java: Base class with a stable identity, attributes map, and optional source timestamp.
  - Python: Pydantic-based base class with deterministic content-based ID generation, JSON serialization support, and dynamic extra fields.
- Input and Output events
  - Java: InputEvent carries framework-provided input; OutputEvent carries agent-emitted results.
  - Python: Mirrors these semantics with typed fields for input and output.
- Domain events
  - Chat events: Request and response events for chat model interactions.
  - Tool events: Request and response events for tool invocation and results.
  - Context retrieval events: Request and response events for vector store queries.

**Section sources**
- [Event.java](file://api/src/main/java/org/apache/flink/agents/api/Event.java#L29-L90)
- [InputEvent.java](file://api/src/main/java/org/apache/flink/agents/api/InputEvent.java#L27-L49)
- [OutputEvent.java](file://api/src/main/java/org/apache/flink/agents/api/OutputEvent.java#L27-L52)
- [event.py](file://python/flink_agents/api/events/event.py#L33-L114)
- [chat_event.py](file://python/flink_agents/api/events/chat_event.py#L26-L57)
- [tool_event.py](file://python/flink_agents/api/events/tool_event.py#L24-L56)
- [context_retrieval_event.py](file://python/flink_agents/api/events/context_retrieval_event.py#L25-L57)

## Architecture Overview
The event processing architecture connects Java-defined event types with Python event types. The Python event classes inherit the same semantic roles as their Java counterparts, enabling cross-language interoperability. Events flow through the runtime, where actions subscribe to specific event types, filter them, transform them, and emit new events.

```mermaid
sequenceDiagram
participant Java as "Java Runtime"
participant Plan as "Agent Plan"
participant Py as "Python Runtime"
participant Sub as "Event Subscriber"
participant Log as "Event Logger"
Java->>Plan : "Emit domain event (e.g., ChatRequest)"
Plan->>Py : "Bridge event to Python"
Py->>Sub : "Dispatch matching event handler"
Sub->>Py : "Transform/Filter/Customize event"
Py-->>Java : "Emit OutputEvent or downstream event"
Java->>Log : "Log events with attributes and timestamps"
```

[No sources needed since this diagram shows conceptual workflow, not actual code structure]

## Detailed Component Analysis

### Base Event Model
- Java Event
  - Provides a stable UUID identity, a mutable attributes map, and optional source timestamp.
  - Enables attaching metadata to events and correlating related events.
- Python Event
  - Deterministic content-based ID generation ensures reproducible identities for equivalent event payloads.
  - Robust JSON serialization with a fallback for non-serializable types (e.g., Row).
  - Supports dynamic extra fields while maintaining schema safety via Pydantic validators.

```mermaid
classDiagram
class Java_Event {
+UUID id
+Map~String,Object~ attributes
+Long sourceTimestamp
+getId() UUID
+getAttr(name) Object
+setAttr(name,value) void
+hasSourceTimestamp() boolean
+getSourceTimestamp() Long
+setSourceTimestamp(timestamp) void
}
class Python_Event {
+UUID id
+model_dump_json(**kwargs) str
+validate_and_set_id() Event
+__setattr__(name, value) void
-_generate_content_based_id() UUID
-__serialize_unknown(field) Dict
}
Java_Event <|-- Java_InputEvent
Java_Event <|-- Java_OutputEvent
Java_Event <|-- Java_DomainEvents
Python_Event <|-- Python_InputEvent
Python_Event <|-- Python_OutputEvent
Python_Event <|-- Python_DomainEvents
```

**Diagram sources**
- [Event.java](file://api/src/main/java/org/apache/flink/agents/api/Event.java#L29-L90)
- [InputEvent.java](file://api/src/main/java/org/apache/flink/agents/api/InputEvent.java#L27-L49)
- [OutputEvent.java](file://api/src/main/java/org/apache/flink/agents/api/OutputEvent.java#L27-L52)
- [event.py](file://python/flink_agents/api/events/event.py#L33-L114)

**Section sources**
- [Event.java](file://api/src/main/java/org/apache/flink/agents/api/Event.java#L29-L90)
- [event.py](file://python/flink_agents/api/events/event.py#L33-L114)

### Chat Events
- Java ChatRequestEvent
  - Fields: model name, message list, optional output schema.
  - Used to initiate chat model interactions.
- Java ChatResponseEvent
  - Fields: request correlation ID and response message.
  - Carries the model’s response back to the caller.
- Python ChatRequestEvent
  - Fields: model, messages, optional output_schema.
- Python ChatResponseEvent
  - Fields: request_id, response.

Processing workflow:
- Emit ChatRequestEvent (Java or Python).
- Subscribe to ChatRequestEvent handlers.
- Transform messages or apply output schema constraints.
- Emit ChatResponseEvent with correlated request_id.

```mermaid
sequenceDiagram
participant Src as "Source"
participant Evt as "ChatRequestEvent"
participant Sub as "Handler"
participant Resp as "ChatResponseEvent"
Src->>Evt : "Create and emit"
Evt-->>Sub : "Dispatch to handler"
Sub->>Sub : "Validate/transform messages"
Sub-->>Resp : "Emit response with request_id"
```

**Diagram sources**
- [ChatRequestEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ChatRequestEvent.java#L28-L58)
- [ChatResponseEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ChatResponseEvent.java#L26-L43)
- [chat_event.py](file://python/flink_agents/api/events/chat_event.py#L26-L57)

**Section sources**
- [ChatRequestEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ChatRequestEvent.java#L28-L58)
- [ChatResponseEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ChatResponseEvent.java#L26-L43)
- [chat_event.py](file://python/flink_agents/api/events/chat_event.py#L26-L57)

### Tool Events
- Java ToolRequestEvent
  - Fields: model, toolCalls list, timestamp.
- Java ToolResponseEvent
  - Fields: request correlation ID, per-call responses, success/error maps, optional external IDs, timestamp.
- Python ToolRequestEvent
  - Fields: model, tool_calls list.
- Python ToolResponseEvent
  - Fields: request_id, responses dict, external_ids dict.

Processing workflow:
- Emit ToolRequestEvent with a batch of tool calls.
- Subscribe to ToolRequestEvent handlers.
- Execute tools and collect results.
- Emit ToolResponseEvent with per-call outcomes and optional external IDs.

```mermaid
sequenceDiagram
participant Src as "Source"
participant Req as "ToolRequestEvent"
participant Exec as "Tool Executor"
participant Resp as "ToolResponseEvent"
Src->>Req : "Emit tool call batch"
Req-->>Exec : "Dispatch to executor"
Exec->>Exec : "Run tools and collect results"
Exec-->>Resp : "Emit ToolResponseEvent with outcomes"
```

**Diagram sources**
- [ToolRequestEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ToolRequestEvent.java#L26-L63)
- [ToolResponseEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ToolResponseEvent.java#L27-L95)
- [tool_event.py](file://python/flink_agents/api/events/tool_event.py#L24-L56)

**Section sources**
- [ToolRequestEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ToolRequestEvent.java#L26-L63)
- [ToolResponseEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ToolResponseEvent.java#L27-L95)
- [tool_event.py](file://python/flink_agents/api/events/tool_event.py#L24-L56)

### Context Retrieval Events
- Java ContextRetrievalRequestEvent
  - Fields: query, vector store name, max results (with default).
- Java ContextRetrievalResponseEvent
  - Fields: request correlation ID, query, documents list.
- Python ContextRetrievalRequestEvent
  - Fields: query, vector store, max_results with default.
- Python ContextRetrievalResponseEvent
  - Fields: request_id, query, documents list.

Processing workflow:
- Emit ContextRetrievalRequestEvent with query and vector store.
- Subscribe to request handlers.
- Query vector store and collect documents.
- Emit ContextRetrievalResponseEvent with retrieved documents.

```mermaid
sequenceDiagram
participant Src as "Source"
participant Req as "ContextRetrievalRequestEvent"
participant VS as "Vector Store"
participant Resp as "ContextRetrievalResponseEvent"
Src->>Req : "Emit retrieval request"
Req-->>VS : "Dispatch query"
VS-->>Resp : "Return documents"
Resp-->>Src : "Emit response with request_id"
```

**Diagram sources**
- [ContextRetrievalRequestEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ContextRetrievalRequestEvent.java#L23-L70)
- [ContextRetrievalResponseEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ContextRetrievalResponseEvent.java#L27-L65)
- [context_retrieval_event.py](file://python/flink_agents/api/events/context_retrieval_event.py#L25-L57)

**Section sources**
- [ContextRetrievalRequestEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ContextRetrievalRequestEvent.java#L23-L70)
- [ContextRetrievalResponseEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ContextRetrievalResponseEvent.java#L27-L65)
- [context_retrieval_event.py](file://python/flink_agents/api/events/context_retrieval_event.py#L25-L57)

### Event Subscription, Filtering, and Transformation
- Subscription
  - Handlers subscribe to specific event types (e.g., ChatRequestEvent, ToolRequestEvent).
  - The runtime dispatches events to matching subscribers.
- Filtering
  - Use event attributes or request correlation IDs to filter irrelevant events.
  - Apply predicates on fields such as model name, vector store, or tool call types.
- Transformation
  - Convert between Java and Python event representations during cross-language execution.
  - Normalize message formats, enrich attributes, or adapt schemas (e.g., output_schema).

[No sources needed since this section provides general guidance]

### Custom Event Processing and Logging
- Custom event processing
  - Define custom event subclasses extending the base Event class in Python.
  - Implement handlers that consume and transform events.
- Event logging
  - Attach metadata via attributes on Java events or extra fields on Python events.
  - Use the runtime’s event logging facilities to capture events with timestamps and IDs.

[No sources needed since this section provides general guidance]

### Relationship Between Python Events and Java Events
- Semantics parity
  - Python event classes mirror Java event semantics for input/output and domain events.
- Cross-language bridging
  - The runtime bridges Java events to Python and vice versa, preserving IDs and attributes.
- Serialization compatibility
  - Python’s deterministic ID and robust serialization align with Java’s event identity and attribute model.

```mermaid
graph LR
J_Base["Java Event (base)"] -- "bridge" --> P_Base["Python Event (base)"]
J_ChatReq["ChatRequestEvent"] -- "bridge" --> P_ChatReq["ChatRequestEvent"]
J_ChatResp["ChatResponseEvent"] -- "bridge" --> P_ChatResp["ChatResponseEvent"]
J_ToolReq["ToolRequestEvent"] -- "bridge" --> P_ToolReq["ToolRequestEvent"]
J_ToolResp["ToolResponseEvent"] -- "bridge" --> P_ToolResp["ToolResponseEvent"]
J_ContextReq["ContextRetrievalRequestEvent"] -- "bridge" --> P_ContextReq["ContextRetrievalRequestEvent"]
J_ContextResp["ContextRetrievalResponseEvent"] -- "bridge" --> P_ContextResp["ContextRetrievalResponseEvent"]
```

**Diagram sources**
- [Event.java](file://api/src/main/java/org/apache/flink/agents/api/Event.java#L29-L90)
- [InputEvent.java](file://api/src/main/java/org/apache/flink/agents/api/InputEvent.java#L27-L49)
- [OutputEvent.java](file://api/src/main/java/org/apache/flink/agents/api/OutputEvent.java#L27-L52)
- [ChatRequestEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ChatRequestEvent.java#L28-L58)
- [ChatResponseEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ChatResponseEvent.java#L26-L43)
- [ToolRequestEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ToolRequestEvent.java#L26-L63)
- [ToolResponseEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ToolResponseEvent.java#L27-L95)
- [ContextRetrievalRequestEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ContextRetrievalRequestEvent.java#L23-L70)
- [ContextRetrievalResponseEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ContextRetrievalResponseEvent.java#L27-L65)
- [event.py](file://python/flink_agents/api/events/event.py#L33-L114)
- [chat_event.py](file://python/flink_agents/api/events/chat_event.py#L26-L57)
- [tool_event.py](file://python/flink_agents/api/events/tool_event.py#L24-L56)
- [context_retrieval_event.py](file://python/flink_agents/api/events/context_retrieval_event.py#L25-L57)

## Dependency Analysis
- Cohesion
  - Each event type encapsulates a single responsibility (request/response or input/output).
- Coupling
  - Handlers depend on event interfaces rather than concrete implementations.
  - Cross-language coupling is mediated by the runtime bridge and shared semantics.
- Serialization and identity
  - Java events rely on Jackson annotations and attribute maps.
  - Python events rely on Pydantic and deterministic ID generation.

```mermaid
graph TB
E["Event (base)"] --> I["InputEvent"]
E --> O["OutputEvent"]
E --> CReq["ChatRequestEvent"]
E --> CResp["ChatResponseEvent"]
E --> TReq["ToolRequestEvent"]
E --> TResp["ToolResponseEvent"]
E --> RReq["ContextRetrievalRequestEvent"]
E --> RResp["ContextRetrievalResponseEvent"]
P_E["Event (base)"] --> P_I["InputEvent"]
P_E --> P_O["OutputEvent"]
P_E --> P_CReq["ChatRequestEvent"]
P_E --> P_CResp["ChatResponseEvent"]
P_E --> P_TReq["ToolRequestEvent"]
P_E --> P_TResp["ToolResponseEvent"]
P_E --> P_RReq["ContextRetrievalRequestEvent"]
P_E --> P_RResp["ContextRetrievalResponseEvent"]
```

**Diagram sources**
- [Event.java](file://api/src/main/java/org/apache/flink/agents/api/Event.java#L29-L90)
- [InputEvent.java](file://api/src/main/java/org/apache/flink/agents/api/InputEvent.java#L27-L49)
- [OutputEvent.java](file://api/src/main/java/org/apache/flink/agents/api/OutputEvent.java#L27-L52)
- [ChatRequestEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ChatRequestEvent.java#L28-L58)
- [ChatResponseEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ChatResponseEvent.java#L26-L43)
- [ToolRequestEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ToolRequestEvent.java#L26-L63)
- [ToolResponseEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ToolResponseEvent.java#L27-L95)
- [ContextRetrievalRequestEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ContextRetrievalRequestEvent.java#L23-L70)
- [ContextRetrievalResponseEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ContextRetrievalResponseEvent.java#L27-L65)
- [event.py](file://python/flink_agents/api/events/event.py#L33-L114)
- [chat_event.py](file://python/flink_agents/api/events/chat_event.py#L26-L57)
- [tool_event.py](file://python/flink_agents/api/events/tool_event.py#L24-L56)
- [context_retrieval_event.py](file://python/flink_agents/api/events/context_retrieval_event.py#L25-L57)

**Section sources**
- [Event.java](file://api/src/main/java/org/apache/flink/agents/api/Event.java#L29-L90)
- [event.py](file://python/flink_agents/api/events/event.py#L33-L114)

## Performance Considerations
- Deterministic IDs reduce duplication and enable efficient deduplication in state stores.
- Prefer lightweight attributes and avoid large payloads in event bodies.
- Batch tool calls when possible to minimize event volume.
- Use event filtering early to reduce unnecessary handler invocations.
- Ensure serialization performance by avoiding expensive transformations inside event constructors.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
- Event identity issues
  - Verify deterministic ID generation and ensure content changes trigger ID recalculation.
- Serialization errors
  - Confirm all fields are JSON serializable; use the provided fallback for special types.
- Correlation problems
  - Always propagate request_id in response events to maintain end-to-end traceability.
- Attribute inspection
  - Use attributes to attach contextual metadata for debugging; log events with timestamps for replay.

[No sources needed since this section provides general guidance]

## Conclusion
Flink Agents’ Python event processing builds on a robust, cross-language event model. The base event semantics, input/output events, and domain-specific events (chat, tool, context retrieval) provide a cohesive foundation for event-driven agent behavior. By leveraging deterministic IDs, strong typing, and cross-runtime bridging, developers can implement reliable, high-throughput event processing pipelines with clear filtering, transformation, and logging capabilities.