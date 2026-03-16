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
"""URL Skill Repository implementation.

This module provides UrlSkillRepository which loads skills from
remote URLs (OSS, S3, HTTP servers).
"""
import tempfile
import zipfile
from pathlib import Path
from typing import List
from urllib.parse import urlparse

from flink_agents.api.skills.agent_skill import AgentSkill
from flink_agents.api.skills.repository.filesystem_repository import (
    FileSystemSkillRepository,
)
from flink_agents.api.skills.repository.skill_repository import (
    SkillRepository,
    SkillRepositoryInfo,
)


class UrlSkillRepository(SkillRepository):
    """URL-based implementation of SkillRepository.

    This repository downloads skills from remote URLs (OSS, S3, HTTP servers).
    The URL can point to:
    - A single SKILL.md file
    - A zip archive containing skill directories
    - A directory listing endpoint

    Currently supports:
    - HTTP/HTTPS URLs
    - Zip archives containing skill directories

    Future support planned for:
    - S3, OSS, and other cloud storage
    - GitHub repositories

    Example:
    -------
    >>> repo = UrlSkillRepository("https://example.com/skills/my-skill.zip")
    >>> skill = repo.get_skill("my-skill")
    """

    SKILL_MD_FILE = "SKILL.md"

    def __init__(
        self,
        url: str,
        cache_dir: Path | None = None,
        source: str | None = None,
    ) -> None:
        """Create a UrlSkillRepository.

        Parameters
        ----------
        url : str
            The URL to load skills from.
        cache_dir : Optional[Path]
            Directory to cache downloaded skills. If None, a temp directory is used.
        source : Optional[str]
            Custom source identifier for skills.

        Raises:
        ------
        ValueError
            If url is None or empty.
        """
        if not url:
            raise ValueError("URL cannot be None or empty")

        self._url = url
        self._source = source
        self._cache_dir = cache_dir
        self._temp_dir: tempfile.TemporaryDirectory | None = None
        self._cached_repo: FileSystemSkillRepository | None = None
        self._skill_names: List[str] = []

    @property
    def url(self) -> str:
        """Get the URL.

        Returns:
        -------
        str
            The URL.
        """
        return self._url

    def _ensure_loaded(self) -> None:
        """Ensure skills are loaded from the URL.

        This method downloads and caches the skills on first access.
        """
        if self._cached_repo is not None:
            return

        # Create cache directory
        if self._cache_dir is None:
            self._temp_dir = tempfile.TemporaryDirectory(prefix="skills-url-cache-")
            cache_path = Path(self._temp_dir.name)
        else:
            cache_path = self._cache_dir
            cache_path.mkdir(parents=True, exist_ok=True)

        # Download and extract
        downloaded_path = self._download(cache_path)

        # Check if it's a zip file
        if downloaded_path.suffix == ".zip" or self._is_zip_content(downloaded_path):
            extracted_path = self._extract_zip(downloaded_path, cache_path)
            self._cached_repo = FileSystemSkillRepository(
                extracted_path, writeable=False, source=self.get_source()
            )
        else:
            # Assume it's a directory
            self._cached_repo = FileSystemSkillRepository(
                downloaded_path, writeable=False, source=self.get_source()
            )

        # Cache skill names
        self._skill_names = self._cached_repo.get_all_skill_names()

    def _download(self, cache_path: Path) -> Path:
        """Download content from URL.

        Parameters
        ----------
        cache_path : Path
            Path to cache directory.

        Returns:
        -------
        Path
            Path to downloaded content.
        """
        import urllib.request

        # Parse URL to get filename
        parsed = urlparse(self._url)
        filename = Path(parsed.path).name or "skills"

        # If URL points to a zip file
        if filename.endswith(".zip"):
            target_path = cache_path / filename
            urllib.request.urlretrieve(self._url, target_path)
            return target_path

        # If URL points to a single SKILL.md
        if filename == self.SKILL_MD_FILE:
            # Create a skill directory based on parent path
            skill_name = Path(parsed.path).parent.name or "skill"
            skill_dir = cache_path / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)

            target_path = skill_dir / self.SKILL_MD_FILE
            urllib.request.urlretrieve(self._url, target_path)
            return cache_path

        # Assume URL points to a zip file
        target_path = cache_path / f"{filename}.zip"
        urllib.request.urlretrieve(self._url, target_path)
        return target_path

    def _is_zip_content(self, path: Path) -> bool:
        """Check if file is a zip archive.

        Parameters
        ----------
        path : Path
            Path to check.

        Returns:
        -------
        bool
            True if file is a zip archive.
        """
        if not path.is_file():
            return False
        try:
            with zipfile.ZipFile(path, "r") as _:
                return True
        except zipfile.BadZipFile:
            return False

    def _extract_zip(self, zip_path: Path, cache_path: Path) -> Path:
        """Extract zip file.

        Parameters
        ----------
        zip_path : Path
            Path to zip file.
        cache_path : Path
            Path to cache directory.

        Returns:
        -------
        Path
            Path to extracted directory.
        """
        extract_path = cache_path / "extracted"
        extract_path.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)

        # Check if extracted content has SKILL.md at root
        if (extract_path / self.SKILL_MD_FILE).exists():
            return extract_path

        # Check if there's a single subdirectory with SKILL.md
        subdirs = [p for p in extract_path.iterdir() if p.is_dir()]
        if len(subdirs) == 1 and (subdirs[0] / self.SKILL_MD_FILE).exists():
            return extract_path

        # Check all subdirectories for skills
        return extract_path

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
        self._ensure_loaded()
        return self._cached_repo.get_skill(name)

    def get_all_skill_names(self) -> List[str]:
        """Get all skill names in this repository.

        Returns:
        -------
        List[str]
            List of skill names.
        """
        self._ensure_loaded()
        return self._skill_names

    def get_all_skills(self) -> List[AgentSkill]:
        """Get all skills in this repository.

        Returns:
        -------
        List[AgentSkill]
            List of all skills.
        """
        self._ensure_loaded()
        return self._cached_repo.get_all_skills()

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
        self._ensure_loaded()
        return self._cached_repo.skill_exists(name)

    def get_repository_info(self) -> SkillRepositoryInfo:
        """Get information about this repository.

        Returns:
        -------
        SkillRepositoryInfo
            Repository information.
        """
        return SkillRepositoryInfo(
            repo_type="url",
            location=self._url,
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

        # Build source from URL
        parsed = urlparse(self._url)
        host = parsed.netloc or "unknown"
        path = Path(parsed.path).stem or "skill"

        return f"url-{host}-{path}"

    def __del__(self) -> None:
        """Clean up temporary directory on deletion."""
        if self._temp_dir is not None:
            try:
                self._temp_dir.cleanup()
            except Exception:
                pass
