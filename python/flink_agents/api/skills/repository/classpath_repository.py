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
"""Classpath Skill Repository implementation.

This module provides ClasspathSkillRepository which loads skills from
Python package resources (similar to JAR resources in Java).
"""
from typing import List

from importlib_resources import files

from flink_agents.api.skills.agent_skill import AgentSkill
from flink_agents.api.skills.repository.skill_repository import (
    SkillRepository,
    SkillRepositoryInfo,
)
from flink_agents.api.skills.skill_parser import SkillParser


class ClasspathSkillRepository(SkillRepository):
    """Classpath-based implementation of SkillRepository.

    This repository loads skills from Python package resources, similar to
    loading from JAR resources in Java. It uses importlib_resources to
    access package resources.

    Directory structure in the package:

    package/
    ├── skills/
    │   ├── skill-name-1/
    │   │   ├── SKILL.md
    │   │   └── scripts/
    │   │       └── run.sh
    │   └── skill-name-2/
    │       └── SKILL.md
    └── __init__.py

    Example:
    -------
    >>> repo = ClasspathSkillRepository("my_package.skills")
    >>> skill = repo.get_skill("my-skill")
    """

    SKILL_MD_FILE = "SKILL.md"

    def __init__(
        self,
        package_path: str,
        source: str | None = None,
    ) -> None:
        """Create a ClasspathSkillRepository.

        Parameters
        ----------
        package_path : str
            The Python package path containing skills (e.g., "my_package.skills").
        source : Optional[str]
            Custom source identifier for skills.

        Raises:
        ------
        ValueError
            If package_path is None or empty, or if the package doesn't exist.
        """
        if not package_path:
            raise ValueError("Package path cannot be None or empty")

        self._package_path = package_path
        self._source = source

        # Validate package exists
        try:
            self._package_files = files(package_path)
        except (ImportError, TypeError) as e:
            raise ValueError(f"Package not found: {package_path}") from e

    @property
    def package_path(self) -> str:
        """Get the package path.

        Returns:
        -------
        str
            The package path.
        """
        return self._package_path

    def get_skill(self, name: str) -> AgentSkill | None:
        """Get a skill by name.

        Parameters
        ----------
        name : str
            The skill name.

        Returns:
        -------
        Optional[AgentSkill]
            The skill, or None if not found.
        """
        skill_md_path = f"{name}/{self.SKILL_MD_FILE}"

        try:
            skill_md_file = self._package_files.joinpath(skill_md_path)
            if not skill_md_file.is_file():
                return None

            skill_md_content = skill_md_file.read_text()

            # Load resources
            resources = self._load_resources(name)

            # Parse and create skill
            return SkillParser.parse_skill(
                skill_md_content, resources, source=self.get_source()
            )

        except Exception:
            return None

    def get_all_skill_names(self) -> List[str]:
        """Get all skill names in this repository.

        Returns:
        -------
        List[str]
            List of skill names.
        """
        skill_names = []

        try:
            for entry in self._package_files.iterdir():
                if entry.is_dir():
                    skill_md = entry.joinpath(self.SKILL_MD_FILE)
                    if skill_md.is_file():
                        skill_names.append(entry.name)
        except Exception:
            pass

        return sorted(skill_names)

    def get_all_skills(self) -> List[AgentSkill]:
        """Get all skills in this repository.

        Returns:
        -------
        List[AgentSkill]
            List of all skills.
        """
        skills = []
        for skill_name in self.get_all_skill_names():
            skill = self.get_skill(skill_name)
            if skill is not None:
                skills.append(skill)
        return skills

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
        try:
            skill_md_path = f"{name}/{self.SKILL_MD_FILE}"
            skill_md_file = self._package_files.joinpath(skill_md_path)
            return skill_md_file.is_file()
        except Exception:
            return False

    def get_repository_info(self) -> SkillRepositoryInfo:
        """Get information about this repository.

        Returns:
        -------
        SkillRepositoryInfo
            Repository information.
        """
        return SkillRepositoryInfo(
            repo_type="classpath",
            location=self._package_path,
            writeable=False,
        )

    def get_source(self) -> str:
        """Get the source identifier for skills from this repository.

        Returns:
        -------
        str
            Source identifier.
        """
        if self._source is not None:
            return self._source
        return f"classpath-{self._package_path}"

    def _load_resources(self, skill_name: str) -> dict[str, str]:
        """Load all resources for a skill.

        Parameters
        ----------
        skill_name : str
            The skill name.

        Returns:
        -------
        Dict[str, str]
            Map of relative path to content.
        """
        resources = {}

        try:
            skill_dir = self._package_files.joinpath(skill_name)
            resources = self._walk_and_load(skill_dir, "")
        except Exception:
            pass

        return resources

    def _walk_and_load(self, dir_path, relative_prefix: str) -> dict[str, str]:
        """Walk directory and load all files.

        Parameters
        ----------
        dir_path : Traversable
            Directory to walk.
        relative_prefix : str
            Relative path prefix.

        Returns:
        -------
        Dict[str, str]
            Map of relative path to content.
        """
        resources = {}

        try:
            for entry in dir_path.iterdir():
                if entry.is_dir():
                    # Recursively walk subdirectories
                    subdir_prefix = (
                        f"{relative_prefix}/{entry.name}"
                        if relative_prefix
                        else entry.name
                    )
                    sub_resources = self._walk_and_load(entry, subdir_prefix)
                    resources.update(sub_resources)

                elif entry.is_file():
                    # Skip SKILL.md
                    if entry.name == self.SKILL_MD_FILE:
                        continue

                    # Build relative path
                    relative_path = (
                        f"{relative_prefix}/{entry.name}"
                        if relative_prefix
                        else entry.name
                    )

                    try:
                        content = entry.read_text()
                        resources[relative_path] = content
                    except (UnicodeDecodeError, Exception):
                        # Skip binary files or unreadable files
                        pass

        except Exception:
            pass

        return resources
