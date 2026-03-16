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
    >>> skill = repo.get_skill("my-skill")
    """

    SKILL_MD_FILE = "SKILL.md"

    def __init__(
        self,
        base_dir: Path | str,
        writeable: bool = True,
        source: str | None = None,
        skip_dirs: Set[str] | None = None,
        skip_patterns: Set[str] | None = None,
    ) -> None:
        """Create a FileSystemSkillRepository.

        Parameters
        ----------
        base_dir : Path | str
            The base directory containing skill subdirectories.
        writeable : bool
            Whether the repository supports write operations.
        source : Optional[str]
            Custom source identifier for skills.
        skip_dirs : Optional[Set[str]]
            Directory names to skip when loading resources.
        skip_patterns : Optional[Set[str]]
            File patterns to skip when loading resources.

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

        self._writeable = writeable
        self._source = source
        self._skip_dirs = skip_dirs if skip_dirs is not None else DEFAULT_SKIP_DIRS
        self._skip_patterns = (
            skip_patterns if skip_patterns is not None else DEFAULT_SKIP_PATTERNS
        )

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
        skill_dir = self._base_dir / name
        return skill_dir.is_dir() and (skill_dir / self.SKILL_MD_FILE).exists()

    def get_repository_info(self) -> SkillRepositoryInfo:
        """Get information about this repository.

        Returns:
        -------
        SkillRepositoryInfo
            Repository information.
        """
        return SkillRepositoryInfo(
            repo_type="filesystem",
            location=str(self._base_dir),
            writeable=self._writeable,
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

        # Build default source from path
        parent = self._base_dir.parent.name
        dir_name = self._base_dir.name

        if parent:
            return f"filesystem-{parent}_{dir_name}"
        return f"filesystem-{dir_name}"

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
        """
        if not self._writeable:
            return False

        if not skills:
            return False

        for skill in skills:
            skill_dir = self._base_dir / skill.name

            # Check if skill already exists
            if skill_dir.exists() and not force:
                continue

            # Create skill directory
            skill_dir.mkdir(parents=True, exist_ok=True)

            # Write SKILL.md
            skill_md_content = SkillParser.generate_skill_md(skill)
            (skill_dir / self.SKILL_MD_FILE).write_text(skill_md_content)

            # Write resources
            for resource_path, content in skill.resources.items():
                resource_file = skill_dir / resource_path
                resource_file.parent.mkdir(parents=True, exist_ok=True)
                resource_file.write_text(content)

        return True

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
        """
        if not self._writeable:
            return False

        import shutil

        skill_dir = self._base_dir / skill_name
        if not skill_dir.exists():
            return False

        shutil.rmtree(skill_dir)
        return True

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

            # Load resources
            resources = self._load_resources(skill_dir)

            # Parse and create skill
            skill = SkillParser.parse_skill(
                skill_md_content, resources, source=self.get_source()
            )

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
