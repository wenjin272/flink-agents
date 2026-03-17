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
"""Unit tests for Skill Repository components."""
import tempfile
from pathlib import Path

import pytest

from flink_agents.api.skills.agent_skill import AgentSkill
from flink_agents.api.skills.repository.filesystem_repository import (
    FileSystemSkillRepository,
)
from flink_agents.api.skills.repository.skill_repository import SkillRepositoryInfo
from flink_agents.api.skills.skill_parser import SkillParser


class TestFileSystemSkillRepository:
    """Tests for FileSystemSkillRepository class."""

    @pytest.fixture
    def temp_skills_dir(self) -> Path:
        """Create a temporary directory with test skills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)

            # Create first skill
            skill1_dir = skills_dir / "skill-one"
            skill1_dir.mkdir()
            skill1_md = """---
name: skill-one
description: First test skill
license: Apache-2.0
---
# Skill One

This is the first skill.

## Instructions
1. Do something
2. Do something else
"""
            (skill1_dir / "SKILL.md").write_text(skill1_md)

            # Create scripts directory
            scripts_dir = skill1_dir / "scripts"
            scripts_dir.mkdir()
            (scripts_dir / "run.sh").write_text("#!/bin/bash\necho 'Hello from skill one'")

            # Create second skill
            skill2_dir = skills_dir / "skill-two"
            skill2_dir.mkdir()
            skill2_md = """---
name: skill-two
description: Second test skill
---
# Skill Two

Content for skill two.
"""
            (skill2_dir / "SKILL.md").write_text(skill2_md)

            yield skills_dir

    def test_create_repository(self, temp_skills_dir: Path) -> None:
        """Test creating a repository."""
        repo = FileSystemSkillRepository(temp_skills_dir)
        # Path is resolved, so compare resolved paths
        assert repo.base_dir == temp_skills_dir.resolve()
        assert repo.is_writeable()

    def test_create_repository_invalid_path(self) -> None:
        """Test creating repository with invalid path."""
        with pytest.raises(ValueError):
            FileSystemSkillRepository("/nonexistent/path")

    def test_get_all_skill_names(self, temp_skills_dir: Path) -> None:
        """Test getting all skill names."""
        repo = FileSystemSkillRepository(temp_skills_dir)
        names = repo.get_all_skill_names()
        assert len(names) == 2
        assert "skill-one" in names
        assert "skill-two" in names

    def test_get_skill(self, temp_skills_dir: Path) -> None:
        """Test getting a specific skill."""
        repo = FileSystemSkillRepository(temp_skills_dir)
        skill = repo.load_content("skill-one")

        assert skill is not None
        assert skill.name == "skill-one"
        assert skill.description == "First test skill"
        assert skill.license == "Apache-2.0"
        assert "# Skill One" in skill.skill_content

    def test_get_skill_with_resources(self, temp_skills_dir: Path) -> None:
        """Test getting a skill with resources."""
        repo = FileSystemSkillRepository(temp_skills_dir)
        skill = repo.load_content("skill-one")

        assert skill is not None
        resources = skill.get_resource_paths()
        assert "scripts/run.sh" in resources

        script_content = skill.get_resource("scripts/run.sh")
        assert "echo 'Hello from skill one'" in script_content

    def test_get_nonexistent_skill(self, temp_skills_dir: Path) -> None:
        """Test getting a nonexistent skill."""
        repo = FileSystemSkillRepository(temp_skills_dir)
        skill = repo.load_content("nonexistent")
        assert skill is None

    def test_skill_exists(self, temp_skills_dir: Path) -> None:
        """Test checking if skill exists."""
        repo = FileSystemSkillRepository(temp_skills_dir)
        assert repo.skill_exists("skill-one")
        assert repo.skill_exists("skill-two")
        assert not repo.skill_exists("nonexistent")

    def test_get_all_skills(self, temp_skills_dir: Path) -> None:
        """Test getting all skills."""
        repo = FileSystemSkillRepository(temp_skills_dir)
        skills = repo.get_all_skills()
        assert len(skills) == 2
        names = {s.name for s in skills}
        assert "skill-one" in names
        assert "skill-two" in names

    def test_get_repository_info(self, temp_skills_dir: Path) -> None:
        """Test getting repository info."""
        repo = FileSystemSkillRepository(temp_skills_dir)
        info = repo.get_repository_info()
        assert isinstance(info, SkillRepositoryInfo)
        assert info.repo_type == "filesystem"
        assert str(temp_skills_dir) in info.location
        assert info.writeable is True

    def test_get_source(self, temp_skills_dir: Path) -> None:
        """Test getting source identifier."""
        repo = FileSystemSkillRepository(temp_skills_dir, source="custom-source")
        assert repo.get_source() == "custom-source"

    def test_save_skill(self, temp_skills_dir: Path) -> None:
        """Test saving a skill."""
        repo = FileSystemSkillRepository(temp_skills_dir)

        new_skill = AgentSkill(
            name="new-skill",
            description="A new skill",
            skill_content="# New Skill\n\nContent here.",
            resources={"script.py": "#!/usr/bin/env python3\nprint('hello')"},
        )

        result = repo.save([new_skill])
        assert result is True
        assert repo.skill_exists("new-skill")

        loaded = repo.load_content("new-skill")
        assert loaded is not None
        assert loaded.name == "new-skill"
        assert loaded.get_resource("script.py") is not None

    def test_delete_skill(self, temp_skills_dir: Path) -> None:
        """Test deleting a skill."""
        repo = FileSystemSkillRepository(temp_skills_dir)

        assert repo.skill_exists("skill-one")
        result = repo.delete("skill-one")
        assert result is True
        assert not repo.skill_exists("skill-one")

    def test_readonly_repository(self, temp_skills_dir: Path) -> None:
        """Test readonly repository."""
        repo = FileSystemSkillRepository(temp_skills_dir, writeable=False)

        new_skill = AgentSkill(
            name="new-skill",
            description="A new skill",
            skill_content="Content",
        )
        assert repo.save([new_skill]) is False
        assert repo.delete("skill-one") is False

    def test_custom_source(self, temp_skills_dir: Path) -> None:
        """Test custom source identifier."""
        repo = FileSystemSkillRepository(temp_skills_dir, source="my-source")
        skill = repo.load_content("skill-one")
        assert skill is not None
        assert skill.group == "my-source"


class TestSkillRepositoryInfo:
    """Tests for SkillRepositoryInfo class."""

    def test_create_info(self) -> None:
        """Test creating repository info."""
        info = SkillRepositoryInfo(
            repo_type="filesystem",
            location="/path/to/skills",
            writeable=True,
        )
        assert info.repo_type == "filesystem"
        assert info.location == "/path/to/skills"
        assert info.writeable is True
