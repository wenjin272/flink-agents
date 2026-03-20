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
################################################################################
from pathlib import Path
from typing import Dict, List

from pydantic import Field, ConfigDict

from flink_agents.api.resource import Resource, ResourceType
from flink_agents.api.skills.agent_skill import AgentSkill
from flink_agents.api.skills.prompt import Prompt
from flink_agents.api.skills.repository.filesystem_repository import (
    FileSystemSkillRepository,
)
from flink_agents.api.skills.repository.skill_repository import (
    SkillRepository,
)


class RegisteredSkill:
    agent_skill: AgentSkill
    repo: SkillRepository
    active: bool = False

    def __init__(self, agent_skill: AgentSkill, repo: SkillRepository):
        self.agent_skill = agent_skill
        self.repo = repo

    @property
    def name(self) -> str:
        return self.agent_skill.name

    @property
    def description(self) -> str:
        return self.agent_skill.description

    @property
    def content(self) -> str:
        return self.agent_skill.content

    def get_resource(self, resource_path: str) -> str:
        self._activate()
        return self.agent_skill.get_resource(resource_path)

    def get_resource_paths(self) -> List[str]:
        self._activate()
        return self.agent_skill.get_resource_paths()

    def _activate(self):
        if not self.active:
            self.agent_skill.resources = self.repo.get_resources(self.agent_skill.name)
            self.active = True


class AgentSkillManager(Resource):
    """Unified manager for loading, parsing, and managing skills.

    This manager provides a high-level interface for loading skills from
    various sources, registering and activating skills, and generating
    system prompts for LLM integration.

    Progressive Disclosure Pattern:
    - Discovery: Load only name/description at startup (~100 tokens)
    - Activation: Load full SKILL.md when skill matches task
    - Execution: Load resources/scripts only when needed

    Attributes:
    ----------
    paths : Optional[List[Path | str]]
        List of filesystem paths to load skills from.
    resources : Optional[List[str]]
        List of Python package resources to load skills from.
    urls : Optional[List[str]]
        List of URLs to load skills from.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    paths: List[Path | str] | None = Field(default=None)
    resources: List[str] | None = Field(default=None)
    urls: List[str] | None = Field(default=None)
    skills: Dict[str, RegisteredSkill] = Field(default_factory=dict, exclude=True)

    def __init__(
        self,
        paths: List[Path | str] | None = None,
        resources: List[str] | None = None,
        urls: List[str] | None = None,
    ) -> None:
        """Initialize the AgentSkillManager.

        Args:
            paths: Optional list of filesystem paths to  load skills from.
            resources: Optional list of Python package resources to load skills from.
            urls: Optional list of URLs to load skills from.
        """
        super().__init__(paths=paths, resources=resources, urls=urls)
        self._load_skills_from_paths()

    @classmethod
    def resource_type(cls) -> ResourceType:
        return ResourceType.SKILL

    def generate_discovery_prompt(self, *names: str) -> str:
        """Generate a system prompt for skill discovery.

        This prompt includes only skill names and descriptions (~100 tokens per skill).

        Args:
            *names: The names of the skills to activate.

        Returns:
            The discovery prompt.
        """
        skill_list = []
        for name in names:
            skill = self.get_skill(name)
            skill_list.append(
                Prompt.AVAILABLE_SKILL_TEMPLATE.format(
                    name=skill.name, description=skill.description
                )
            )

        return (
            Prompt.SKILL_DISCOVERY_PROMPT.format()
            + ("".join(skill_list))
            + Prompt.AVAILABLE_SKILLS_TAG_END
        )

    def _load_skills_from_paths(self) -> None:
        """Add skills from a filesystem path."""
        for path in self.paths:
            repo = FileSystemSkillRepository(path)
            for skill in repo.get_skills():
                self.skills[skill.name] = RegisteredSkill(agent_skill=skill, repo=repo)

    def _load_skills_from_resources(self) -> List[str]:
        """Add skills from Python package resources."""

    def _load_skills_from_urls(self) -> List[str]:
        """Add skills from a remote URL."""

    def _register_skills_from_repo(self, repo: SkillRepository) -> List[str]:
        """Register all skills from a repository.

        Args:
            repo: The repository to load from.

        Returns:
            List of loaded skill names.
        """
        self._repositories.append(repo)
        loaded_names = []

        for skill in repo.get_all_skills():
            self.register_skill(skill)
            loaded_names.append(skill.name)

        return loaded_names

    def get_skill(self, name: str) -> RegisteredSkill:
        if name not in self.skills:
            raise ValueError(
                f"Skill {name} not found, available skill names are: {self.skills.keys()}"
            )
        return self.skills[name]

    def load_skill_resource(self, skill_id: str, resource_path: str) -> str | None:
        """Load a specific resource from a skill.

        Args:
            skill_id: The skill ID.
            resource_path: The relative path of the resource.

        Returns:
            The resource content, or None if not found.
        """
        skill = self.get_skill(skill_id)
        if skill is None:
            return None

        return skill.get_resource(resource_path)

    def size(self) -> int:
        """Get the number of registered skills.

        Returns:
            The number of skills.
        """
        return 0 if self._skills is None else len(self._skills)
