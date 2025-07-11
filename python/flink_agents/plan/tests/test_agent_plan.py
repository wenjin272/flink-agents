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
import json
from pathlib import Path

import pytest

from flink_agents.api.agent import Agent
from flink_agents.api.decorators import action
from flink_agents.api.event import Event, InputEvent, OutputEvent
from flink_agents.api.runner_context import RunnerContext
from flink_agents.plan.agent_plan import AgentPlan
from flink_agents.plan.function import PythonFunction


class TestAgent(Agent):  # noqa D101
    @action(InputEvent)
    @staticmethod
    def increment(event: Event, ctx: RunnerContext) -> None:  # noqa D102
        value = event.input
        value += 1
        ctx.send_event(OutputEvent(output=value))


def test_from_agent():  # noqa D102
    agent = TestAgent()
    agent_plan = AgentPlan.from_agent(agent)
    event_type = f"{InputEvent.__module__}.{InputEvent.__name__}"
    actions = agent_plan.get_actions(event_type)
    assert len(actions) == 1
    action = actions[0]
    assert action.name == "increment"
    func = action.exec
    assert isinstance(func, PythonFunction)
    assert func.module == "flink_agents.plan.tests.test_agent_plan"
    assert func.qualname == "TestAgent.increment"
    assert action.listen_event_types == [event_type]


class InvalidAgent(Agent):  # noqa D101
    @action(InputEvent)
    @staticmethod
    def invalid_signature_action(event: Event) -> None:  # noqa D102
        pass


def test_to_agent_invalid_signature() -> None:  # noqa D103
    agent = InvalidAgent()
    with pytest.raises(TypeError):
        AgentPlan.from_agent(agent)


class MyEvent(Event):
    """Event for testing purposes."""


class MyAgent(Agent):  # noqa: D101
    @action(InputEvent)
    @staticmethod
    def first_action(event: InputEvent, ctx: RunnerContext) -> None:  # noqa: D102
        pass

    @action(InputEvent, MyEvent)
    @staticmethod
    def second_action(event: InputEvent, ctx: RunnerContext) -> None:  # noqa: D102
        pass


@pytest.fixture(scope="module")
def agent_plan() -> AgentPlan:  # noqa: D103
    return AgentPlan.from_agent(MyAgent())


current_dir = Path(__file__).parent


def test_agent_plan_serialize(agent_plan: AgentPlan) -> None:  # noqa: D103
    json_value = agent_plan.model_dump_json(serialize_as_any=True, indent=4)
    with Path.open(Path(f"{current_dir}/resources/agent_plan.json")) as f:
        expected_json = f.read()
    actual = json.loads(json_value)
    expected = json.loads(expected_json)
    assert actual == expected


def test_agent_plan_deserialize(agent_plan: AgentPlan) -> None:  # noqa: D103
    with Path.open(Path(f"{current_dir}/resources/agent_plan.json")) as f:
        expected_json = f.read()
    deserialized_agent_plan = AgentPlan.model_validate_json(expected_json)
    assert deserialized_agent_plan == agent_plan
