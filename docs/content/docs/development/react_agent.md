---
title: ReAct Agent
weight: 1
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

## Overview

ReAct Agent is a general paradigm that combines reasoning and action capabilities to solve complex tasks. Leveraging this paradigm, the user only needs to specify the goal with prompt and provide available tools, and the LLM will decide how to achieve the goal and take actions autonomously

## ReAct Agent Example

```python
review_analysis_react_agent = ReActAgent(
    chat_model=chat_model,
    prompt=review_analysis_react_prompt,
    output_schema=ProductReviewAnalysisRes,
)
```
## Initialize Arguments
### Chat Model
User should specify the chat model used in the ReAct Agent.

We use `ResourceDescriptor` to describe the chat model, includes chat model type and chat model arguments. See [Chat Model]({{< ref "docs/development/chat_with_llm#chatmodel" >}}) for more details.
```python
chat_model = ResourceDescriptor(
    clazz=OllamaChatModelSetup,
    connection="ollama_server",
    model="qwen3:8b",
    tools=["notify_shipping_manager"],
)
```

### Prompt
User can provide prompt to instruct agent. 

Here we create a prompt contains two messages. The first message tells the agent what to do, and gives the input and output example. The second message tells how to convert input element to text string.
```python
review_analysis_system_prompt_str = """
    Analyze the user review and product information to determine a
    satisfaction score (1-5) and potential reasons for dissatisfaction.

    Example input format:
    {{
        "id": "12345",
        "review": "The headphones broke after one week of use. Very poor quality."
    }}

    Ensure your response can be parsed by Python JSON, using this format as an example:
    {{
     "id": "12345",
     "score": 1,
     "reasons": [
       "poor quality"
       ]
    }}

    Please note that if a product review includes dissatisfaction with the shipping process,
    you should first notify the shipping manager using the appropriate tools. After executing
    the tools, strictly follow the example above to provide your score and reason — there is
    no need to disclose whether the tool was used.
    """
    
# Prompt for review analysis react agent.
review_analysis_react_prompt = Prompt.from_messages(
    messages=[
        ChatMessage(
            role=MessageRole.SYSTEM,
            content=review_analysis_system_prompt_str,
        ),
        # For react agent, if the input element is not primitive types,
        # framework will deserialize input element to dict and fill the prompt.
        # Note, the input element should be primitive types, BaseModel or Row.
        ChatMessage(
            role=MessageRole.USER,
            content="""
            "id": {id},
            "review": {review}
            """,
        ),
    ],
) 

```
If the input element is primitive types, like `int`, `str` and so on, the second message should be
```python
ChatMessage(
    role=MessageRole.USER,
    content="{input}"
)
```

See [Prompt]({{< ref "docs/development/chat_with_llm#prompt" >}}) for more details.

### Output Schema
User can set output schema to configure the ReAct Agent output type. If output schema is set, the ReAct Agent will deserialize the llm response to expected type. 

The output schema should be `BaseModel` or `RowTypeInfo`.
```python
class ProductReviewAnalysisRes(BaseModel):
    id: str
    score: int
    reasons: list[str]
```
