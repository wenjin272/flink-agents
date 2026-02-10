# Unit Testing

<cite>
**Referenced Files in This Document**
- [ReActAgentTest.java](file://api/src/test/java/org/apache/flink/agents/api/agents/ReActAgentTest.java)
- [MemorySetTest.java](file://api/src/test/java/org/apache/flink/agents/api/memory/MemorySetTest.java)
- [EmbeddingModelUtilsTest.java](file://api/src/test/java/org/apache/flink/agents/api/embedding/model/EmbeddingModelUtilsTest.java)
- [ResourceDescriptorTest.java](file://api/src/test/java/org/apache/flink/agents/api/resource/ResourceDescriptorTest.java)
- [PromptTest.java](file://api/src/test/java/org/apache/flink/agents/api/prompt/PromptTest.java)
- [ChatMessageTest.java](file://api/src/test/java/org/apache/flink/agents/api/chat/messages/ChatMessageTest.java)
- [BaseChatModelTest.java](file://api/src/test/java/org/apache/flink/agents/api/chat/model/BaseChatModelTest.java)
- [PythonCollectionManageableVectorStoreTest.java](file://api/src/test/java/org/apache/flink/agents/api/vectorstores/python/PythonCollectionManageableVectorStoreTest.java)
- [AgentPlanTest.java](file://plan/src/test/java/org/apache/flink/agents/plan/AgentPlanTest.java)
- [ut.sh](file://tools/ut.sh)
- [pom.xml](file://pom.xml)
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
This document provides a comprehensive guide to unit testing strategies for Flink Agents. It focuses on testing patterns for core components such as agents, chat models, memory systems, and resource management. It explains how to write effective unit tests for agent behavior, resource provider implementations, and utility classes. It also covers mocking strategies for external dependencies, test data management, assertion patterns, and test isolation techniques. Guidance is grounded in the existing test suites present in the repository.

## Project Structure
The repository organizes unit tests primarily under the api module’s test tree and plan module’s test tree. Representative tests include:
- Agents: ReActAgentTest
- Memory: MemorySetTest
- Utilities: EmbeddingModelUtilsTest, PromptTest
- Resources: ResourceDescriptorTest
- Chat model: ChatMessageTest, BaseChatModelTest
- Vector stores (Python): PythonCollectionManageableVectorStoreTest
- Plan and resource providers: AgentPlanTest

```mermaid
graph TB
subgraph "API Tests"
A1["ReActAgentTest"]
A2["MemorySetTest"]
A3["EmbeddingModelUtilsTest"]
A4["ResourceDescriptorTest"]
A5["PromptTest"]
A6["ChatMessageTest"]
A7["BaseChatModelTest"]
A8["PythonCollectionManageableVectorStoreTest"]
end
subgraph "Plan Tests"
P1["AgentPlanTest"]
end
subgraph "Tools"
T1["ut.sh"]
T2["pom.xml"]
end
A1 --> T1
A2 --> T1
A3 --> T1
A4 --> T1
A5 --> T1
A6 --> T1
A7 --> T1
A8 --> T1
P1 --> T1
T2 --> T1
```

**Diagram sources**
- [ReActAgentTest.java](file://api/src/test/java/org/apache/flink/agents/api/agents/ReActAgentTest.java#L1-L45)
- [MemorySetTest.java](file://api/src/test/java/org/apache/flink/agents/api/memory/MemorySetTest.java#L1-L43)
- [EmbeddingModelUtilsTest.java](file://api/src/test/java/org/apache/flink/agents/api/embedding/model/EmbeddingModelUtilsTest.java#L1-L123)
- [ResourceDescriptorTest.java](file://api/src/test/java/org/apache/flink/agents/api/resource/ResourceDescriptorTest.java#L1-L55)
- [PromptTest.java](file://api/src/test/java/org/apache/flink/agents/api/prompt/PromptTest.java#L1-L261)
- [ChatMessageTest.java](file://api/src/test/java/org/apache/flink/agents/api/chat/messages/ChatMessageTest.java#L1-L153)
- [BaseChatModelTest.java](file://api/src/test/java/org/apache/flink/agents/api/chat/model/BaseChatModelTest.java#L1-L256)
- [PythonCollectionManageableVectorStoreTest.java](file://api/src/test/java/org/apache/flink/agents/api/vectorstores/python/PythonCollectionManageableVectorStoreTest.java#L1-L355)
- [AgentPlanTest.java](file://plan/src/test/java/org/apache/flink/agents/plan/AgentPlanTest.java#L1-L482)
- [ut.sh](file://tools/ut.sh#L1-L328)
- [pom.xml](file://pom.xml#L69-L107)

**Section sources**
- [ReActAgentTest.java](file://api/src/test/java/org/apache/flink/agents/api/agents/ReActAgentTest.java#L1-L45)
- [MemorySetTest.java](file://api/src/test/java/org/apache/flink/agents/api/memory/MemorySetTest.java#L1-L43)
- [EmbeddingModelUtilsTest.java](file://api/src/test/java/org/apache/flink/agents/api/embedding/model/EmbeddingModelUtilsTest.java#L1-L123)
- [ResourceDescriptorTest.java](file://api/src/test/java/org/apache/flink/agents/api/resource/ResourceDescriptorTest.java#L1-L55)
- [PromptTest.java](file://api/src/test/java/org/apache/flink/agents/api/prompt/PromptTest.java#L1-L261)
- [ChatMessageTest.java](file://api/src/test/java/org/apache/flink/agents/api/chat/messages/ChatMessageTest.java#L1-L153)
- [BaseChatModelTest.java](file://api/src/test/java/org/apache/flink/agents/api/chat/model/BaseChatModelTest.java#L1-L256)
- [PythonCollectionManageableVectorStoreTest.java](file://api/src/test/java/org/apache/flink/agents/api/vectorstores/python/PythonCollectionManageableVectorStoreTest.java#L1-L355)
- [AgentPlanTest.java](file://plan/src/test/java/org/apache/flink/agents/plan/AgentPlanTest.java#L1-L482)
- [ut.sh](file://tools/ut.sh#L1-L328)
- [pom.xml](file://pom.xml#L69-L107)

## Core Components
This section outlines testing patterns for the major functional areas.

- Agents
  - Serialization and schema correctness: OutputSchema serialization test validates round-trip JSON compatibility for Row-type schemas used by agents.
  - Action discovery and plan construction: AgentPlanTest verifies that annotated actions are discovered, mapped by event types, and that resource providers are initialized correctly.

- Chat Models and Messages
  - Message semantics: ChatMessageTest validates roles, content, tool calls, and equality.
  - Prompt templating and formatting: PromptTest validates text-to-string and text-to-messages formatting, variable substitution, and serialization/deserialization.
  - Model behavior: BaseChatModelTest validates resource type, response generation, conversation handling, and robustness against edge cases.

- Memory Systems
  - MemorySet serialization: MemorySetTest validates JSON serialization/deserialization of memory sets including compaction configuration and chat message types.

- Resource Management
  - ResourceDescriptor serialization: ResourceDescriptorTest validates serializability of descriptors with diverse initial arguments and input events.
  - Resource providers and caching: AgentPlanTest demonstrates extraction of resource providers, caching behavior, and retrieval with proper exceptions when adapters are missing.

- Utilities
  - Embedding arrays: EmbeddingModelUtilsTest validates conversion of numeric lists to float arrays, including empty lists, single-element lists, mixed numeric types, and error handling for non-numeric entries.

- Vector Stores (Python)
  - Python-backed vector store operations: PythonCollectionManageableVectorStoreTest validates collection lifecycle (get/create/delete), document operations (add/get/delete), and size queries, using mocks for PythonResourceAdapter and Python objects.

**Section sources**
- [ReActAgentTest.java](file://api/src/test/java/org/apache/flink/agents/api/agents/ReActAgentTest.java#L30-L43)
- [AgentPlanTest.java](file://plan/src/test/java/org/apache/flink/agents/plan/AgentPlanTest.java#L247-L320)
- [ChatMessageTest.java](file://api/src/test/java/org/apache/flink/agents/api/chat/messages/ChatMessageTest.java#L47-L151)
- [PromptTest.java](file://api/src/test/java/org/apache/flink/agents/api/prompt/PromptTest.java#L78-L259)
- [BaseChatModelTest.java](file://api/src/test/java/org/apache/flink/agents/api/chat/model/BaseChatModelTest.java#L107-L254)
- [MemorySetTest.java](file://api/src/test/java/org/apache/flink/agents/api/memory/MemorySetTest.java#L28-L41)
- [ResourceDescriptorTest.java](file://api/src/test/java/org/apache/flink/agents/api/resource/ResourceDescriptorTest.java#L32-L53)
- [EmbeddingModelUtilsTest.java](file://api/src/test/java/org/apache/flink/agents/api/embedding/model/EmbeddingModelUtilsTest.java#L35-L121)
- [PythonCollectionManageableVectorStoreTest.java](file://api/src/test/java/org/apache/flink/agents/api/vectorstores/python/PythonCollectionManageableVectorStoreTest.java#L76-L354)

## Architecture Overview
The unit testing architecture leverages JUnit 5, AssertJ, and Mockito. The test harness supports both Java and Python test suites, with Maven coordinates and a dedicated script to orchestrate builds and test runs.

```mermaid
graph TB
JUnit["JUnit 5"]
AssertJ["AssertJ"]
Mockito["Mockito"]
ByteBuddy["Byte Buddy"]
JUnit --> Tests["Unit Tests"]
AssertJ --> Tests
Mockito --> Tests
ByteBuddy --> Tests
Tests --> API["API Module Tests"]
Tests --> PLAN["Plan Module Tests"]
Tests --> PYTHON["Python Tests"]
Tools["ut.sh"] --> Tests
POM["pom.xml"] --> JUnit
POM --> AssertJ
POM --> Mockito
POM --> ByteBuddy
```

**Diagram sources**
- [pom.xml](file://pom.xml#L69-L107)
- [ut.sh](file://tools/ut.sh#L1-L328)

**Section sources**
- [pom.xml](file://pom.xml#L69-L107)
- [ut.sh](file://tools/ut.sh#L1-L328)

## Detailed Component Analysis

### Agent Behavior and Plan Construction
This test suite focuses on verifying agent action discovery, event mapping, and resource provider initialization.

```mermaid
sequenceDiagram
participant T as "AgentPlanTest"
participant AP as "AgentPlan"
participant AG as "TestAgent/TestAgentWithResources"
participant RP as "ResourceProviders"
T->>AG : "Instantiate agent with annotated methods"
T->>AP : "new AgentPlan(agent)"
AP->>AP : "scan for @Action methods"
AP-->>T : "actions map and actionsByEvent map"
T->>AP : "getResource(name, type)"
AP->>RP : "lookup provider"
RP-->>AP : "resource instance"
AP-->>T : "cached resource"
```

**Diagram sources**
- [AgentPlanTest.java](file://plan/src/test/java/org/apache/flink/agents/plan/AgentPlanTest.java#L247-L480)

Key testing patterns:
- Annotation scanning: Verifies that only annotated methods are included in the plan.
- Event mapping: Ensures actions are indexed per listening event type.
- Resource provider extraction: Confirms providers are created for tools and chat models, including JavaSerializableResourceProvider and PythonResourceProvider.
- Adapter integration: Validates behavior when a PythonResourceAdapter is configured and when it is missing.

Assertions and patterns:
- Size checks on collections of actions and event mappings.
- Parameter type verification for JavaFunction executors.
- Exception assertions for missing resources and missing adapters.

**Section sources**
- [AgentPlanTest.java](file://plan/src/test/java/org/apache/flink/agents/plan/AgentPlanTest.java#L247-L480)

### Chat Models and Prompts
Testing chat models and prompts emphasizes correctness of message formatting, prompt templating, and response generation.

```mermaid
flowchart TD
Start(["Test Entry"]) --> CreatePrompt["Create Prompt (text or messages)"]
CreatePrompt --> FormatVars["Format with variables"]
FormatVars --> BuildMessages["Build ChatMessage list"]
BuildMessages --> CallChat["Call chat(model, messages)"]
CallChat --> ValidateRole["Validate role is ASSISTANT"]
ValidateRole --> ValidateContent["Validate content presence and structure"]
ValidateContent --> End(["Test Exit"])
```

**Diagram sources**
- [BaseChatModelTest.java](file://api/src/test/java/org/apache/flink/agents/api/chat/model/BaseChatModelTest.java#L113-L233)
- [PromptTest.java](file://api/src/test/java/org/apache/flink/agents/api/prompt/PromptTest.java#L78-L133)

Patterns:
- Prompt formatting: Text-to-string and text-to-messages conversions with variable substitution.
- Message roles and equality: Validation of role constants and equality semantics.
- Model behavior: Echo-style response generation with configurable prefixes and robustness against empty or multi-user-message inputs.

**Section sources**
- [BaseChatModelTest.java](file://api/src/test/java/org/apache/flink/agents/api/chat/model/BaseChatModelTest.java#L107-L254)
- [ChatMessageTest.java](file://api/src/test/java/org/apache/flink/agents/api/chat/messages/ChatMessageTest.java#L47-L151)
- [PromptTest.java](file://api/src/test/java/org/apache/flink/agents/api/prompt/PromptTest.java#L78-L259)

### Memory Operations
MemorySet tests focus on serialization and equality semantics for memory sets.

```mermaid
flowchart TD
A["Create MemorySet with type info and compaction config"] --> B["Serialize to JSON"]
B --> C["Deserialize JSON to MemorySet"]
C --> D["Assert equality with original"]
D --> E["Validate compaction config and element type"]
```

**Diagram sources**
- [MemorySetTest.java](file://api/src/test/java/org/apache/flink/agents/api/memory/MemorySetTest.java#L28-L41)

**Section sources**
- [MemorySetTest.java](file://api/src/test/java/org/apache/flink/agents/api/memory/MemorySetTest.java#L28-L41)

### Resource Provider Implementations
ResourceDescriptor and AgentPlan tests demonstrate serialization and provider extraction.

```mermaid
sequenceDiagram
participant T as "ResourceDescriptorTest"
participant RD as "ResourceDescriptor"
participant JSON as "ObjectMapper"
participant AP as "AgentPlan"
participant RP as "ResourceProvider"
T->>RD : "Build with diverse initial args"
T->>JSON : "serialize"
JSON-->>T : "JSON string"
T->>JSON : "deserialize"
JSON-->>T : "ResourceDescriptor"
T->>AP : "new AgentPlan(agentWithResources)"
AP->>RP : "extract providers by type and name"
RP-->>AP : "instances"
```

**Diagram sources**
- [ResourceDescriptorTest.java](file://api/src/test/java/org/apache/flink/agents/api/resource/ResourceDescriptorTest.java#L32-L53)
- [AgentPlanTest.java](file://plan/src/test/java/org/apache/flink/agents/plan/AgentPlanTest.java#L388-L480)

**Section sources**
- [ResourceDescriptorTest.java](file://api/src/test/java/org/apache/flink/agents/api/resource/ResourceDescriptorTest.java#L32-L53)
- [AgentPlanTest.java](file://plan/src/test/java/org/apache/flink/agents/plan/AgentPlanTest.java#L388-L480)

### Utility Classes
EmbeddingModelUtils tests validate numeric conversion and error handling.

```mermaid
flowchart TD
Start(["Input List"]) --> CheckType{"List of Doubles?<br/>or Floats?<br/>or Mixed Numbers?"}
CheckType --> |Yes| Convert["Convert to float[]"]
CheckType --> |No| Throw["Throw IllegalArgumentException"]
Convert --> AssertLen["Assert length and values"]
Throw --> AssertMsg["Assert exception message"]
AssertLen --> End(["Test Exit"])
AssertMsg --> End
```

**Diagram sources**
- [EmbeddingModelUtilsTest.java](file://api/src/test/java/org/apache/flink/agents/api/embedding/model/EmbeddingModelUtilsTest.java#L35-L121)

**Section sources**
- [EmbeddingModelUtilsTest.java](file://api/src/test/java/org/apache/flink/agents/api/embedding/model/EmbeddingModelUtilsTest.java#L35-L121)

### Vector Store Operations (Python)
Python-backed vector store tests validate collection and document operations using mocks.

```mermaid
sequenceDiagram
participant T as "PythonCollectionManageableVectorStoreTest"
participant VS as "PythonCollectionManageableVectorStore"
participant PA as "PythonResourceAdapter"
participant PO as "PyObject"
T->>VS : "new PythonCollectionManageableVectorStore(adapter, ...)"
T->>VS : "get_or_create_collection(name, metadata?)"
VS->>PA : "callMethod(vectorStore, 'get_or_create_collection', kwargs)"
PA-->>VS : "PyObject collection"
VS->>PA : "fromPythonCollection(PyObject)"
PA-->>VS : "Collection"
VS-->>T : "Collection"
```

**Diagram sources**
- [PythonCollectionManageableVectorStoreTest.java](file://api/src/test/java/org/apache/flink/agents/api/vectorstores/python/PythonCollectionManageableVectorStoreTest.java#L93-L127)

**Section sources**
- [PythonCollectionManageableVectorStoreTest.java](file://api/src/test/java/org/apache/flink/agents/api/vectorstores/python/PythonCollectionManageableVectorStoreTest.java#L93-L127)

## Dependency Analysis
The test dependencies are declared in the project’s dependency management and dependencies sections. The primary libraries used in tests are:
- JUnit Jupiter for test framework
- AssertJ for fluent assertions
- Mockito for mocking
- Byte Buddy for advanced mocking scenarios

```mermaid
graph TB
P["pom.xml"]
J["JUnit Jupiter"]
AJ["AssertJ"]
MK["Mockito"]
BB["Byte Buddy"]
P --> J
P --> AJ
P --> MK
P --> BB
```

**Diagram sources**
- [pom.xml](file://pom.xml#L69-L107)

**Section sources**
- [pom.xml](file://pom.xml#L69-L107)

## Performance Considerations
- Prefer lightweight assertions and deterministic inputs to keep tests fast and reliable.
- Use mocks judiciously to avoid heavyweight external dependencies during unit tests.
- Keep test data minimal and focused to reduce serialization overhead (e.g., small prompts, compact memory sets).
- Avoid unnecessary object creation inside test loops; reuse instances where safe.

## Troubleshooting Guide
Common issues and resolutions:
- Serialization failures
  - Symptom: JSON serialization/deserialization tests fail.
  - Resolution: Ensure all relevant fields are serializable and that constructors support default instantiation. Confirm ObjectMapper usage and field visibility.
  - References:
    - [ReActAgentTest.java](file://api/src/test/java/org/apache/flink/agents/api/agents/ReActAgentTest.java#L30-L43)
    - [MemorySetTest.java](file://api/src/test/java/org/apache/flink/agents/api/memory/MemorySetTest.java#L28-L41)
    - [PromptTest.java](file://api/src/test/java/org/apache/flink/agents/api/prompt/PromptTest.java#L240-L259)
    - [ResourceDescriptorTest.java](file://api/src/test/java/org/apache/flink/agents/api/resource/ResourceDescriptorTest.java#L32-L53)

- Mock misuse
  - Symptom: Mockito argument matchers fail or invocations are not verified.
  - Resolution: Use ArgumentMatchers consistently, verify interactions after asserting outcomes, and ensure mocks are initialized via @BeforeEach or openMocks.
  - References:
    - [PythonCollectionManageableVectorStoreTest.java](file://api/src/test/java/org/apache/flink/agents/api/vectorstores/python/PythonCollectionManageableVectorStoreTest.java#L61-L74)

- Missing adapters for Python resources
  - Symptom: IllegalStateException when retrieving Python resources without a configured adapter.
  - Resolution: Configure a PythonResourceAdapter before retrieving Python resources.
  - References:
    - [AgentPlanTest.java](file://plan/src/test/java/org/apache/flink/agents/plan/AgentPlanTest.java#L466-L476)

- Assertion mismatches
  - Symptom: Fluent assertions fail unexpectedly.
  - Resolution: Use AssertJ assertions for richer diagnostics and clearer failure messages; prefer assertThat(...) over classic assertions for complex objects.
  - References:
    - [AgentPlanTest.java](file://plan/src/test/java/org/apache/flink/agents/plan/AgentPlanTest.java#L255-L304)

## Conclusion
The Flink Agents repository provides a solid foundation for unit testing across agents, chat models, memory systems, resources, utilities, and vector stores. The tests demonstrate effective patterns for serialization validation, annotation-driven action discovery, resource provider extraction, and Python integration via mocks. By following the outlined strategies—serialization-first validations, fluent assertions, targeted mocking, and deterministic test data—you can maintain high confidence in core components while keeping tests fast and maintainable.