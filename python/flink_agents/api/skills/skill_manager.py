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
from typing import List

from typing_extensions import override

from flink_agents.api.resource import Resource, ResourceType
from flink_agents.api.skills.agent_skill import AgentSkill
from flink_agents.api.skills.skill_repository import SkillRepository


class RegisteredSkill:
    """A wrapper that associates an AgentSkill with its source repository.

    This class provides lazy activation for skill resources, loading them
    only when first needed (e.g., when get_resource or get_resource_paths
    is called).

    Attributes:
        agent_skill: The wrapped agent skill instance.
        repo: The repository from which the skill was loaded.
        active: Whether the skill's resources have been loaded.
    """

    agent_skill: AgentSkill
    repo: SkillRepository
    active: bool = False

    def __init__(self, agent_skill: AgentSkill, repo: SkillRepository) -> None:
        """Initializes a new registered skill.

        Args:
            agent_skill: The agent skill to register.
            repo: The repository the agent skill load from.
        """
        self.agent_skill = agent_skill
        self.repo = repo

    @property
    def name(self) -> str:
        """Get the name of the skill."""
        return self.agent_skill.name

    @property
    def description(self) -> str:
        """Get the description of the skill."""
        return self.agent_skill.description

    @property
    def content(self) -> str:
        """Get the content of the skill."""
        return self.agent_skill.content

    def get_resource(self, resource_path: str) -> str:
        """Get the resource fo the skill."""
        self._activate()
        return self.agent_skill.get_resource(resource_path)

    def get_resource_paths(self) -> List[str]:
        """Get all the resource relative paths of the skill."""
        self._activate()
        return self.agent_skill.get_resource_paths()

    def _activate(self) -> None:
        if not self.active:
            self.agent_skill.resources = self.repo.get_resources(self.agent_skill.name)
            self.active = True


class BaseAgentSkillManager(Resource, ABC):
    """Unified manager for loading, parsing, and managing skills.

    This manager provides a high-level interface for loading skills from
    various sources, registering and activating skills, and generating
    system prompts for LLM integration.

    Progressive Disclosure Pattern:
    - Discovery: Load only name/description at startup (~100 tokens)
    - Activation: Load full SKILL.md when skill matches task
    - Execution: Load resources/scripts only when needed
    """

    @classmethod
    @override
    def resource_type(cls) -> ResourceType:
        return ResourceType.SKILL

    @abstractmethod
    def generate_discovery_prompt(self, *names: str) -> str:
        """Generate a system prompt for skill discovery.

        This prompt includes only skill names and descriptions (~100 tokens per skill).

        Args:
            *names: The names of the skills to activate.

        Returns:
            The discovery prompt.
        """

    def get_skill(self, name: str) -> RegisteredSkill:
        """Get a registered skill by name.

        The registered skill contains both the agent skill and the skill
        repo it from.

        Args:
            name: The name of the skill to get.

        Returns:
            The registered skill.
        """

    def load_skill_resource(self, skill_name: str, resource_path: str) -> str | None:
        """Load a specified resource of a skill.

        Args:
            skill_name: The name of the skill.
            resource_path: The relative path to the resource to load.

        Returns:
            The content of the resource.
        """

    @property
    @abstractmethod
    def size(self) -> int:
        """Get the number of skills in managed by this skill manager."""


SKILL_MANAGER = "_skill_manager"
