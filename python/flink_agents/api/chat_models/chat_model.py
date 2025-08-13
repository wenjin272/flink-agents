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
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence, Union

from pydantic import Field
from typing_extensions import override

from flink_agents.api.chat_message import ChatMessage
from flink_agents.api.prompts.prompt import Prompt
from flink_agents.api.resource import Resource, ResourceType
from flink_agents.api.tools.tool import BaseTool


class BaseChatModelServer(Resource, ABC):
    """Base abstract class for chat model server.

    Responsible for managing model service connection configurations, such as:
    - Service address (base_url)
    - API key (api_key)
    - Connection timeout (timeout)
    - Model name (model_name)
    - Authentication information, etc.

    Provides the basic chat interface for direct communication with model services.

    One server can be shared in multiple chat models.
    """

    @classmethod
    @override
    def resource_type(cls) -> ResourceType:
        """Return resource type of class."""
        return ResourceType.CHAT_MODEL_SERVER

    @abstractmethod
    def chat(
        self,
        messages: Sequence[ChatMessage],
        tools: Optional[List[BaseTool]] = None,
        **kwargs: Any,
    ) -> ChatMessage:
        """Direct communication with model service for chat conversation.

        Parameters
        ----------
        messages : Sequence[ChatMessage]
            Input message sequence
        tools : Optional[List]
            List of tools that can be called by the model
        **kwargs : Any
            Additional parameters passed to the model service (e.g., temperature,
            max_tokens, etc.)

        Returns:
        -------
        ChatMessage
            Model response message
        """


class ChatModel(Resource):
    """Chat model implementation.

    Responsible for managing chat configurations, such as:
    - Prompt templates (prompt)
    - Available tools (tools)
    - Generation parameters (temperature, max_tokens, etc.)
    - Context management

    Internally calls ChatModelServer to perform actual communication with llm.

    Different chat models can call the same chat model server with different chat
    arguments.
    """

    server: str = Field(description="Name of the referenced server.")
    prompt: Optional[Union[Prompt, str]] = None
    tools: Optional[List[str]] = None

    @property
    @abstractmethod
    def model_kwargs(self) -> Dict[str, Any]:
        """Return chat model settings."""

    @classmethod
    @override
    def resource_type(cls) -> ResourceType:
        """Return resource type of class."""
        return ResourceType.CHAT_MODEL

    def chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatMessage:
        """Execute chat conversation.

        1. Apply prompt template (if any)
        2. Bind tools (if any)
        3. Call ChatModelConnection to perform actual communication
        4. Process response

        Parameters
        ----------
        messages : Sequence[ChatMessage]
            Input message sequence
        **kwargs : Any
            Additional parameters passed to the model service

        Returns:
        -------
        ChatMessage
            Model response message
        """
        # Get model connection
        server = self.get_resource(self.server, ResourceType.CHAT_MODEL_SERVER)

        # Apply prompt template
        if self.prompt is not None:
            if isinstance(self.prompt, str):
                # Get prompt resource if it's a string
                prompt = self.get_resource(self.prompt, ResourceType.PROMPT)
            else:
                prompt = self.prompt

            input_variable = {}
            for msg in messages:
                input_variable.update(msg.extra_args)
            messages = prompt.format_messages(**input_variable)

        # Bind tools
        tools = None
        if self.tools is not None:
            tools = [
                self.get_resource(tool_name, ResourceType.TOOL)
                for tool_name in self.tools
            ]

        # Call server to execute chat
        merged_kwargs = self.model_kwargs.copy()
        merged_kwargs.update(kwargs)
        return server.chat(messages, tools=tools, **merged_kwargs)
