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
from flink_agents.plan.function import JavaFunction, PythonFunction


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


def test_compatibility_with_java_agent_plan() -> None:  # noqa: D103
    with Path.open(
        Path(
            f"{current_dir}/../../../../plan/src/test/resources/agent_plans/agent_plan.json"
        )
    ) as f:
        java_plan_json = f.read()

    agent_plan = AgentPlan.model_validate_json(java_plan_json)
    actions = agent_plan.actions

    assert len(actions) == 2

    # check the first action
    assert "first_action" in actions
    action1 = actions["first_action"]
    func1 = action1.exec
    assert isinstance(func1, JavaFunction)
    assert func1.qualname == "org.apache.flink.agents.plan.TestAction"
    assert func1.method_name == "legal"
    assert func1.parameter_types == [
        "org.apache.flink.agents.api.InputEvent",
        "org.apache.flink.agents.api.context.RunnerContext",
    ]
    listen_event_types1 = action1.listen_event_types
    assert listen_event_types1 == ["org.apache.flink.agents.api.InputEvent"]

    # check the second action
    assert "second_action" in actions
    action2 = actions["second_action"]
    func2 = action2.exec
    assert isinstance(func2, JavaFunction)
    assert (
        func2.qualname
        == "org.apache.flink.agents.plan.serializer.AgentPlanJsonDeserializerTest$MyAction"
    )
    assert func2.method_name == "doNothing"
    assert func2.parameter_types == [
        "org.apache.flink.agents.api.Event",
        "org.apache.flink.agents.api.context.RunnerContext",
    ]
    listen_event_types2 = action2.listen_event_types
    assert listen_event_types2 == [
        "org.apache.flink.agents.api.InputEvent",
        "org.apache.flink.agents.plan.serializer.AgentPlanJsonDeserializerTest$MyEvent",
    ]

    # check actions_by_event
    actions_by_event = agent_plan.actions_by_event
    assert len(actions_by_event) == 2

    input_evnet = "org.apache.flink.agents.api.InputEvent"
    assert input_evnet in actions_by_event
    assert actions_by_event[input_evnet] == ["first_action", "second_action"]

    my_event = (
        "org.apache.flink.agents.plan.serializer.AgentPlanJsonDeserializerTest$MyEvent"
    )
    assert my_event in actions_by_event
    assert actions_by_event[my_event] == ["second_action"]
