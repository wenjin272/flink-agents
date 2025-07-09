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
from typing import Any, Dict, List, Optional

import cloudpickle
from pyflink.common import TypeInformation
from pyflink.common.typeinfo import (
    PickledBytesTypeInfo,
)
from pyflink.datastream import (
    DataStream,
    KeyedStream,
    KeySelector,
)
from pyflink.table import Schema, StreamTableEnvironment, Table
from pyflink.util.java_utils import invoke_method

from flink_agents.api.execution_enviroment import (
    AgentBuilder,
    AgentInstance,
    AgentsExecutionEnvironment,
)
from flink_agents.api.workflow import Workflow
from flink_agents.plan.workflow_plan import WorkflowPlan


class RemoteAgentBuilder(AgentBuilder):
    """RemoteAgentBuilder for integrating datastream and agent."""

    __input: DataStream
    __workflow_plan: WorkflowPlan = None
    __output: DataStream = None
    __t_env: StreamTableEnvironment

    def __init__(
        self, input: DataStream, t_env: Optional[StreamTableEnvironment] = None
    ) -> None:
        """Init method of RemoteAgentBuilder."""
        self.__input = input
        self.__t_env = t_env

    def apply(self, workflow: Workflow) -> "AgentBuilder":
        """Set workflow of execution environment.

        Parameters
        ----------
        workflow : Workflow
            The workflow user defined to run in execution environment.
        """
        if self.__workflow_plan is not None:
            err_msg = "RemoteAgentBuilder doesn't support apply multiple workflows yet."
            raise RuntimeError(err_msg)
        self.__workflow_plan = WorkflowPlan.from_workflow(workflow)
        return self

    def to_datastream(
        self, output_type: Optional[TypeInformation] = None
    ) -> DataStream:
        """Get output datastream of workflow execution.

        Returns:
        -------
        DataStream
            Output datastream of agent execution.
        """
        j_data_stream_output = invoke_method(
            None,
            "org.apache.flink.agents.runtime.CompileUtils",
            "connectToWorkflow",
            [
                self.__input._j_data_stream,
                self.__workflow_plan.model_dump_json(serialize_as_any=True),
            ],
            [
                "org.apache.flink.streaming.api.datastream.KeyedStream",
                "java.lang.String",
            ],
        )
        output_stream = DataStream(j_data_stream_output)
        self.__output = output_stream.map(
            lambda x: cloudpickle.loads(x), output_type=output_type
        )
        return self.__output

    def to_table(self, schema: Schema, output_type: TypeInformation) -> Table:
        """Get output Table of workflow execution.

        Parameters
        ----------
        schema : Schema
            Indicate schema of the output table.
        output_type : TypeInformation
            Indicate schema corresponding type information.

        Returns:
        -------
        Table
            Output Table of agent execution.
        """
        return self.__t_env.from_data_stream(self.to_datastream(output_type), schema)

    def to_list(self) -> List[Dict[str, Any]]:
        """Get output list of workflow execution.

        This method is not supported for remote execution environments.
        """
        msg = "RemoteAgentBuilder does not support to_list."
        raise NotImplementedError(msg)

    def build(self) -> AgentInstance:
        """Build agent instance.

        This method is not supported for RemoteAgentBuilder.
        """
        msg = (
            "RemoteAgentBuilder does not support build Agent Instance and run individually, must run as"
            "a flink job."
        )
        raise NotImplementedError(msg)


class RemoteExecutionEnvironment(AgentsExecutionEnvironment):
    """Implementation of AgentsExecutionEnvironment for execution with DataStream."""

    @staticmethod
    def __process_input_datastream(
        input: DataStream, key_selector: Optional[KeySelector] = None
    ) -> KeyedStream:
        if isinstance(input, KeyedStream):
            return input
        else:
            if key_selector is None:
                msg = "KeySelector must be provided."
                raise RuntimeError(msg)
            input = input.key_by(key_selector)
            return input

    def from_datastream(
        self, input: DataStream, key_selector: KeySelector = None
    ) -> RemoteAgentBuilder:
        """Set input datastream of agent.

        Parameters
        ----------
        input : DataStream
            Receive a DataStream as input.
        key_selector : KeySelector
            Extract key from each input record, must not be None when input is
            not KeyedStream.
        """
        input = self.__process_input_datastream(input, key_selector)

        return RemoteAgentBuilder(input=input)

    def from_table(
        self,
        input: Table,
        t_env: StreamTableEnvironment,
        key_selector: Optional[KeySelector] = None,
    ) -> AgentBuilder:
        """Set input Table of agent.

        Parameters
        ----------
        input : Table
            Receive a Table as input.
        t_env: StreamTableEnvironment
            table environment supports convert table to/from datastream.
        key_selector : KeySelector
            Extract key from each input record.
        """
        input = t_env.to_data_stream(table=input)

        input = input.map(lambda x: x, output_type=PickledBytesTypeInfo())

        input = self.__process_input_datastream(input, key_selector)
        return RemoteAgentBuilder(input=input, t_env=t_env)

    def from_list(self, input: List[Dict[str, Any]]) -> "AgentsExecutionEnvironment":
        """Set input list of workflow execution.

        This method is not supported for remote execution environments.
        """
        msg = "RemoteExecutionEnvironment does not support from_list."
        raise NotImplementedError(msg)


def create_instance(**kwargs: Dict[str, Any]) -> AgentsExecutionEnvironment:
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
