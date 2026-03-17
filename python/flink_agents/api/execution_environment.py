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
import importlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from importlib_resources import files
from pyflink.common import TypeInformation
from pyflink.datastream import DataStream, KeySelector, StreamExecutionEnvironment
from pyflink.table import Schema, StreamTableEnvironment, Table

from flink_agents.api.agents.agent import Agent
from flink_agents.api.configuration import Configuration
from flink_agents.api.resource import (
    ResourceDescriptor,
    ResourceType,
    SerializableResource,
)
from flink_agents.api.skills.skill_manager import AgentSkillManager
from flink_agents.api.version_compatibility import flink_version_manager


class AgentBuilder(ABC):
    """Builder for integrating agent with input and output."""

    @abstractmethod
    def apply(self, agent: Agent) -> "AgentBuilder":
        """Set agent of AgentBuilder.

        Parameters
        ----------
        agent : Agent
            The agent user defined to run in execution environment.
        """

    @abstractmethod
    def to_list(self) -> List[Dict[str, Any]]:
        """Get output list of agent execution.

        The element in the list is a dict like {'key': output}.

        Returns:
        -------
        list
            Outputs of agent execution.
        """

    @abstractmethod
    def to_datastream(self) -> DataStream:
        """Get output datastream of agent execution.

        Returns:
        -------
        DataStream
            Output datastream of agent execution.
        """

    # TODO: auto generate output_type.
    @abstractmethod
    def to_table(self, schema: Schema, output_type: TypeInformation) -> Table:
        """Get output table of agent execution.

        Parameters
        ----------
        schema : Schema
            Indicate schema of the output table.
        output_type : TypeInformation
            Indicate schema corresponding type information.

        Returns:
        -------
        Table
            Output table of agent execution.
        """


