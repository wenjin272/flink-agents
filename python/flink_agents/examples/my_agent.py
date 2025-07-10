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
import copy
from typing import Any

from pydantic import BaseModel

from flink_agents.api.decorators import action
from flink_agents.api.event import Event, InputEvent, OutputEvent
from flink_agents.api.runner_context import RunnerContext
from flink_agents.api.workflow import Workflow


class ItemData(BaseModel):
    """Data model for storing item information.

    Attributes:
    ----------
    id : int
        Unique identifier of the item
    review : str
        The user review of the item
    review_score: float
        The review_score of the item
    """

    id: int
    review: str
    review_score: float


class MyEvent(Event):  # noqa D101
    value: Any


class DataStreamAgent(Workflow):
    """Agent used for explaining integrating agents with DataStream.

    Because pemja will find action in this class when execute Agent, we can't
    define this class directly in example.py for module name will be set
    to __main__.
    """

    @action(InputEvent)
    @staticmethod
    def first_action(event: Event, ctx: RunnerContext):  # noqa D102
        input = event.input
        content = copy.deepcopy(input)
        content.review += " first action"
        ctx.get_short_term_memory().set("a.b", 1)
        ctx.get_short_term_memory().set("m", True)
        print(ctx.get_short_term_memory().get("m"))
        print(ctx.get_short_term_memory().get("a").get_field_names())
        print(ctx.get_short_term_memory().get("a").get_fields())
        print(ctx.get_short_term_memory().get("a").get("b"))
        ctx.send_event(MyEvent(value=content))

    @action(MyEvent)
    @staticmethod
    def second_action(event: Event, ctx: RunnerContext):  # noqa D102
        input = event.value
        content = copy.deepcopy(input)
        content.review += " second action"
        ctx.send_event(OutputEvent(output=content))


class TableAgent(Workflow):
    """Agent used for explaining integrating agents with Table.

    Because pemja will find action in this class when execute Agent, we can't
    define this class directly in example.py for module name will be set
    to __main__.
    """

    @action(InputEvent)
    @staticmethod
    def first_action(event: Event, ctx: RunnerContext):  # noqa D102
        input = event.input
        content = input
        content["review"] += " first action"
        ctx.send_event(MyEvent(value=content))

    @action(MyEvent)
    @staticmethod
    def second_action(event: Event, ctx: RunnerContext):  # noqa D102
        input = event.value
        content = input
        content["review"] += " second action"
        ctx.send_event(OutputEvent(output=content))
