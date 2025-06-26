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

from flink_agents.api.decorators import action
from flink_agents.api.event import Event, InputEvent, OutputEvent
from flink_agents.api.runner_context import RunnerContext
from flink_agents.api.workflow import Workflow
from flink_agents.plan.function import PythonFunction
from flink_agents.plan.workflow_plan import WorkflowPlan


class TestWorkflow(Workflow): #noqa D101
    @action(InputEvent)
    @staticmethod
    def increment(event: Event, ctx: RunnerContext) -> None: #noqa D102
        value = event.input
        value += 1
        ctx.send_event(OutputEvent(output=value))

def test_from_workflow(): #noqa D102
    workflow = TestWorkflow()
    workflow_plan = WorkflowPlan.from_workflow(workflow)
    event_type = f'{InputEvent.__module__}.{InputEvent.__name__}'
    actions = workflow_plan.get_actions(event_type)
    assert len(actions) == 1
    action = actions[0]
    assert action.name == "increment"
    func = action.exec
    assert isinstance(func, PythonFunction)
    assert func.module == "flink_agents.plan.tests.test_workflow_plan"
    assert func.qualname == "TestWorkflow.increment"
    assert action.listen_event_types == [event_type]

class InvalidWorkflow(Workflow): #noqa D101
    @action(InputEvent)
    @staticmethod
    def invalid_signature_action(event: Event) -> None: #noqa D102
        pass

def test_to_workflow_invalid_signature() -> None: #noqa D103
    workflow = InvalidWorkflow()
    with pytest.raises(TypeError):
        WorkflowPlan.from_workflow(workflow)

class MyEvent(Event):
    """Event for testing purposes."""

class MyWorkflow(Workflow): # noqa: D101
    @action(InputEvent)
    @staticmethod
    def first_action(event: InputEvent, ctx: RunnerContext) -> None: # noqa: D102
        pass

    @action(InputEvent, MyEvent)
    @staticmethod
    def second_action(event: InputEvent, ctx: RunnerContext) -> None: # noqa: D102
        pass

@pytest.fixture(scope="module")
def workflow_plan() -> WorkflowPlan: # noqa: D103
    return WorkflowPlan.from_workflow(MyWorkflow())

current_dir = Path(__file__).parent

def test_workflow_plan_serialize(workflow_plan: WorkflowPlan) -> None: # noqa: D103
    json_value = workflow_plan.model_dump_json(serialize_as_any=True, indent=4)
    with Path.open(Path(f'{current_dir}/resources/workflow_plan.json')) as f:
        expected_json = f.read()
    actual = json.loads(json_value)
    expected = json.loads(expected_json)
    assert actual == expected

def test_workflow_plan_deserialize(workflow_plan: WorkflowPlan) -> None: # noqa: D103
    with Path.open(Path(f'{current_dir}/resources/workflow_plan.json')) as f:
        expected_json = f.read()
    deserialized_workflow_plan = WorkflowPlan.model_validate_json(expected_json)
    assert deserialized_workflow_plan == workflow_plan
