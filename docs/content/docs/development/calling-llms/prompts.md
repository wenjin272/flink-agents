---
title: "Prompts"
weight: 2
type: docs
aliases:
  - /docs/development/prompts/
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

# Prompts

## Overview

Prompts are templates that define how your agents communicate with Large Language Models (LLMs). They provide structured instructions, context, and formatting guidelines that shape the LLM's responses. In Flink Agents, prompts are first-class resources that can be defined, reused, and referenced across agents and chat models.

To reuse a prompt by name, register it as a `PROMPT` Resource and reference that
name from a chat model setup's `prompt` field. See
[Registering Resources]({{< ref "docs/development/create-agent/resources#registering-resources" >}})
for registration methods and scopes. This page describes how to construct and
format the prompt itself.

## Prompt Types

Flink Agents supports two types of prompts:

### Local Prompt

Local prompts are templates defined directly in your code. They support variable substitution using `{variable_name}` syntax and can be created from either text strings or message sequences.

### MCP Prompt

MCP (Model Context Protocol) prompts are managed by external MCP servers. They enable dynamic prompt retrieval, centralized prompt management, and integration with external prompt repositories.

See [MCP]({{< ref "docs/development/calling-llms/mcp" >}}) for details.
## Local Prompt

### Creating from Text

The simplest way to create a prompt is from a text string using `Prompt.from_text()`:

{{< tabs "Creating from Text" >}}

{{< tab "Python" >}}
```python
product_suggestion_prompt_str = """
Based on the rating distribution and user dissatisfaction reasons, generate three actionable suggestions for product improvement.

Input format:
{
    "id": "1",
    "score_histogram": ["10%", "20%", "10%", "15%", "45%"],
    "unsatisfied_reasons": ["reason1", "reason2", "reason3"]
}

Ensure that your response can be parsed by Python json, use the following format as an example:
{
    "suggestion_list": [
        "suggestion1",
        "suggestion2",
        "suggestion3"
    ]
}

input:
{input}
"""

product_suggestion_prompt = Prompt.from_text(product_suggestion_prompt_str)
```
{{< /tab >}}

{{< tab "Java" >}}
```java
// Prompt for product suggestion agent
String PRODUCT_SUGGESTION_PROMPT_STR =
        "Based on the rating distribution and user dissatisfaction reasons, generate three actionable suggestions for product improvement.\n\n"
                + "Input format:\n"
                + "{\n"
                + "    \"id\": \"1\",\n"
                + "    \"score_histogram\": [\"10%\", \"20%\", \"10%\", \"15%\", \"45%\"],\n"
                + "    \"unsatisfied_reasons\": [\"reason1\", \"reason2\", \"reason3\"]\n"
                + "}\n\n"
                + "Ensure that your response can be parsed by Java JSON, use the following format as an example:\n"
                + "{\n"
                + "    \"suggestion_list\": [\n"
                + "        \"suggestion1\",\n"
                + "        \"suggestion2\",\n"
                + "        \"suggestion3\"\n"
                + "    ]\n"
                + "}\n\n"
                + "input:\n"
                + "{input}";


Prompt productSuggestionPrompt = Prompt.fromText(PRODUCT_SUGGESTION_PROMPT_STR);
```
{{< /tab >}}

{{< /tabs >}}

**Key points:**
- Use `{variable_name}` for template variables that will be substituted at runtime
- `{variable_name}` is the only substitution syntax. Any `{` or `}` that is not part of a known placeholder passes through verbatim, so JSON examples inside a prompt should use single braces. There is no `{{` / `}}` escape — doubled braces are emitted to the LLM as literal `{{` and `}}`, which the model may copy into its reply and break downstream `json.loads`

### Creating from Messages

For more control, create prompts from a sequence of `ChatMessage` objects using `Prompt.from_messages()`:

{{< tabs "Creating from Messages" >}}

{{< tab "Python" >}}
```python
review_analysis_prompt = Prompt.from_messages(
    messages=[
        ChatMessage.system(
            """
            Analyze the user review and product information to determine a
            satisfaction score (1-5) and potential reasons for dissatisfaction.

            Example input format:
            {
                "id": "12345",
                "review": "The headphones broke after one week of use."
            }

            Ensure your response can be parsed by Python JSON:
            {
                "id": "12345",
                "score": 1,
                "reasons": ["poor quality"]
            }
            """
        ),
        ChatMessage.user(
            """
            "input":
            {input}
            """
        ),
    ],
)
```
{{< /tab >}}

