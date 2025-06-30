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
from typing import Any, Dict, List

import cloudpickle
from pyflink.common import Row, TypeInformation
from pyflink.common.typeinfo import RowTypeInfo, BasicType, BasicTypeInfo, PickledBytesTypeInfo
from pyflink.datastream import DataStream, KeySelector, StreamExecutionEnvironment
from pyflink.util.java_utils import invoke_method

from flink_agents.api.event import OutputEvent
from flink_agents.api.execution_enviroment import AgentsExecutionEnvironment
from flink_agents.api.workflow import Workflow
from flink_agents.plan.workflow_plan import WorkflowPlan


class RemoteExecutionEnvironment(AgentsExecutionEnvironment):
    __env: StreamExecutionEnvironment
    __input: DataStream
    __key_selector: KeySelector
    __workflow_plan: WorkflowPlan
    __output: DataStream

    def from_datastream(self, input: DataStream, key_selector: KeySelector = None) -> 'AgentsExecutionEnvironment':
        self.__input = input.map(lambda x: Row(key=key_selector.get_key(x) if key_selector is not None else 0,
                                               value=cloudpickle.dumps(x)),
                                 output_type=RowTypeInfo([BasicTypeInfo(BasicType.INT), PickledBytesTypeInfo()],
                                                         ["key", "value"]))
        print(self.__input.get_type())
        self.__key_selector = key_selector
        return self

    def apply(self, workflow: Workflow) -> 'AgentsExecutionEnvironment':
        self.__workflow_plan = WorkflowPlan.from_workflow(workflow)
        return self

    def to_datastream(self) -> DataStream:
        j_data_stream_output = invoke_method(
            None,
            "org.apache.flink.agents.runtime.FlinkAgent",
            "connectToWorkflow",
            [self.__input._j_data_stream,
             self.__workflow_plan.model_dump_json(serialize_as_any=True)],
            ["org.apache.flink.streaming.api.datastream.DataStream",
             "java.lang.String"]
        )
        output_stream = DataStream(j_data_stream_output)
        self.__output = output_stream.map(lambda x: cloudpickle.loads(x))
        return self.__output

    def execute(self) -> None:
        msg = "RemoteExecutionEnvironment does not support execute locally."
        raise NotImplementedError(msg)

    def from_list(self, input: List[Dict[str, Any]]) -> 'AgentsExecutionEnvironment':
        msg = "RemoteExecutionEnvironment does not support from_list."
        raise NotImplementedError(msg)

    def to_list(self) -> List[Dict[str, Any]]:
        msg = "RemoteExecutionEnvironment does not support to_list."
        raise NotImplementedError(msg)

def get_execution_environment(**kwargs: Dict[str, Any]) -> AgentsExecutionEnvironment:
    """Factory function to create a remote agents execution environment.

    Parameters
    ----------
    **kwargs : Dict[str, Any]
        The dict of parameters to configure the execution environment.

    Returns:
    -------
    AgentsExecutionEnvironment
        A configured agents execution environment instance.
    """
    return RemoteExecutionEnvironment()
