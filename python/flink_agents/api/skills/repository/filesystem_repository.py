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
"""File System Skill Repository implementation.

This module provides FileSystemSkillRepository which loads skills from
a local file system directory structure.
"""
import os
from pathlib import Path
from typing import List, Set

from flink_agents.api.skills.agent_skill import AgentSkill
from flink_agents.api.skills.repository.skill_repository import (
    SkillRepository,
    SkillRepositoryInfo,
)
from flink_agents.api.skills.skill_parser import SkillParser

# Default directories to skip when loading skill resources
DEFAULT_SKIP_DIRS = {
    "__pycache__",
    ".git",
    ".github",
    ".idea",
    ".vscode",
    "node_modules",
    ".pytest_cache",
    ".ruff_cache",
}

# Default file patterns to skip
DEFAULT_SKIP_PATTERNS = {
    ".pyc",
    ".pyo",
    ".gitignore",
    ".DS_Store",
    "Thumbs.db",
}


class FileSystemSkillRepository(SkillRepository):
    """File system based implementation of SkillRepository.

    This repository stores skills in a local file system directory structure
    where each skill is stored in its own subdirectory containing a SKILL.md
    file and optional resource files.

    Directory structure:

    baseDir/
    ├── skill-name-1/
    │   ├── SKILL.md          # Required: Entry file with YAML frontmatter
    │   ├── references/       # Optional: Reference documentation
    │   ├── examples/         # Optional: Example files
    │   └── scripts/          # Optional: Script files
    └── skill-name-2/
        └── SKILL.md

    Example:
    -------
    >>> from pathlib import Path
    >>> repo = FileSystemSkillRepository(Path("/path/to/skills"))
    >>> skill = repo.load_content("my-skill")
    """

    SKILL_MD_FILE = "SKILL.md"

    def __init__(
        self,
        base_dir: Path | str,
    ) -> None:
        """Create a FileSystemSkillRepository.

        Parameters
        ----------
        base_dir : Path | str
            The base directory containing skill subdirectories.

        Raises:
        ------
        ValueError
            If base_dir is None, doesn't exist, or is not a directory.
        """
        if base_dir is None:
            raise ValueError("Base directory cannot be None")

        # Convert to Path and normalize
        self._base_dir = Path(base_dir).resolve()

        # Validate directory exists
        if not self._base_dir.exists():
            raise ValueError(f"Base directory does not exist: {self._base_dir}")

        # Validate it's a directory
        if not self._base_dir.is_dir():
            raise ValueError(f"Base directory is not a directory: {self._base_dir}")

    @property
    def base_dir(self) -> Path:
        """Get the base directory.

        Returns:
        -------
        Path
            The base directory path.
        """
        return self._base_dir
    
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
        skill_dir = self._base_dir / name
        skill_md_path = skill_dir / self.SKILL_MD_FILE

        if not skill_md_path.exists():
            return None

        return self._load_skill(skill_dir)
    
    def get_skills(self) -> List[AgentSkill]:
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

    def get_all_skill_names(self) -> List[str]:
        """Get all skill names in this repository.

        Returns:
        -------
        List[str]
            List of skill names.
        """
        skill_names = []
        for entry in self._base_dir.iterdir():
            if entry.is_dir() and (entry / self.SKILL_MD_FILE).exists():
                skill_names.append(entry.name)
        return sorted(skill_names)


    def load_content(self, name: str) -> AgentSkill | None:
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
        skill_dir = self._base_dir / name
        skill_md_path = skill_dir / self.SKILL_MD_FILE

        if not skill_md_path.exists():
            return None

        return self._load_skill(skill_dir)

    def get_all_skill_names(self) -> List[str]:
        """Get all skill names in this repository.

        Returns:
        -------
        List[str]
            List of skill names.
        """
        skill_names = []
        for entry in self._base_dir.iterdir():
            if entry.is_dir() and (entry / self.SKILL_MD_FILE).exists():
                skill_names.append(entry.name)
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
            skill = self.load_content(skill_name)
            if skill is not None:
                skills.append(skill)
        return skills

    def _load_skill(self, skill_dir: Path) -> AgentSkill | None:
        """Load a skill from a directory.

        Parameters
        ----------
        skill_dir : Path
            Path to the skill directory.

        Returns:
        -------
        Optional[AgentSkill]
            The loaded skill, or None if loading failed.
        """
        skill_md_path = skill_dir / self.SKILL_MD_FILE

        if not skill_md_path.exists():
            return None

        try:
            # Read SKILL.md
            skill_md_content = skill_md_path.read_text()

            # Parse and create skill
            skill = SkillParser.parse_skill(skill_md_content, self)
            skill._repo = self

            # Validate skill name matches directory name
            if skill.name != skill_dir.name:
                # Log warning but still return the skill
                pass

            return skill

        except Exception:
            return None

    def _load_resources(self, skill_dir: Path) -> dict[str, str]:
        """Load all resources from a skill directory.

        Parameters
        ----------
        skill_dir : Path
            Path to the skill directory.

        Returns:
        -------
        Dict[str, str]
            Map of relative path to content.
        """
        resources = {}

        for root, dirs, files in os.walk(skill_dir):
            root_path = Path(root)

            # Skip hidden directories and configured skip directories
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".") and d not in self._skip_dirs
            ]

            for file_name in files:
                # Skip SKILL.md (handled separately)
                if file_name == self.SKILL_MD_FILE:
                    continue

                # Skip files matching skip patterns
                if any(file_name.endswith(pattern) for pattern in self._skip_patterns):
                    continue

                file_path = root_path / file_name
                relative_path = str(file_path.relative_to(skill_dir))

                try:
                    # Try to read as text
                    content = file_path.read_text()
                    resources[relative_path] = content
                except UnicodeDecodeError:
                    # Skip binary files
                    pass
                except Exception:
                    # Skip files that can't be read
                    pass

        return resources
