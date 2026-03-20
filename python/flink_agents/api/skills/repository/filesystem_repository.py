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
import logging
import os
from pathlib import Path
from typing import List, Set, Dict

from typing_extensions import override

from flink_agents.api.skills.agent_skill import AgentSkill
from flink_agents.api.skills.repository.skill_repository import (
    SkillRepository,
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
    """

    SKILL_MD_FILE = "SKILL.md"

    def __init__(
        self,
        base_dir: Path | str,
        skip_dirs: Set[str] | None = None,
        skip_patterns: Set[str] | None = None,
    ) -> None:
        """Create a FileSystemSkillRepository.

        Args:
            base_dir: The base directory containing skill subdirectories.
            skip_dirs: Optional set of directory names to skip.
            skip_patterns: Optional set of file patterns to skip.

        Raises:
            ValueError: If base_dir is None, doesn't exist, or is not a directory.
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

        self._skip_dirs = skip_dirs if skip_dirs is not None else DEFAULT_SKIP_DIRS
        self._skip_patterns = (
            skip_patterns if skip_patterns is not None else DEFAULT_SKIP_PATTERNS
        )

    @property
    def base_dir(self) -> Path:
        """Get the base directory.

        Returns:
            The base directory path.
        """
        return self._base_dir

    @override
    def get_skill(self, name: str) -> AgentSkill | None:
        """Get a skill by name.

        Args:
            name: The skill name.

        Returns:
            The skill, or None if not found.
        """
        skill_dir = self._base_dir / name
        skill_md_path = skill_dir / self.SKILL_MD_FILE

        if not skill_md_path.exists():
            return None

        return self._load_skill(skill_dir)

    @override
    def get_resources(self, name: str) -> Dict[str, str]:
        skill_dir = self._base_dir / name
        return self._load_resources(skill_dir)

    def get_skills(self) -> List[AgentSkill]:
        """Get all skills in this repository.

        Returns:
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
            List of skill names.
        """
        skill_names = []
        for entry in self._base_dir.iterdir():
            if entry.is_dir() and (entry / self.SKILL_MD_FILE).exists():
                skill_names.append(entry.name)
        return sorted(skill_names)

    def _load_skill(self, skill_dir: Path) -> AgentSkill | None:
        """Load a skill from a directory.

        Args:
            skill_dir: Path to the skill directory.

        Returns:
            The loaded skill, or None if loading failed.
        """
        skill_md_path = skill_dir / self.SKILL_MD_FILE

        if not skill_md_path.exists():
            return None

        try:
            # Read SKILL.md
            skill_md_content = skill_md_path.read_text()

            # Parse and create skill
            skill = SkillParser.parse_skill(skill_md_content)
            skill._repo = self

            # Validate skill name matches directory name
            if skill.name != skill_dir.name:
                # Log warning but still return the skill
                pass

            return skill

        except Exception as e:
            err_msg = f"Failed to load skill from {skill_dir}"
            raise ValueError(err_msg) from e

    def _load_resources(self, skill_dir: Path) -> dict[str, str]:
        """Load all resources from a skill directory.

        Args:
            skill_dir: Path to the skill directory.

        Returns:
            Map of relative path to content.
        """
        resources = {}

        for root, dirs, files in os.walk(skill_dir):
            root_path = Path(root)

            # Skip hidden directories and configured skip directories
            dirs[:] = [
                d for d in dirs if not d.startswith(".") and d not in self._skip_dirs
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
                    content = file_path.read_bytes()
                    resources[relative_path] = f"base64: {content}"
                except Exception:
                    logging.warning(
                        f"Failed to read resource file {file_path}", exc_info=True
                    )

        return resources
