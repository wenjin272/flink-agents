################################################################################
#  Licensed to the Apache Software Foundation (ASF) under one
#  or more contributor license agreements.  See the NOTICE file
#  distributed with this work for additional information
#  regarding copyright ownership.  The ASF licenses this file
#  to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance
#  with the License.  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
# limitations under the License.
#################################################################################
from typing import TYPE_CHECKING, List, Type, cast

from flink_agents.api.chat_message import ChatMessage, MessageRole
from flink_agents.api.memory.long_term_memory import (
    BaseLongTermMemory,
    MemorySet,
    MemorySetItem,
    SummarizationStrategy,
)
from flink_agents.api.resource import ResourceType
from flink_agents.api.runner_context import RunnerContext

if TYPE_CHECKING:
    from flink_agents.api.chat_models.chat_model import BaseChatModelSetup
    from flink_agents.api.prompts.prompt import Prompt


def summarize(
    ltm: BaseLongTermMemory,
    memory_set: MemorySet,
    ctx: RunnerContext,
    ids: List[str] | None = None,
) -> None:
    """Generate summarization of the items in the memory set.

    Will add the summarization to memory set, and delete original items involved
    in summarization.

    Args:
        ltm: The long term memory the memory set belongs to.
        memory_set: The memory set to be summarized.
        ctx: The runner context used to retrieve needed resources.
        ids: The ids of items to be summarized. If not provided, all items will be
        involved in summarization. Optional
    """
    strategy: SummarizationStrategy = cast(
        "SummarizationStrategy", memory_set.compaction_strategy
    )

    # retrieve all items
    items: List[MemorySetItem] = ltm.get(memory_set=memory_set, ids=ids)

    response: ChatMessage = _generate_summarization(
        items, memory_set.item_type, strategy, ctx
    )

    if memory_set.item_type == ChatMessage:
        item = ChatMessage(role=MessageRole.USER, content=response.content)
    else:
        item = response.content

    start = min(
        [
            item.created_time.start if item.compacted else item.created_time
            for item in items
        ]
    ).isoformat()
    end = max(
        [
            item.created_time.end if item.compacted else item.created_time
            for item in items
        ]
    ).isoformat()
    last_accessed_time = max([item.last_accessed_time for item in items]).isoformat()

    # delete involved items
    ids = [item.id for item in items]
    ltm.delete(memory_set=memory_set, ids=ids)

    # add summarization to memory set
    ltm.add(
        memory_set=memory_set,
        memory_items=item,
        metadatas={
            "compacted": True,
            "created_time_start": start,
            "created_time_end": end,
            "last_accessed_time": last_accessed_time,
        },
    )


def _generate_summarization(
    memory_set_items: List[MemorySetItem],
    item_type: Type,
    strategy: SummarizationStrategy,
    ctx: RunnerContext,
) -> ChatMessage:
    """Generate summarization of the items by llm."""
    # get arguments
    model_name = strategy.model
    prompt = strategy.prompt

    msgs: List[ChatMessage]
    if item_type == ChatMessage:
        msgs = [item.value for item in memory_set_items]
    else:
        msgs = [
            ChatMessage(role=MessageRole.USER, content=str(item.value))
            for item in memory_set_items
        ]

    # generate summary
    model: BaseChatModelSetup = cast(
        "BaseChatModelSetup",
        ctx.get_resource(name=model_name, type=ResourceType.CHAT_MODEL),
    )
    input_variable = {}
    for msg in msgs:
        input_variable.update(msg.extra_args)

    if prompt is not None:
        if isinstance(prompt, str):
            prompt: Prompt = cast(
                "Prompt",
                ctx.get_resource(prompt, ResourceType.PROMPT),
            )
        prompt_messages = prompt.format_messages(
            role=MessageRole.USER, **input_variable
        )
        msgs.extend(prompt_messages)
    else:
        msgs.append(
            ChatMessage(
                role=MessageRole.USER,
                content="Create a summary of the conversation above",
            )
        )

    response: ChatMessage = model.chat(messages=msgs)

    return response
