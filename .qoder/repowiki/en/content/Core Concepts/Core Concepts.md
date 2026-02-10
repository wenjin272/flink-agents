# Core Concepts

<cite>
**Referenced Files in This Document**
- [Agent.java](file://api/src/main/java/org/apache/flink/agents/api/agents/Agent.java)
- [ReActAgent.java](file://api/src/main/java/org/apache/flink/agents/api/agents/ReActAgent.java)
- [AgentBuilder.java](file://api/src/main/java/org/apache/flink/agents/api/AgentBuilder.java)
- [AgentsExecutionEnvironment.java](file://api/src/main/java/org/apache/flink/agents/api/AgentsExecutionEnvironment.java)
- [Event.java](file://api/src/main/java/org/apache/flink/agents/api/Event.java)
- [ChatRequestEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ChatRequestEvent.java)
- [RunnerContext.java](file://api/src/main/java/org/apache/flink/agents/api/context/RunnerContext.java)
- [MemoryObject.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryObject.java)
- [MemoryRef.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryRef.java)
- [MemoryUpdate.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryUpdate.java)
- [BaseLongTermMemory.java](file://api/src/main/java/org/apache/flink/agents/api/memory/BaseLongTermMemory.java)
- [BaseVectorStore.java](file://api/src/main/java/org/apache/flink/agents/api/vectorstores/BaseVectorStore.java)
- [Resource.java](file://api/src/main/java/org/apache/flink/agents/api/resource/Resource.java)
- [ResourceProvider.java](file://plan/src/main/java/org/apache/flink/agents/plan/resourceprovider/ResourceProvider.java)
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
This document explains the core concepts of Flink Agents with a focus on architectural patterns and runtime mechanics:
- Agent-based programming: agents encapsulate behavior as actions that react to events.
- Event-driven architecture: the system is built around typed events and asynchronous processing.
- Resource provider pattern: resources (chat models, prompts, vector stores) are declared and instantiated via providers.
- Memory hierarchy: sensory memory, short-term memory, and long-term memory backed by vector stores.
- Execution environment and plan compilation: agents are integrated into Flink streams and executed remotely or locally.
- Cross-language integration: Java and Python resources and execution environments communicate seamlessly.

## Project Structure
Flink Agents is organized into modules that separate API contracts, plan serialization, runtime execution, integrations, and Python bindings. The core API defines agents, events, memory, resources, and execution environments. The plan module serializes agent configurations and resource providers. The runtime bridges Java and Python execution.

```mermaid
graph TB
subgraph "API"
A["Agent.java"]
B["ReActAgent.java"]
C["Event.java"]
D["RunnerContext.java"]
E["MemoryObject.java"]
F["MemoryRef.java"]
G["MemoryUpdate.java"]
H["BaseLongTermMemory.java"]
I["BaseVectorStore.java"]
J["Resource.java"]
K["AgentsExecutionEnvironment.java"]
L["AgentBuilder.java"]
end
subgraph "PLAN"
P["ResourceProvider.java"]
end
subgraph "RUNTIME"
R1["LocalExecutionEnvironment"]
R2["RemoteExecutionEnvironment"]
end
A --> B
B --> C
C --> D
D --> E
E --> F
E --> G
D --> H
J --> I
K --> L
K --> R1
K --> R2
P --> J
```

**Diagram sources**
- [Agent.java](file://api/src/main/java/org/apache/flink/agents/api/agents/Agent.java#L34-L131)
- [ReActAgent.java](file://api/src/main/java/org/apache/flink/agents/api/agents/ReActAgent.java#L51-L183)
- [Event.java](file://api/src/main/java/org/apache/flink/agents/api/Event.java#L30-L90)
- [RunnerContext.java](file://api/src/main/java/org/apache/flink/agents/api/context/RunnerContext.java#L33-L138)
- [MemoryObject.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryObject.java#L29-L132)
- [MemoryRef.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryRef.java#L28-L88)
- [MemoryUpdate.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryUpdate.java#L30-L84)
- [BaseLongTermMemory.java](file://api/src/main/java/org/apache/flink/agents/api/memory/BaseLongTermMemory.java#L33-L134)
- [BaseVectorStore.java](file://api/src/main/java/org/apache/flink/agents/api/vectorstores/BaseVectorStore.java#L38-L174)
- [Resource.java](file://api/src/main/java/org/apache/flink/agents/api/resource/Resource.java#L30-L71)
- [AgentsExecutionEnvironment.java](file://api/src/main/java/org/apache/flink/agents/api/AgentsExecutionEnvironment.java#L43-L223)
- [AgentBuilder.java](file://api/src/main/java/org/apache/flink/agents/api/AgentBuilder.java#L35-L77)
- [ResourceProvider.java](file://plan/src/main/java/org/apache/flink/agents/plan/resourceprovider/ResourceProvider.java#L38-L76)

**Section sources**
- [Agent.java](file://api/src/main/java/org/apache/flink/agents/api/agents/Agent.java#L34-L131)
- [AgentsExecutionEnvironment.java](file://api/src/main/java/org/apache/flink/agents/api/AgentsExecutionEnvironment.java#L43-L223)

## Core Components
- Agent: Encapsulates actions and resources. Actions are methods annotated to listen to specific events and optionally carry per-action configuration.
- ReActAgent: A built-in agent that orchestrates reasoning and acting via chat models and structured outputs.
- Events: Typed event abstractions enabling decoupled communication between actions.
- RunnerContext: Provides access to memory, resources, configuration, metrics, and durable execution helpers.
- Memory: Sensory memory (temporary), short-term memory (structured state), and long-term memory (persistent via vector stores).
- Resources: Pluggable components (chat models, prompts, vector stores) with lifecycle and metrics.
- Execution Environment: Bridges local and Flink remote execution, exposing builder APIs to produce DataStream/Table outputs.

**Section sources**
- [Agent.java](file://api/src/main/java/org/apache/flink/agents/api/agents/Agent.java#L34-L131)
- [ReActAgent.java](file://api/src/main/java/org/apache/flink/agents/api/agents/ReActAgent.java#L51-L183)
- [Event.java](file://api/src/main/java/org/apache/flink/agents/api/Event.java#L30-L90)
- [RunnerContext.java](file://api/src/main/java/org/apache/flink/agents/api/context/RunnerContext.java#L33-L138)
- [MemoryObject.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryObject.java#L29-L132)
- [MemoryRef.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryRef.java#L28-L88)
- [MemoryUpdate.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryUpdate.java#L30-L84)
- [BaseLongTermMemory.java](file://api/src/main/java/org/apache/flink/agents/api/memory/BaseLongTermMemory.java#L33-L134)
- [BaseVectorStore.java](file://api/src/main/java/org/apache/flink/agents/api/vectorstores/BaseVectorStore.java#L38-L174)
- [Resource.java](file://api/src/main/java/org/apache/flink/agents/api/resource/Resource.java#L30-L71)
- [AgentsExecutionEnvironment.java](file://api/src/main/java/org/apache/flink/agents/api/AgentsExecutionEnvironment.java#L43-L223)
- [AgentBuilder.java](file://api/src/main/java/org/apache/flink/agents/api/AgentBuilder.java#L35-L77)

## Architecture Overview
Flink Agents adopts an agent-centric, event-driven design with a resource provider pattern and a layered memory system. Agents declare actions and resources; the runtime resolves resources, manages memory, and routes events. Execution environments integrate with Flink DataStream/Table APIs for scalable, stateful processing.

```mermaid
sequenceDiagram
participant User as "User Code"
participant Env as "AgentsExecutionEnvironment"
participant Builder as "AgentBuilder"
participant Agent as "Agent"
participant RC as "RunnerContext"
participant Mem as "Memory"
participant Res as "Resource"
User->>Env : "getExecutionEnvironment(...)"
User->>Env : "fromDataStream(...) / fromTable(...) / fromList(...)"
Env-->>Builder : "AgentBuilder"
User->>Builder : "apply(Agent)"
User->>Builder : "toDataStream() / toTable() / toList()"
Builder->>Agent : "configure actions/resources"
Agent->>RC : "initialize context"
RC->>Mem : "access sensory/short-term/long-term"
RC->>Res : "getResource(name, type)"
Agent-->>RC : "sendEvent(...)"
RC-->>Env : "emit outputs"
```

**Diagram sources**
- [AgentsExecutionEnvironment.java](file://api/src/main/java/org/apache/flink/agents/api/AgentsExecutionEnvironment.java#L68-L121)
- [AgentBuilder.java](file://api/src/main/java/org/apache/flink/agents/api/AgentBuilder.java#L35-L77)
- [Agent.java](file://api/src/main/java/org/apache/flink/agents/api/agents/Agent.java#L34-L131)
- [RunnerContext.java](file://api/src/main/java/org/apache/flink/agents/api/context/RunnerContext.java#L33-L138)
- [MemoryObject.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryObject.java#L29-L132)
- [Resource.java](file://api/src/main/java/org/apache/flink/agents/api/resource/Resource.java#L30-L71)

## Detailed Component Analysis

### Agent-Based Programming
Agents define behavior as actions that listen to specific event types. Actions can carry per-action configuration and interact with resources and memory via RunnerContext.

```mermaid
classDiagram
class Agent {
+addAction(events, method, config)
+addResource(name, type, instance)
+getActions()
+getResources()
}
class ReActAgent {
+startAction(event, ctx)
+stopAction(event, ctx)
}
class RunnerContext {
+sendEvent(event)
+getSensoryMemory()
+getShortTermMemory()
+getLongTermMemory()
+getResource(name, type)
+getConfig()
+getActionConfig()
+getActionConfigValue(key)
+durableExecute(callable)
+durableExecuteAsync(callable)
}
Agent <|-- ReActAgent
ReActAgent --> RunnerContext : "uses"
```

**Diagram sources**
- [Agent.java](file://api/src/main/java/org/apache/flink/agents/api/agents/Agent.java#L34-L131)
- [ReActAgent.java](file://api/src/main/java/org/apache/flink/agents/api/agents/ReActAgent.java#L51-L183)
- [RunnerContext.java](file://api/src/main/java/org/apache/flink/agents/api/context/RunnerContext.java#L33-L138)

**Section sources**
- [Agent.java](file://api/src/main/java/org/apache/flink/agents/api/agents/Agent.java#L34-L131)
- [ReActAgent.java](file://api/src/main/java/org/apache/flink/agents/api/agents/ReActAgent.java#L51-L183)
- [RunnerContext.java](file://api/src/main/java/org/apache/flink/agents/api/context/RunnerContext.java#L33-L138)

### Event-Driven Architecture
Events are typed abstractions carrying identifiers and attributes. Actions consume events and produce new events asynchronously. The system supports durable execution to ensure correctness across restarts.

```mermaid
flowchart TD
Start(["Event arrives"]) --> Dispatch["RunnerContext dispatches to matching actions"]
Dispatch --> Exec["Action executes with RunnerContext"]
Exec --> AccessMem["Access sensory/short-term/long-term memory"]
Exec --> UseRes["Use resources (chat model, vector store, etc.)"]
Exec --> Produce["Produce new events"]
Produce --> Emit["Emit outputs to downstream operators"]
Emit --> End(["Done"])
```

**Diagram sources**
- [Event.java](file://api/src/main/java/org/apache/flink/agents/api/Event.java#L30-L90)
- [RunnerContext.java](file://api/src/main/java/org/apache/flink/agents/api/context/RunnerContext.java#L33-L138)

**Section sources**
- [Event.java](file://api/src/main/java/org/apache/flink/agents/api/Event.java#L30-L90)
- [RunnerContext.java](file://api/src/main/java/org/apache/flink/agents/api/context/RunnerContext.java#L33-L138)

### Resource Provider Pattern
Resources are pluggable components (e.g., chat models, prompts, vector stores). Resource providers carry metadata to instantiate resources at runtime. The plan module serializes and deserializes providers for agent configuration.

```mermaid
classDiagram
class Resource {
+getResourceType()
+setMetricGroup(group)
+close()
}
class BaseVectorStore {
+getStoreKwargs()
+add(documents, collection, extraArgs)
+query(query)
+size(collection)
+get(ids, collection, extraArgs)
+delete(ids, collection, extraArgs)
}
class ResourceProvider {
+getName()
+getType()
+provide(getResource)
}
Resource <|-- BaseVectorStore
ResourceProvider --> Resource : "instantiates"
```

**Diagram sources**
- [Resource.java](file://api/src/main/java/org/apache/flink/agents/api/resource/Resource.java#L30-L71)
- [BaseVectorStore.java](file://api/src/main/java/org/apache/flink/agents/api/vectorstores/BaseVectorStore.java#L38-L174)
- [ResourceProvider.java](file://plan/src/main/java/org/apache/flink/agents/plan/resourceprovider/ResourceProvider.java#L38-L76)

**Section sources**
- [Resource.java](file://api/src/main/java/org/apache/flink/agents/api/resource/Resource.java#L30-L71)
- [BaseVectorStore.java](file://api/src/main/java/org/apache/flink/agents/api/vectorstores/BaseVectorStore.java#L38-L174)
- [ResourceProvider.java](file://plan/src/main/java/org/apache/flink/agents/plan/resourceprovider/ResourceProvider.java#L38-L76)

### Memory Hierarchy System
The memory system separates concerns:
- Sensory memory: temporary, cleared after each run.
- Short-term memory: structured state with path-based access, references, and updates.
- Long-term memory: persistent storage backed by vector stores, supporting semantic search and compaction.

```mermaid
classDiagram
class MemoryObject {
+get(path)
+get(ref)
+set(path, value)
+newObject(path, overwrite)
+isExist(path)
+getFieldNames()
+getFields()
+getValue()
+isNestedObject()
}
class MemoryRef {
+create(type, path)
+resolve(ctx)
+getPath()
}
class MemoryUpdate {
+getPath()
+getValue()
}
class BaseLongTermMemory {
+getOrCreateMemorySet(name, itemType, capacity, compactionConfig)
+getMemorySet(name)
+deleteMemorySet(name)
+size(memorySet)
+add(memorySet, items, ids, metadatas)
+get(memorySet, ids)
+delete(memorySet, ids)
+search(memorySet, query, limit, extraArgs)
}
MemoryObject --> MemoryRef : "produces"
MemoryObject --> MemoryUpdate : "applies"
RunnerContext --> MemoryObject : "provides"
RunnerContext --> BaseLongTermMemory : "provides"
```

**Diagram sources**
- [MemoryObject.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryObject.java#L29-L132)
- [MemoryRef.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryRef.java#L28-L88)
- [MemoryUpdate.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryUpdate.java#L30-L84)
- [BaseLongTermMemory.java](file://api/src/main/java/org/apache/flink/agents/api/memory/BaseLongTermMemory.java#L33-L134)
- [RunnerContext.java](file://api/src/main/java/org/apache/flink/agents/api/context/RunnerContext.java#L33-L138)

**Section sources**
- [MemoryObject.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryObject.java#L29-L132)
- [MemoryRef.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryRef.java#L28-L88)
- [MemoryUpdate.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryUpdate.java#L30-L84)
- [BaseLongTermMemory.java](file://api/src/main/java/org/apache/flink/agents/api/memory/BaseLongTermMemory.java#L33-L134)
- [RunnerContext.java](file://api/src/main/java/org/apache/flink/agents/api/context/RunnerContext.java#L33-L138)

### Agent Lifecycle, Execution Environment, and Plan Compilation
- Lifecycle: An agent is configured with actions and resources, then executed within an environment. Actions receive events, mutate memory, and emit outputs.
- Execution environment: Supports local and remote (Flink) modes. Remote mode integrates with DataStream/Table APIs and keying for stateful processing.
- Plan compilation: Resource providers and agent configuration are serialized/deserialized to form the execution plan.

```mermaid
sequenceDiagram
participant Dev as "Developer"
participant Env as "AgentsExecutionEnvironment"
participant Exec as "Execution Mode"
participant Plan as "Agent Plan"
participant Agent as "Agent"
participant RC as "RunnerContext"
Dev->>Env : "getExecutionEnvironment(env, tEnv)"
Env-->>Exec : "LocalExecutionEnvironment or RemoteExecutionEnvironment"
Dev->>Env : "fromDataStream/Table/List(...)"
Env-->>Plan : "build AgentBuilder"
Plan->>Agent : "apply(Agent)"
Agent->>RC : "initialize"
RC-->>Plan : "outputs emitted"
```

**Diagram sources**
- [AgentsExecutionEnvironment.java](file://api/src/main/java/org/apache/flink/agents/api/AgentsExecutionEnvironment.java#L68-L121)
- [AgentBuilder.java](file://api/src/main/java/org/apache/flink/agents/api/AgentBuilder.java#L35-L77)
- [Agent.java](file://api/src/main/java/org/apache/flink/agents/api/agents/Agent.java#L34-L131)
- [RunnerContext.java](file://api/src/main/java/org/apache/flink/agents/api/context/RunnerContext.java#L33-L138)

**Section sources**
- [AgentsExecutionEnvironment.java](file://api/src/main/java/org/apache/flink/agents/api/AgentsExecutionEnvironment.java#L68-L121)
- [AgentBuilder.java](file://api/src/main/java/org/apache/flink/agents/api/AgentBuilder.java#L35-L77)
- [Agent.java](file://api/src/main/java/org/apache/flink/agents/api/agents/Agent.java#L34-L131)
- [RunnerContext.java](file://api/src/main/java/org/apache/flink/agents/api/context/RunnerContext.java#L33-L138)

### Event Processing Model and Flink Streaming Interaction
Agents process events in a streaming context. Inputs can come from DataStream or Table APIs, optionally keyed for stateful operations. Outputs are emitted as DataStream or Table.

```mermaid
sequenceDiagram
participant DS as "Flink DataStream"
participant Env as "AgentsExecutionEnvironment"
participant Agent as "Agent"
participant RC as "RunnerContext"
participant Out as "Output DataStream/Table"
DS->>Env : "fromDataStream(input, keySelector)"
Env-->>Agent : "configure builder"
Agent->>RC : "process events"
RC-->>Out : "emit outputs"
```

**Diagram sources**
- [AgentsExecutionEnvironment.java](file://api/src/main/java/org/apache/flink/agents/api/AgentsExecutionEnvironment.java#L154-L189)
- [AgentBuilder.java](file://api/src/main/java/org/apache/flink/agents/api/AgentBuilder.java#L54-L75)
- [RunnerContext.java](file://api/src/main/java/org/apache/flink/agents/api/context/RunnerContext.java#L33-L138)

**Section sources**
- [AgentsExecutionEnvironment.java](file://api/src/main/java/org/apache/flink/agents/api/AgentsExecutionEnvironment.java#L154-L189)
- [AgentBuilder.java](file://api/src/main/java/org/apache/flink/agents/api/AgentBuilder.java#L54-L75)
- [RunnerContext.java](file://api/src/main/java/org/apache/flink/agents/api/context/RunnerContext.java#L33-L138)

### Cross-Language Execution Environments and Communication
- Java and Python resources are supported. Resource providers serialize metadata to enable cross-language instantiation.
- Vector stores and embedding models can be provided by Python implementations, bridged via the plan and runtime layers.

```mermaid
graph LR
Java["Java Agent"] -- "ResourceProvider metadata" --> Plan["Agent Plan"]
Plan -- "serialized descriptors" --> Python["Python Runtime"]
Python -- "resource instances" --> Java
```

**Diagram sources**
- [ResourceProvider.java](file://plan/src/main/java/org/apache/flink/agents/plan/resourceprovider/ResourceProvider.java#L38-L76)
- [BaseVectorStore.java](file://api/src/main/java/org/apache/flink/agents/api/vectorstores/BaseVectorStore.java#L38-L174)
- [Resource.java](file://api/src/main/java/org/apache/flink/agents/api/resource/Resource.java#L30-L71)

**Section sources**
- [ResourceProvider.java](file://plan/src/main/java/org/apache/flink/agents/plan/resourceprovider/ResourceProvider.java#L38-L76)
- [BaseVectorStore.java](file://api/src/main/java/org/apache/flink/agents/api/vectorstores/BaseVectorStore.java#L38-L174)
- [Resource.java](file://api/src/main/java/org/apache/flink/agents/api/resource/Resource.java#L30-L71)

## Dependency Analysis
The following diagram highlights key dependencies among core components:

```mermaid
graph TB
Agent["Agent.java"] --> RunnerContext["RunnerContext.java"]
ReActAgent["ReActAgent.java"] --> Agent
ReActAgent --> ChatRequestEvent["ChatRequestEvent.java"]
RunnerContext --> MemoryObject["MemoryObject.java"]
MemoryObject --> MemoryRef["MemoryRef.java"]
MemoryObject --> MemoryUpdate["MemoryUpdate.java"]
RunnerContext --> BaseLongTermMemory["BaseLongTermMemory.java"]
BaseLongTermMemory --> BaseVectorStore["BaseVectorStore.java"]
BaseVectorStore --> Resource["Resource.java"]
AgentsExecutionEnvironment["AgentsExecutionEnvironment.java"] --> AgentBuilder["AgentBuilder.java"]
ResourceProvider["ResourceProvider.java"] --> Resource
```

**Diagram sources**
- [Agent.java](file://api/src/main/java/org/apache/flink/agents/api/agents/Agent.java#L34-L131)
- [ReActAgent.java](file://api/src/main/java/org/apache/flink/agents/api/agents/ReActAgent.java#L51-L183)
- [ChatRequestEvent.java](file://api/src/main/java/org/apache/flink/agents/api/event/ChatRequestEvent.java#L29-L58)
- [RunnerContext.java](file://api/src/main/java/org/apache/flink/agents/api/context/RunnerContext.java#L33-L138)
- [MemoryObject.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryObject.java#L29-L132)
- [MemoryRef.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryRef.java#L28-L88)
- [MemoryUpdate.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryUpdate.java#L30-L84)
- [BaseLongTermMemory.java](file://api/src/main/java/org/apache/flink/agents/api/memory/BaseLongTermMemory.java#L33-L134)
- [BaseVectorStore.java](file://api/src/main/java/org/apache/flink/agents/api/vectorstores/BaseVectorStore.java#L38-L174)
- [Resource.java](file://api/src/main/java/org/apache/flink/agents/api/resource/Resource.java#L30-L71)
- [AgentsExecutionEnvironment.java](file://api/src/main/java/org/apache/flink/agents/api/AgentsExecutionEnvironment.java#L43-L223)
- [AgentBuilder.java](file://api/src/main/java/org/apache/flink/agents/api/AgentBuilder.java#L35-L77)
- [ResourceProvider.java](file://plan/src/main/java/org/apache/flink/agents/plan/resourceprovider/ResourceProvider.java#L38-L76)

**Section sources**
- [Agent.java](file://api/src/main/java/org/apache/flink/agents/api/agents/Agent.java#L34-L131)
- [ReActAgent.java](file://api/src/main/java/org/apache/flink/agents/api/agents/ReActAgent.java#L51-L183)
- [RunnerContext.java](file://api/src/main/java/org/apache/flink/agents/api/context/RunnerContext.java#L33-L138)
- [MemoryObject.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryObject.java#L29-L132)
- [MemoryRef.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryRef.java#L28-L88)
- [MemoryUpdate.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryUpdate.java#L30-L84)
- [BaseLongTermMemory.java](file://api/src/main/java/org/apache/flink/agents/api/memory/BaseLongTermMemory.java#L33-L134)
- [BaseVectorStore.java](file://api/src/main/java/org/apache/flink/agents/api/vectorstores/BaseVectorStore.java#L38-L174)
- [Resource.java](file://api/src/main/java/org/apache/flink/agents/api/resource/Resource.java#L30-L71)
- [AgentsExecutionEnvironment.java](file://api/src/main/java/org/apache/flink/agents/api/AgentsExecutionEnvironment.java#L43-L223)
- [AgentBuilder.java](file://api/src/main/java/org/apache/flink/agents/api/AgentBuilder.java#L35-L77)
- [ResourceProvider.java](file://plan/src/main/java/org/apache/flink/agents/plan/resourceprovider/ResourceProvider.java#L38-L76)

## Performance Considerations
- Use keying in DataStream/Table inputs to enable stateful operations and efficient checkpointing.
- Prefer compact memory sets and controlled compaction policies for long-term memory to balance retrieval quality and storage cost.
- Minimize large object transfers by storing only references (MemoryRef) in actions and resolving lazily.
- Batch embedding and vector store operations to reduce overhead.
- Monitor resource metrics via the bound metric groups for latency and throughput tuning.

## Troubleshooting Guide
- Resource conflicts: Adding a resource with an existing name/type will raise an error. Ensure unique names per type.
- Unsupported resource types: Only serializable resources or resource descriptors are accepted.
- Unknown memory type: Resolving a MemoryRef with an unsupported type raises an error.
- Action configuration: Use getActionConfig and getActionConfigValue to access per-action configuration safely.
- Durable execution: Avoid memory and event operations inside durable callables; they run synchronously and are cached on recovery.

**Section sources**
- [Agent.java](file://api/src/main/java/org/apache/flink/agents/api/agents/Agent.java#L97-L111)
- [MemoryRef.java](file://api/src/main/java/org/apache/flink/agents/api/context/MemoryRef.java#L56-L64)
- [RunnerContext.java](file://api/src/main/java/org/apache/flink/agents/api/context/RunnerContext.java#L109-L133)

## Conclusion
Flink Agents provides a cohesive framework for building intelligent, event-driven agents that operate over streaming data. Its agent-based programming model, event-driven architecture, and resource provider pattern enable flexible composition of AI capabilities. The layered memory system and execution environment integrate seamlessly with Flink, while cross-language support broadens the ecosystem of available resources.