class AgentsExecutionEnvironment(ABC):
    """Base class for agent execution environment."""

    _resources: Dict[ResourceType, Dict[str, Any]]

    def __init__(self) -> None:
        """Init method."""
        self._actions = {}
        self._resources = {}
        for type in ResourceType:
            self._resources[type] = {}

    @property
    def resources(self) -> Dict[ResourceType, Dict[str, Any]]:
        """Get registered resources."""
        return self._resources

    @staticmethod
    def get_execution_environment(
        env: StreamExecutionEnvironment | None = None,
        t_env: StreamTableEnvironment | None = None,
        **kwargs: Dict[str, Any],
    ) -> "AgentsExecutionEnvironment":
        """Get agents execution environment.

        Currently, user can run flink agents in ide using LocalExecutionEnvironment or
        RemoteExecutionEnvironment. To distinguish which environment to use, when run
        flink agents with pyflink datastream/table, user should pass flink
        StreamExecutionEnvironment when get AgentsExecutionEnvironment.

        Returns:
        -------
        AgentsExecutionEnvironment
            Environment for agent execution.
        """
        if env is None:
            return importlib.import_module(
                "flink_agents.runtime.local_execution_environment"
            ).create_instance(env=env, t_env=t_env, **kwargs)
        else:
            major_version = flink_version_manager.major_version
            if major_version:
                # Determine the version-specific lib directory
                version_dir = f"flink-{major_version}"
                lib_base = files("flink_agents.lib")
                version_lib = lib_base / version_dir

                # Check if version-specific directory exists
                if version_lib.is_dir():
                    for jar_file in version_lib.iterdir():
                        if jar_file.is_file() and str(jar_file).endswith(".jar"):
                            env.add_jars(f"file://{jar_file}")
                else:
                    err_msg = (
                        f"Flink Agents dist JAR for Flink {major_version} not found."
                    )
                    raise FileNotFoundError(err_msg)

                return importlib.import_module(
                    "flink_agents.runtime.remote_execution_environment"
                ).create_instance(env=env, t_env=t_env, **kwargs)
            else:
                err_msg = "Apache Flink is not installed."
                raise ModuleNotFoundError(err_msg)

    @abstractmethod
    def get_config(self, path: str | None = None) -> Configuration:
        """Get the writable configuration for flink agents.

        Returns:
        -------
        WritableConfiguration
            The configuration for flink agents.
        """

    @abstractmethod
    def from_list(self, input: List[Dict[str, Any]]) -> AgentBuilder:
        """Set input for agents. Used for local execution.

        Parameters
        ----------
        input : list
            Receive a list as input. The element in the list should be a dict like
            {'key': Any, 'value': Any} or {'value': Any} , extra field will be ignored.

        Returns:
        -------
        AgentBuilder
            A new builder to build an agent for specific input.
        """

    @abstractmethod
    def from_datastream(
        self, input: DataStream, key_selector: KeySelector | Callable | None = None
    ) -> AgentBuilder:
        """Set input for agents. Used for remote execution.

        Parameters
        ----------
        input : DataStream
            Receive a DataStream as input.
        key_selector : KeySelector
            Extract key from each input record.

        Returns:
        -------
        AgentBuilder
            A new builder to build an agent for specific input.
        """

    @abstractmethod
    def from_table(
        self,
        input: Table,
        key_selector: KeySelector | Callable | None = None,
    ) -> AgentBuilder:
        """Set input for agents. Used for remote execution.

        Parameters
        ----------
        input : Table
            Receive a Table as input.
        t_env: StreamTableEnvironment
            table environment supports convert Table to/from DataStream.
        key_selector : KeySelector
            Extract key from each input record.

        Returns:
        -------
        AgentBuilder
            A new builder to build an agent for specific input.
        """

    @abstractmethod
    def execute(self) -> None:
        """Execute agent individually."""

    def add_resource(
        self, name: str, resource_type: ResourceType, instance: SerializableResource | ResourceDescriptor
    ) -> "AgentsExecutionEnvironment":
        """Register resource to agent execution environment.

        Parameters
        ----------
        name : str
            The name of the prompt, should be unique in the same Agent.
        resource_type: ResourceType
            The type of the resource.
        instance: SerializableResource | ResourceDescriptor
            The serializable resource instance, or the descriptor of resource.

        Returns:
        -------
        AgentsExecutionEnvironment
            The environment to register the resource.
        """
        if name in self._resources[resource_type]:
            msg = f"{resource_type.value} {name} already defined"
            raise ValueError(msg)

        self._resources[resource_type][name] = instance
        return self

    def add_skills_from_paths(
        self,
        *paths: Path | str,
        source: Optional[str] = None,
    ) -> "AgentsExecutionEnvironment":
        """Add skills from filesystem paths.

        Each path should point to a directory containing skill subdirectories,
        where each subdirectory has a SKILL.md file.

        Parameters
        ----------
        *paths : Path | str
            Paths to directories containing skill subdirectories.
        source : Optional[str]
            Custom source identifier for the skills.

        Returns:
        -------
        AgentsExecutionEnvironment
            The environment to register the skills.

        Example:
        -------
        >>> env = AgentsExecutionEnvironment.get_execution_environment()
        >>> env.add_skills_from_paths("/path/to/skills", "/another/path")
        """
        manager = self._get_or_create_skill_manager()
        for path in paths:
            manager.add_skills_from_path(path, source=source)
        return self

    def add_skills_from_resources(
        self,
        package_path: str,
        source: Optional[str] = None,
    ) -> "AgentsExecutionEnvironment":
        """Add skills from Python package resources.

        This is useful for distributing skills within Python packages,
        similar to JAR resources in Java.

        Parameters
        ----------
        package_path : str
            Python package path containing skills (e.g., "my_package.skills").
        source : Optional[str]
            Custom source identifier for the skills.

        Returns:
        -------
        AgentsExecutionEnvironment
            The environment to register the skills.

        Example:
        -------
        >>> env = AgentsExecutionEnvironment.get_execution_environment()
        >>> env.add_skills_from_resource("my_package.skills")
        """
        manager = self._get_or_create_skill_manager()
        manager.add_skills_from_resource(package_path, source=source)
        return self

    def add_skills_from_urls(
        self,
        *urls: str,
        source: Optional[str] = None,
    ) -> "AgentsExecutionEnvironment":
        """Add skills from remote URLs.

        Each URL should point to either:
        - A zip file containing skill directories
        - A directory listing endpoint

        Parameters
        ----------
        *urls : str
            URLs to load skills from.
        source : Optional[str]
            Custom source identifier for the skills.

        Returns:
        -------
        AgentsExecutionEnvironment
            The environment to register the skills.

        Example:
        -------
        >>> env = AgentsExecutionEnvironment.get_execution_environment()
        >>> env.add_skills_from_urls("https://example.com/skills.zip")
        """
        manager = self._get_or_create_skill_manager()
        for url in urls:
            manager.add_skills_from_url(url, source=source)
        return self

    def get_skill_manager(self) -> AgentSkillManager:
        """Get the skill manager for this environment.

        Returns:
        -------
        AgentSkillManager
            The skill manager.

        Raises:
        ------
        ValueError
            If no skills have been registered.
        """
        if not hasattr(self, "_skill_manager") or self._skill_manager is None:
            msg = "No skills have been registered. Use add_skills_from_* methods first."
            raise ValueError(msg)
        return self._skill_manager

    def _get_or_create_skill_manager(self) -> AgentSkillManager:
        """Get or create the skill manager.

        Returns:
        -------
        AgentSkillManager
            The skill manager.
        """
        if not hasattr(self, "_skill_manager") or self._skill_manager is None:
            self._skill_manager = AgentSkillManager()
        return self._skill_manager