{{< tab "Java" >}}
```java
Prompt reviewAnalysisPrompt =
        Prompt.fromMessages(
                Arrays.asList(
                        new ChatMessage(
                                MessageRole.SYSTEM,
                                "Analyze the user review and product information to determine a "
                                        + "satisfaction score (1-5) and potential reasons for dissatisfaction.\n\n"
                                        + "Example input format:\n"
                                        + "{\n"
                                        + "    \"id\": \"12345\",\n"
                                        + "    \"review\": \"The headphones broke after one week of use. Very poor quality.\"\n"
                                        + "}\n\n"
                                        + "Ensure your response can be parsed by Java JSON, using this format as an example:\n"
                                        + "{\n"
                                        + " \"id\": \"12345\",\n"
                                        + " \"score\": 1,\n"
                                        + " \"reasons\": [\n"
                                        + "   \"poor quality\"\n"
                                        + "   ]\n"
                                        + "}"),
                        new ChatMessage(MessageRole.USER, "\"input\":\n" + "{input}")));
```
{{< /tab >}}

{{< /tabs >}}

**Key points:**
- Define multiple messages with different roles (SYSTEM, USER)
- Each message can have its own template variables

Template variables are replaced in message text, including text in tool results.
For example, `weather: {city}` becomes `weather: Paris` when `city="Paris"`.
Media and other non-text content stay unchanged. Use `formatMessages()` (Java)
or `format_messages()` (Python) to keep media; `formatString()` / `format_string()`
returns text only. Conversation history added to the prompt is used as-is, so
braces in an actual tool result are not treated as template variables.

### Using Prompts in Agents

Start with the Agent and connection in the
[Resources example]({{< ref "docs/development/create-agent/resources#declaration-api" >}}).
Add the following prompt and request Action, and replace the model setup with the
one below. Each input is review text; `language` controls the summary language.
Imports are omitted.

{{< tabs "Using Prompts in Agents" >}}
{{< tab "Python" >}}
```python
@prompt
@staticmethod
def review_prompt() -> Prompt:
    return Prompt.from_messages([
        ChatMessage.system("Summarize the review in {language}."),
    ])


@chat_model_setup
@staticmethod
def review_model() -> ResourceDescriptor:
    return ResourceDescriptor(
        clazz=ResourceName.ChatModel.OLLAMA_SETUP,
        connection="ollama_server",
        model="qwen3:8b",
        prompt="review_prompt",
    )


@action(EventType.InputEvent)
@staticmethod
def process_input(event: Event, ctx: RunnerContext) -> None:
    input_event = InputEvent.from_event(event)
    ctx.send_event(ChatRequestEvent(
        model="review_model",
        messages=[ChatMessage.user(str(input_event.input))],
        prompt_args={"language": "English"},
    ))
```
{{< /tab >}}
{{< tab "Java" >}}
```java
@Prompt
public static org.apache.flink.agents.api.prompt.Prompt reviewPrompt() {
    return org.apache.flink.agents.api.prompt.Prompt.fromMessages(List.of(
            ChatMessage.system("Summarize the review in {language}.")));
}

@ChatModelSetup
public static ResourceDescriptor reviewModel() {
    return ResourceDescriptor.Builder.newBuilder(ResourceName.ChatModel.OLLAMA_SETUP)
            .addInitialArgument("connection", "ollamaServer")
            .addInitialArgument("model", "qwen3:8b")
            .addInitialArgument("prompt", "reviewPrompt")
            .build();
}

@Action(EventType.InputEvent)
public static void processInput(Event event, RunnerContext ctx) throws Exception {
    InputEvent input = InputEvent.fromEvent(event);
    ctx.sendEvent(new ChatRequestEvent(
            "reviewModel",
            List.of(ChatMessage.user(String.valueOf(input.getInput()))),
            Map.of("language", "English"),
            null));
}
```
{{< /tab >}}
{{< /tabs >}}

The setup's `prompt` field references the registered prompt. The framework fills
its placeholders from `prompt_args` (Python) / `promptArgs` (Java), then places
the rendered prompt before the request's messages. In this example, the model
receives the system instruction "Summarize the review in English." followed by
the user's review.

For handling the response, see
[Using Chat Events]({{< ref "docs/development/calling-llms/chat#chat-events" >}}).
You can also supply prompt arguments when calling
[`ctx.chat`]({{< ref "docs/development/calling-llms/chat#using-ctx-chat" >}}): use
its `prompt_args` argument in Python, or pass a `ChatRequestEvent` in Java.

## Brace Handling

`{variable_name}` is the only template syntax. When a prompt is rendered:

- `{name}` is replaced with the matching argument; if no argument is supplied, the placeholder is left unchanged.
- Any other `{` or `}` (including JSON braces in examples) passes through verbatim.
- There is **no** `{{` / `}}` escape. Unlike Python f-strings and `str.format`, doubled braces are *not* collapsed to single braces — they reach the LLM as literal `{{` and `}}`.

Write literal JSON examples with single braces. Doubling them sends `{{` / `}}` to the model, which may copy that form into its reply and break downstream `json.loads`.
