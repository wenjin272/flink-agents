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
from abc import ABC
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator
from pyflink.common import Row


class Event(BaseModel, ABC, extra="allow"):
    """Base class for all event types in the system. Event allow extra properties, but
    these properties are required isinstance of BaseModel, or json serializable.

    Attributes:
    ----------
    id : UUID
        Unique identifier for the event, automatically generated using uuid4.
    """
    id: UUID = Field(default_factory=uuid4)

    @model_validator(mode='after')
    def validate_extra(self) -> 'Event':
        """Ensure init fields is serializable."""
        #TODO: support Event contains Row field be json serializable
        for value in self.model_dump().values():
            if isinstance(value, Row):
                return self
        self.model_dump_json()
        return self

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        # Ensure added property can be serialized.
        self.model_dump_json()


class InputEvent(Event):
    """Event generated by the framework, carrying an input data that
    arrives at the agent.
    """

    input: Any


class OutputEvent(Event):
    """Event representing a result from agent. By generating an OutputEvent,
    actions can emit output data.

    Attributes:
    ----------
    output : Any
        The output result returned by the agent.
    """

    output: Any
