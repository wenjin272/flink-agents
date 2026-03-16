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
from typing import Dict, List, Set

from flink_agents.api.skills.agent_skill import AgentSkill, RegisteredSkill
from flink_agents.api.skills.repository.classpath_repository import (
    ClasspathSkillRepository,
)
from flink_agents.api.skills.repository.filesystem_repository import (
    FileSystemSkillRepository,
)
from flink_agents.api.skills.repository.skill_repository import SkillRepository
from flink_agents.api.skills.repository.url_repository import UrlSkillRepository
from flink_agents.api.skills.skill_registry import SkillRegistry


class AgentSkillManager:
    """Unified manager for loading, parsing, and managing skills.

    This manager provides a high-level interface for:
    - Loading skills from various sources (filesystem, classpath, URL)
    - Registering and activating skills
    - Generating system prompts for LLM integration

    Progressive Disclosure Pattern:
    - Discovery: Load only name/description at startup (~100 tokens)
    - Activation: Load full SKILL.md when skill matches task
    - Execution: Load resources/scripts only when needed

    Example:
    -------
    >>> manager = AgentSkillManager()
    >>> manager.add_skills_from_path("/path/to/skills")
    >>> manager.add_skills_from_resources("my_package.skills")
    >>> manager.add_skills_from_url("https://example.com/skills.zip")
    >>> skill = manager.get_skill("my-skill")
    >>> manager.activate_skill("my-skill")
    >>> prompt = manager.generate_skills_prompt()
    """

    # System prompt template for skills discovery
    SKILL_DISCOVERY_PROMPT = """## Available Skills

The following skills are available. Use `load_skill` tool to load a skill's full content when you need it.

{skill_list}

## How to Use Skills

1. First, review the skill descriptions above to find relevant skills
2. Use `load_skill` tool with the skill name to load the full skill content
3. Follow the skill's instructions to complete the task
"""

    # System prompt template for active skill
    SKILL_ACTIVE_PROMPT = """## Active Skill: {skill_name}

{skill_content}

## Available Resources

{resource_list}

## How to Use Resources

Use `load_skill_resource` tool with the resource path to load specific resource content.
"""

    def __init__(self) -> None:
        """Initialize the AgentSkillManager."""
        self._registry = SkillRegistry()
        self._repositories: List[SkillRepository] = []

    @property
    def registry(self) -> SkillRegistry:
        """Get the skill registry.

        Returns:
        -------
        SkillRegistry
            The skill registry.
        """
        return self._registry

    def add_skills_from_path(
        self,
        path: Path | str,
        source: str | None = None,
    ) -> List[str]:
        """Add skills from a filesystem path.

        Parameters
        ----------
        path : Path | str
            Path to a directory containing skill subdirectories.
        source : Optional[str]
            Custom source identifier.

        Returns:
        -------
        List[str]
            List of loaded skill names.
        """
        repo = FileSystemSkillRepository(path, writeable=False, source=source)
        return self._register_skills_from_repo(repo)

    def add_skills_from_resources(
        self,
        package_path: str,
        source: str | None = None,
    ) -> List[str]:
        """Add skills from Python package resources.

        Parameters
        ----------
        package_path : str
            Python package path containing skills (e.g., "my_package.skills").
        source : Optional[str]
            Custom source identifier.

        Returns:
        -------
        List[str]
            List of loaded skill names.
        """
        repo = ClasspathSkillRepository(package_path, source=source)
        return self._register_skills_from_repo(repo)

    def add_skills_from_url(
        self,
        url: str,
        source: str | None = None,
    ) -> List[str]:
        """Add skills from a remote URL.

        Parameters
        ----------
        url : str
            URL pointing to a zip file or skill directory.
        source : Optional[str]
            Custom source identifier.

        Returns:
        -------
        List[str]
            List of loaded skill names.
        """
        repo = UrlSkillRepository(url, source=source)
        return self._register_skills_from_repo(repo)

    def add_repository(self, repo: SkillRepository) -> List[str]:
        """Add skills from a custom repository.

        Parameters
        ----------
        repo : SkillRepository
            The repository to add.

        Returns:
        -------
        List[str]
            List of loaded skill names.
        """
        return self._register_skills_from_repo(repo)

    def register_skill(self, skill: AgentSkill) -> None:
        """Register a skill directly.

        Parameters
        ----------
        skill : AgentSkill
            The skill to register.
        """
        skill_id = skill.skill_id
        registered = RegisteredSkill(skill_id=skill_id)
        self._registry.register_skill(skill_id, skill, registered)

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

    def get_skill(self, skill_id: str) -> AgentSkill | None:
        """Get a skill by ID.

        Parameters
        ----------
        skill_id : str
            The skill ID (name_source format) or just the skill name.

        Returns:
        -------
        Optional[AgentSkill]
            The skill, or None if not found.
        """
        # Try exact match first
        skill = self._registry.get_skill(skill_id)
        if skill is not None:
            return skill

        # Try to find by name only
        for sid in self._registry.get_skill_ids():
            if sid.startswith(f"{skill_id}_"):
                return self._registry.get_skill(sid)

        return None

    def get_skill_by_name(self, name: str) -> AgentSkill | None:
        """Get a skill by name (first match).

        Parameters
        ----------
        name : str
            The skill name.

        Returns:
        -------
        Optional[AgentSkill]
            The skill, or None if not found.
        """
        for skill_id in self._registry.get_skill_ids():
            if skill_id.startswith(f"{name}_"):
                return self._registry.get_skill(skill_id)

        return None

    def get_all_skills(self) -> Dict[str, AgentSkill]:
        """Get all registered skills.

        Returns:
        -------
        Dict[str, AgentSkill]
            Map of skill ID to skill.
        """
        return self._registry.get_all_skills()

    def get_all_skill_ids(self) -> Set[str]:
        """Get all skill IDs.

        Returns:
        -------
        Set[str]
            Set of skill IDs.
        """
        return self._registry.get_skill_ids()

    def get_all_skill_names(self) -> Set[str]:
        """Get all unique skill names.

        Returns:
        -------
        Set[str]
            Set of skill names.
        """
        names = set()
        for skill in self._registry.get_all_skills().values():
            names.add(skill.name)
        return names

    def skill_exists(self, skill_id: str) -> bool:
        """Check if a skill exists.

        Parameters
        ----------
        skill_id : str
            The skill ID.

        Returns:
        -------
        bool
            True if the skill exists.
        """
        return self._registry.exists(skill_id)

    def activate_skill(self, skill_id: str) -> bool:
        """Activate a skill.

        When a skill is active, its full content is loaded and available
        for the LLM to use.

        Parameters
        ----------
        skill_id : str
            The skill ID.

        Returns:
        -------
        bool
            True if the skill was activated, False if not found.
        """
        skill = self.get_skill(skill_id)
        if skill is None:
            return False

        self._registry.set_skill_active(skill.skill_id, True)
        return True

    def deactivate_skill(self, skill_id: str) -> bool:
        """Deactivate a skill.

        Parameters
        ----------
        skill_id : str
            The skill ID.

        Returns:
        -------
        bool
            True if the skill was deactivated, False if not found.
        """
        skill = self.get_skill(skill_id)
        if skill is None:
            return False

        self._registry.set_skill_active(skill.skill_id, False)
        return True

    def deactivate_all_skills(self) -> None:
        """Deactivate all skills.

        This is typically called at the start of each agent call
        to ensure a clean state.
        """
        self._registry.set_all_skills_active(False)

    def is_skill_active(self, skill_id: str) -> bool:
        """Check if a skill is active.

        Parameters
        ----------
        skill_id : str
            The skill ID.

        Returns:
        -------
        bool
            True if the skill is active.
        """
        registered = self._registry.get_registered_skill(skill_id)
        if registered is None:
            # Try to find by name
            for sid, reg in self._registry.get_all_registered_skills().items():
                if sid.startswith(f"{skill_id}_"):
                    return reg.active
            return False
        return registered.active

    def get_active_skills(self) -> Dict[str, AgentSkill]:
        """Get all active skills.

        Returns:
        -------
        Dict[str, AgentSkill]
            Map of skill ID to active skills.
        """
        return self._registry.get_active_skills()

    def remove_skill(self, skill_id: str) -> bool:
        """Remove a skill from the manager.

        Parameters
        ----------
        skill_id : str
            The skill ID.

        Returns:
        -------
        bool
            True if the skill was removed.
        """
        return self._registry.remove_skill(skill_id)

    def clear(self) -> None:
        """Clear all registered skills."""
        self._registry.clear()
        self._repositories.clear()

    def generate_discovery_prompt(self) -> str:
        """Generate a system prompt for skill discovery.

        This prompt includes only skill names and descriptions (~100 tokens per skill).

        Returns:
        -------
        str
            The discovery prompt.
        """
        skill_list = []
        for skill_id, skill in self._registry.get_all_skills().items():
            skill_list.append(f"- **{skill.name}**: {skill.description}")

        skill_list_str = "\n".join(skill_list) if skill_list else "No skills available."

        return self.SKILL_DISCOVERY_PROMPT.format(skill_list=skill_list_str)

    def generate_active_skill_prompt(self, skill_id: str) -> str | None:
        """Generate a system prompt for an active skill.

        This prompt includes the full skill content and available resources.

        Parameters
        ----------
        skill_id : str
            The skill ID.

        Returns:
        -------
        Optional[str]
            The active skill prompt, or None if skill not found.
        """
        skill = self.get_skill(skill_id)
        if skill is None:
            return None

        # Build resource list
        resource_paths = skill.get_resource_paths()
        if resource_paths:
            resource_list = "\n".join(f"- `{path}`" for path in sorted(resource_paths))
        else:
            resource_list = "No resources available."

        return self.SKILL_ACTIVE_PROMPT.format(
            skill_name=skill.name,
            skill_content=skill.skill_content,
            resource_list=resource_list,
        )

    def generate_skills_prompt(self, include_active: bool = True) -> str:
        """Generate a combined system prompt for skills.

        This includes both the discovery prompt and active skill prompts.

        Parameters
        ----------
        include_active : bool
            Whether to include active skill content.

        Returns:
        -------
        str
            The combined skills prompt.
        """
        prompts = [self.generate_discovery_prompt()]

        if include_active:
            for skill_id in self._registry.get_active_skill_ids():
                active_prompt = self.generate_active_skill_prompt(skill_id)
                if active_prompt:
                    prompts.append(active_prompt)

        return "\n\n".join(prompts)

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
        return self._registry.size()

    def is_empty(self) -> bool:
        """Check if no skills are registered.

        Returns:
        -------
        bool
            True if no skills are registered.
        """
        return self._registry.is_empty()
