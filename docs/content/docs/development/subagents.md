---
title: Sub-agents
weight: 13
type: docs
---
<!--
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
-->

A sub-agent handles a task delegated by a parent agent. An internal sub-agent runs
an agent workflow in the same job. An external sub-agent calls an agent service
through a `SubagentSetup` implementation.

## Declare an internal sub-agent

Use `InternalSubagentResourceDescriptorBuilder` to attach a description and input
schema to a child agent. The builder returns a normal resource descriptor for `addResource`
or `add_resource`.

```java
import org.apache.flink.agents.api.resource.ResourceType;
import org.apache.flink.agents.api.subagent.InternalSubagentResourceDescriptorBuilder;

parent.addResource(
    "reviewer",
    ResourceType.AGENT,
    new InternalSubagentResourceDescriptorBuilder()
        .agent(new ReviewAgent())
        .description("Review code for correctness and potential defects")
        .inputType(ReviewRequest.class)
        .build());
```

```python
from pydantic import BaseModel

from flink_agents.api.resource import ResourceType
from flink_agents.api.subagent import InternalSubagentResourceDescriptorBuilder

class ReviewRequest(BaseModel):
    code: str

parent.add_resource(
    "reviewer",
    ResourceType.AGENT,
    InternalSubagentResourceDescriptorBuilder()
        .agent(ReviewAgent())
        .description("Review code for correctness and potential defects")
        .input_type(ReviewRequest)
        .build(),
)
```

`ReviewAgent` is your child workflow; the Java `ReviewRequest` is a data class
with fields describing its input. Alternatively, pass a JSON schema string to
`inputSchema(...)` in Java or `input_schema(...)` in Python. Choose either an
input type or an explicit schema. The schema describes the submitted arguments,
which the child receives as its input event payload; it does not convert that
payload into an instance of the input type.

When a chat model is configured with `subagents=["reviewer"]`, the description
helps it choose when to delegate, and the schema tells it which arguments to
send. A schema is required for model-selected calls. A missing description uses
a generic delegation description.

For calls made explicitly by an action, the existing shorthand remains available:

```java
parent.addResource("reviewer", ResourceType.AGENT, new ReviewAgent());
```

```python
parent.add_resource("reviewer", ResourceType.AGENT, ReviewAgent())
```

This shorthand does not declare an input schema. Use the builder when exposing
the child to a model. Recursive registration, such as a child registering its
parent, is rejected when the plan is built.

## Declare an external sub-agent

Implement `SubagentSetup` (or the appropriate runtime base class) and register a
resource descriptor naming that implementation. Do not register a setup instance.

```java
parent.addResource(
    "remote_reviewer",
    ResourceType.AGENT,
    ResourceDescriptor.Builder.newBuilder(RemoteReviewSetup.class.getName())
        .addInitialArgument("endpoint", "https://example.com/review")
        .addInitialArgument("description", "Review code using the remote service")
        .addInitialArgument("input_schema", inputSchema)
        .build());
```

The Java setup exposes a public `(ResourceDescriptor, ResourceContext)`
constructor and implements the sub-agent invocation contract. `endpoint` above
is configuration read by the example implementation, not a built-in transport.

```python
parent.add_resource(
    "remote_reviewer",
    ResourceType.AGENT,
    ResourceDescriptor(
        clazz="my_app.agents.RemoteReviewSetup",
        endpoint="https://example.com/review",
        description="Review code using the remote service",
        input_schema=input_schema,
    ),
)
```

The Python setup declares these configuration fields and implements the
invocation contract. Both languages construct the setup at runtime from the
descriptor. Existing code that passes a setup instance to `addResource` or
`add_resource` must instead pass a descriptor with the same configuration.
