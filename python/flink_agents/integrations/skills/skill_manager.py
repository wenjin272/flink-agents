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
from typing import Any, Dict, List

from pydantic import ConfigDict, Field
from typing_extensions import override

from flink_agents.api.skills.skill_manager import BaseAgentSkillManager, RegisteredSkill
from flink_agents.integrations.skills.repository.filesystem_repository import (
    FileSystemSkillRepository,
)
from flink_agents.integrations.skills.skill_prompt_provider import SkillPromptProvider


class AgentSkillManager(BaseAgentSkillManager):
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
        **kwargs: Any,
    ) -> None:
        """Initialize the AgentSkillManager.

        Args:
            paths: Optional list of filesystem paths to  load skills from.
            resources: Optional list of Python package resources to load skills from.
            urls: Optional list of URLs to load skills from.
            kwargs: Additional keyword arguments to pass to the constructor.
        """
        super().__init__(paths=paths, resources=resources, urls=urls, **kwargs)
        self._load_skills_from_paths()
        self._load_skills_from_urls()
        self._load_skills_from_resources()

    @override
    def get_skill(self, name: str) -> RegisteredSkill:
        if name not in self.skills:
            msg = f"Skill {name} not found, available skill names are: {self.skills.keys()}"
            raise ValueError(msg)
        return self.skills[name]

    @override
    def load_skill_resource(self, skill_name: str, resource_path: str) -> str | None:
        """Load a specific resource from a skill.

        Args:
            skill_name: The skill ID.
            resource_path: The relative path of the resource.

        Returns:
            The resource content, or None if not found.
        """
        skill = self.get_skill(skill_name)
        if skill is None:
            return None

        return skill.get_resource(resource_path)

    @override
    @property
    def size(self) -> int:
        """Get the number of registered skills.

        Returns:
            The number of skills.
        """
        return len(self.skills)

    @override
    def generate_discovery_prompt(self, *names: str) -> str:
        """Generate a system prompt for skill discovery.

        This prompt includes only skill names and descriptions (~100 tokens per skill).

        Args:
            *names: The names of the skills to activate.

        Returns:
            The discovery prompt.
        """
        if self.size == 0:
            return ""

        skill_list = []
        for name in names:
            skill = self.get_skill(name)
            skill_list.append(
                SkillPromptProvider.AVAILABLE_SKILL_TEMPLATE.format(
                    name=skill.name, description=skill.description
                )
            )

        return (
            SkillPromptProvider.SKILL_DISCOVERY_PROMPT.format()
            + ("".join(skill_list))
            + SkillPromptProvider.AVAILABLE_SKILLS_TAG_END
        )

    def _load_skills_from_paths(self) -> None:
        """Add skills from a filesystem path."""
        for path in self.paths:
            repo = FileSystemSkillRepository(path)
            for skill in repo.get_skills():
                self.skills[skill.name] = RegisteredSkill(agent_skill=skill, repo=repo)

    def _load_skills_from_resources(self) -> List[str]:
        """Add skills from python package resources."""
        # TODO: Implement

    def _load_skills_from_urls(self) -> List[str]:
        """Add skills from remote URLs."""
        # TODO: Implement
