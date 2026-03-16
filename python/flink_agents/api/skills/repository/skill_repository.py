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
"""Skill Repository interface for loading and managing skills.

This module provides the abstract SkillRepository interface and its implementations
for loading skills from different sources (filesystem, classpath, URL).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from flink_agents.api.skills.agent_skill import AgentSkill


@dataclass
class SkillRepositoryInfo:
    """Information about a skill repository.

    Attributes:
    ----------
    repo_type : str
        The type of repository (e.g., "filesystem", "classpath", "url").
    location : str
        The location of the repository (e.g., path, URL).
    writeable : bool
        Whether the repository supports write operations.
    """

    repo_type: str
    location: str
    writeable: bool


class SkillRepository(ABC):
    """Abstract interface for skill repositories.

    A SkillRepository is responsible for loading and optionally storing skills
    from a specific source (filesystem, classpath, URL, etc.).

    Each skill is stored in its own subdirectory containing a SKILL.md file
    and optional resource files:

    baseDir/
    ├── skill-name-1/
    │   ├── SKILL.md          # Required: Entry file with YAML frontmatter
    │   ├── references/       # Optional: Reference documentation
    │   ├── examples/         # Optional: Example files
    │   └── scripts/          # Optional: Script files
    └── skill-name-2/
        └── SKILL.md
    """

    @abstractmethod
    def get_skill(self, name: str) -> AgentSkill | None:
        """Get a skill by name.

        Parameters
        ----------
        name : str
            The skill name (must match the directory name and frontmatter name).

        Returns:
        -------
        Optional[AgentSkill]
            The skill, or None if not found.
        """

    @abstractmethod
    def get_all_skill_names(self) -> List[str]:
        """Get all skill names in this repository.

        Returns:
        -------
        List[str]
            List of skill names.
        """

    @abstractmethod
    def get_all_skills(self) -> List[AgentSkill]:
        """Get all skills in this repository.

        Returns:
        -------
        List[AgentSkill]
            List of all skills.
        """

    @abstractmethod
    def skill_exists(self, name: str) -> bool:
        """Check if a skill exists in this repository.

        Parameters
        ----------
        name : str
            The skill name.

        Returns:
        -------
        bool
            True if the skill exists.
        """

    @abstractmethod
    def get_repository_info(self) -> SkillRepositoryInfo:
        """Get information about this repository.

        Returns:
        -------
        SkillRepositoryInfo
            Repository information.
        """

    @abstractmethod
    def get_source(self) -> str:
        """Get the source identifier for skills from this repository.

        Returns:
        -------
        str
            Source identifier.
        """

    def save(self, skills: List[AgentSkill], force: bool = False) -> bool:
        """Save skills to this repository.

        Parameters
        ----------
        skills : List[AgentSkill]
            Skills to save.
        force : bool
            Whether to overwrite existing skills.

        Returns:
        -------
        bool
            True if successful, False otherwise.

        Raises:
        ------
        NotImplementedError
            If the repository does not support write operations.
        """
        raise NotImplementedError("This repository does not support write operations")

    def delete(self, skill_name: str) -> bool:
        """Delete a skill from this repository.

        Parameters
        ----------
        skill_name : str
            Name of the skill to delete.

        Returns:
        -------
        bool
            True if successful, False otherwise.

        Raises:
        ------
        NotImplementedError
            If the repository does not support write operations.
        """
        raise NotImplementedError("This repository does not support write operations")

    def is_writeable(self) -> bool:
        """Check if this repository supports write operations.

        Returns:
        -------
        bool
            True if writeable.
        """
        return self.get_repository_info().writeable
