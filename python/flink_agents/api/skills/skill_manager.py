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
"""Agent Skill Manager for unified skill management.

This module provides the AgentSkillManager class which is responsible for:
- Loading skills from various sources (filesystem, classpath, URL)
- Managing skill registration and activation
- Generating system prompts for LLM
"""
from pathlib import Path
from typing import Dict, List

from pydantic import Field

from flink_agents.api.resource import Resource, ResourceType
from flink_agents.api.skills.agent_skill import AgentSkill
from flink_agents.api.skills.prompt import Prompt
from flink_agents.api.skills.repository.filesystem_repository import (
    FileSystemSkillRepository,
)
from flink_agents.api.skills.repository.skill_repository import SkillRepository


class AgentSkillManager(Resource):
    """Unified manager for loading, parsing, and managing skills.

    This manager provides a high-level interface for:
    - Loading skills from various sources (filesystem, classpath, URL)
    - Registering and activating skills
    - Generating system prompts for LLM integration

    Progressive Disclosure Pattern:
    - Discovery: Load only name/description at startup (~100 tokens)
    - Activation: Load full SKILL.md when skill matches task
    - Execution: Load resources/scripts only when needed
    """
    
    paths: List[Path | str] | None = Field(default=None)
    resources: List[str] | None = Field(default=None)
    urls: List[str] | None = Field(default=None)
    _skills: Dict[str, AgentSkill] = Field(default=None, exclude=True)
    
    def __init__(self, paths: List[Path | str] | None = None, resources: List[str] | None = None, urls: List[str] | None = None) -> None:
        """Initialize the AgentSkillManager."""
        super().__init__(paths=paths, resources=resources, urls=urls)
        
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
        if self._skills is None:
            self._skills = {}
            self._load_skills_from_paths()
            self._load_skills_from_resources()
            self._load_skills_from_urls()
            
        skill_list = []
        for name in names:
            skill = self._skills.get(name)
            skill_list.append(f"- **{skill.name}**: {skill.description}")

        skill_list_str = "\n".join(skill_list) if skill_list else "No skills available."

        return Prompt.SKILL_DISCOVERY_PROMPT.format(skill_list=skill_list_str)

    def _load_skills_from_paths(self) -> List[str]:
        """Add skills from a filesystem path."""
        for path in self.paths:
            repo = FileSystemSkillRepository(path)
        return self._register_skills_from_repo(repo)

    def _load_skills_from_resources(self) -> List[str]:
        """Add skills from Python package resources."""
        

    def _load_skills_from_urls(self) -> List[str]:
        """Add skills from a remote URL."""
    

    def _register_skills_from_repo(self, repo: SkillRepository) -> List[str]:
        """Register all skills from a repository.

        Parameters
        ----------
        repo : SkillRepository
            The repository to load from.

        Returns:
        -------
        List[str]
            List of loaded skill names.
        """
        self._repositories.append(repo)
        loaded_names = []

        for skill in repo.get_all_skills():
            self.register_skill(skill)
            loaded_names.append(skill.name)

        return loaded_names
    
    def get_skill(self, name: str) -> AgentSkill:
        if name not in self._skills:
            raise ValueError(f"Skill {name} not found, available skill names are: {self._skills.keys()}")
        return self._skills[name]

    def load_skill_resource(
        self, skill_id: str, resource_path: str
    ) -> str | None:
        """Load a specific resource from a skill.

        Parameters
        ----------
        skill_id : str
            The skill ID.
        resource_path : str
            The relative path of the resource.

        Returns:
        -------
        Optional[str]
            The resource content, or None if not found.
        """
        skill = self.get_skill(skill_id)
        if skill is None:
            return None

        return skill.get_resource(resource_path)

    def size(self) -> int:
        """Get the number of registered skills.

        Returns:
        -------
        int
            The number of skills.
        """
        return 0 if self._skills is None else len(self._skills)
