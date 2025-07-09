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

from pyflink.common import TypeInformation
from pyflink.datastream import DataStream, KeySelector
from pyflink.table import Schema, StreamTableEnvironment, Table

from flink_agents.api.execution_enviroment import (
    AgentBuilder,
    AgentInstance,
    AgentsExecutionEnvironment,
)
from flink_agents.api.workflow import Workflow
from flink_agents.runtime.local_runner import LocalRunner


class AgentInstanceImpl(AgentInstance):
    """AgentInstance impl which can be executed individually."""

    __input: List[Dict[str, Any]]
    __output: List[Any]
    __runner: LocalRunner
    __executed: bool = False

    def __init__(
        self, input: List[Dict[str, Any]], output: List[Any], runner: LocalRunner
    ) -> None:
        """Init method of AgentInstanceImpl."""
        self.__input = input
        self.__output = output
        self.__runner = runner

    def execute(self) -> None:
        """Execute agent.

        Doesn't support execute multiple times.
        """
        if self.__executed:
            err_msg = (
                "LocalExecutionEnvironment doesn't support execute multiple times."
            )
            raise RuntimeError(err_msg)
        self.__executed = True
        for input in self.__input:
            self.__runner.run(**input)
        outputs = self.__runner.get_outputs()
        for output in outputs:
            self.__output.append(output)


class LocalAgentBuilder(AgentBuilder):
    """LocalAgentBuilder for building agent instance."""

    __input: List[Dict[str, Any]]
    __output: List[Any]
    __runner: LocalRunner = None
    __executed: bool = False

    def __init__(self, input: List[Dict[str, Any]]) -> None:
        """Init empty output list."""
        self.__input = input
        self.__output = []

    def apply(self, workflow: Workflow) -> "AgentBuilder":
        """Create local runner to execute given workflow.

        Doesn't support apply multiple workflows.
        """
        if self.__runner is not None:
            err_msg = (
                "LocalExecutionEnvironment doesn't support apply multiple workflows."
            )
            raise RuntimeError(err_msg)
        self.__runner = LocalRunner(workflow)
        return self

    def to_list(self) -> List[Dict[str, Any]]:
        """Get output list of execution environment."""
        return self.__output

    def build(self) -> AgentInstance:
        """Build agent instance."""
        return AgentInstanceImpl(self.__input, self.__output, self.__runner)

    def to_datastream(self) -> DataStream:
        """Get output DataStream of workflow execution.

        This method is not supported for LocalAgentBuilder.
        """
        msg = "LocalAgentBuilder does not support to_datastream."
        raise NotImplementedError(msg)

    def to_table(self, schema: Schema, output_type: TypeInformation) -> Table:
        """Get output Table of workflow execution.

        This method is not supported for LocalAgentBuilder.
        """
        msg = "LocalAgentBuilder does not support to_table."
        raise NotImplementedError(msg)


class LocalExecutionEnvironment(AgentsExecutionEnvironment):
    """Implementation of AgentsExecutionEnvironment for local execution environment."""

    def from_list(self, input: list) -> LocalAgentBuilder:
        """Set input list of execution environment."""
        return LocalAgentBuilder(input)

    def from_datastream(
        self, input: DataStream, key_selector: KeySelector = None
    ) -> "AgentsExecutionEnvironment":
        """Set input DataStream of workflow execution.

        This method is not supported for local execution environments.
        """
        msg = "LocalExecutionEnvironment does not support from_datastream."
        raise NotImplementedError(msg)

    def from_table(
        self,
        input: Table,
        t_env: StreamTableEnvironment,
        key_selector: KeySelector = None,
    ) -> AgentBuilder:
        """Set input Table of workflow execution.

        This method is not supported for local execution environments.
        """
        msg = "LocalExecutionEnvironment does not support from_table."
        raise NotImplementedError(msg)


def create_instance(**kwargs: Dict[str, Any]) -> AgentsExecutionEnvironment:
    """Factory function to create a local agents execution environment.

    Parameters
    ----------
    **kwargs : Dict[str, Any]
        The dict of parameters to configure the execution environment.

    Returns:
    -------
    AgentsExecutionEnvironment
        A configured agents execution environment instance.
    """
    return LocalExecutionEnvironment()
