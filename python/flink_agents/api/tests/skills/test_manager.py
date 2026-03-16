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
"""Unit tests for AgentSkillManager and skill tools."""
import tempfile
from pathlib import Path

import pytest

from flink_agents.api.skills import (
    AgentSkill,
    AgentSkillManager,
    LoadSkillArgs,
    LoadSkillResult,
    LoadSkillTool,
    create_skill_tools,
)
from flink_agents.api.skills.repository.filesystem_repository import (
    FileSystemSkillRepository,
)


class TestAgentSkillManager:
    """Tests for AgentSkillManager class."""

    @pytest.fixture
    def temp_skills_dir(self) -> Path:
        """Create a temporary directory with test skills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)

            skill1_dir = skills_dir / "skill-one"
            skill1_dir.mkdir()
            skill1_md = """---
name: skill-one
description: First test skill for testing
---
# Skill One
Instructions for skill one.
"""
            (skill1_dir / "SKILL.md").write_text(skill1_md)
            scripts_dir = skill1_dir / "scripts"
            scripts_dir.mkdir()
            (scripts_dir / "run.sh").write_text("#!/bin/bash\necho hello")

            skill2_dir = skills_dir / "skill-two"
            skill2_dir.mkdir()
            skill2_md = """---
name: skill-two
description: Second test skill for testing
---
# Skill Two
Instructions for skill two.
"""
            (skill2_dir / "SKILL.md").write_text(skill2_md)

            yield skills_dir

    def test_create_manager(self) -> None:
        """Test creating a manager."""
        manager = AgentSkillManager()
        assert manager.is_empty()
        assert manager.size() == 0

    def test_add_skills_from_path(self, temp_skills_dir: Path) -> None:
        """Test adding skills from path."""
        manager = AgentSkillManager()
        loaded = manager.add_skills_from_path(temp_skills_dir)

        assert len(loaded) == 2
        assert "skill-one" in loaded
        assert "skill-two" in loaded
        assert manager.size() == 2

    def test_get_skill(self, temp_skills_dir: Path) -> None:
        """Test getting a skill."""
        manager = AgentSkillManager()
        manager.add_skills_from_path(temp_skills_dir)

        skill = manager.get_skill("skill-one")
        assert skill is not None
        assert skill.name == "skill-one"

        # Get by partial ID (name)
        skill2 = manager.get_skill_by_name("skill-two")
        assert skill2 is not None
        assert skill2.name == "skill-two"

    def test_get_all_skills(self, temp_skills_dir: Path) -> None:
        """Test getting all skills."""
        manager = AgentSkillManager()
        manager.add_skills_from_path(temp_skills_dir)

        all_skills = manager.get_all_skills()
        assert len(all_skills) == 2

        names = manager.get_all_skill_names()
        assert "skill-one" in names
        assert "skill-two" in names

    def test_activate_skill(self, temp_skills_dir: Path) -> None:
        """Test activating a skill."""
        manager = AgentSkillManager()
        manager.add_skills_from_path(temp_skills_dir)

        assert manager.is_skill_active("skill-one") is False

        result = manager.activate_skill("skill-one")
        assert result is True
        assert manager.is_skill_active("skill-one") is True

        active_skills = manager.get_active_skills()
        assert len(active_skills) == 1

    def test_deactivate_skill(self, temp_skills_dir: Path) -> None:
        """Test deactivating a skill."""
        manager = AgentSkillManager()
        manager.add_skills_from_path(temp_skills_dir)

        manager.activate_skill("skill-one")
        result = manager.deactivate_skill("skill-one")
        assert result is True
        assert manager.is_skill_active("skill-one") is False

    def test_deactivate_all_skills(self, temp_skills_dir: Path) -> None:
        """Test deactivating all skills."""
        manager = AgentSkillManager()
        manager.add_skills_from_path(temp_skills_dir)

        manager.activate_skill("skill-one")
        manager.activate_skill("skill-two")

        manager.deactivate_all_skills()
        assert len(manager.get_active_skills()) == 0

    def test_remove_skill(self, temp_skills_dir: Path) -> None:
        """Test removing a skill."""
        manager = AgentSkillManager()
        manager.add_skills_from_path(temp_skills_dir)

        # Get the actual skill first to find its skill_id
        skill = manager.get_skill_by_name("skill-one")
        assert skill is not None

        result = manager.remove_skill(skill.skill_id)
        assert result is True
        assert manager.get_skill_by_name("skill-one") is None
        assert manager.size() == 1

    def test_clear(self, temp_skills_dir: Path) -> None:
        """Test clearing all skills."""
        manager = AgentSkillManager()
        manager.add_skills_from_path(temp_skills_dir)

        manager.clear()
        assert manager.is_empty()

    def test_generate_discovery_prompt(self, temp_skills_dir: Path) -> None:
        """Test generating discovery prompt."""
        manager = AgentSkillManager()
        manager.add_skills_from_path(temp_skills_dir)

        prompt = manager.generate_discovery_prompt()
        assert "Available Skills" in prompt
        assert "skill-one" in prompt
        assert "First test skill for testing" in prompt
        assert "load_skill" in prompt

    def test_generate_active_skill_prompt(self, temp_skills_dir: Path) -> None:
        """Test generating active skill prompt."""
        manager = AgentSkillManager()
        manager.add_skills_from_path(temp_skills_dir)

        prompt = manager.generate_active_skill_prompt("skill-one")
        assert prompt is not None
        assert "Active Skill: skill-one" in prompt
        assert "Instructions for skill one" in prompt

    def test_load_skill_resource(self, temp_skills_dir: Path) -> None:
        """Test loading a skill resource."""
        manager = AgentSkillManager()
        manager.add_skills_from_path(temp_skills_dir)

        content = manager.load_skill_resource("skill-one", "scripts/run.sh")
        assert content is not None
        assert "echo hello" in content

        nonexistent = manager.load_skill_resource("skill-one", "nonexistent.txt")
        assert nonexistent is None

    def test_register_skill_directly(self) -> None:
        """Test registering a skill directly."""
        manager = AgentSkillManager()
        skill = AgentSkill(
            name="direct-skill",
            description="A directly registered skill",
            skill_content="Content",
            resources={"file.txt": "content"},
        )
        manager.register_skill(skill)

        assert manager.size() == 1
        loaded = manager.get_skill_by_name("direct-skill")
        assert loaded is not None
        assert loaded.name == "direct-skill"


class TestLoadSkillTool:
    """Tests for LoadSkillTool class."""

    @pytest.fixture
    def manager_with_skills(self) -> AgentSkillManager:
        """Create a manager with test skills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)

            skill_dir = skills_dir / "test-skill"
            skill_dir.mkdir()
            skill_md = """---
name: test-skill
description: A test skill
---
# Test Skill
Instructions here.
"""
            (skill_dir / "SKILL.md").write_text(skill_md)
            scripts_dir = skill_dir / "scripts"
            scripts_dir.mkdir()
            (scripts_dir / "run.sh").write_text("#!/bin/bash\necho test")

            manager = AgentSkillManager()
            manager.add_skills_from_path(skills_dir)
            yield manager

    def test_load_skill_full_content(self, manager_with_skills: AgentSkillManager) -> None:
        """Test loading full skill content."""
        tools = create_skill_tools(manager_with_skills)
        load_tool = tools[0]

        result = load_tool.call(skill_name="test-skill")

        assert isinstance(result, LoadSkillResult)
        assert result.success is True
        assert result.activated is True
        assert "Instructions here" in result.content
        assert result.skill_name == "test-skill"
        assert "scripts/run.sh" in result.available_resources

    def test_load_skill_resource(self, manager_with_skills: AgentSkillManager) -> None:
        """Test loading a specific resource."""
        tools = create_skill_tools(manager_with_skills)
        load_tool = tools[0]

        result = load_tool.call(skill_name="test-skill", resource_path="scripts/run.sh")

        assert result.success is True
        assert "echo test" in result.content
        assert result.activated is False  # Should not activate when loading resource

    def test_load_nonexistent_skill(self, manager_with_skills: AgentSkillManager) -> None:
        """Test loading a nonexistent skill."""
        tools = create_skill_tools(manager_with_skills)
        load_tool = tools[0]

        result = load_tool.call(skill_name="nonexistent")

        assert result.success is False
        assert "not found" in result.error
        assert result.skill_name == "nonexistent"

    def test_load_nonexistent_resource(self, manager_with_skills: AgentSkillManager) -> None:
        """Test loading a nonexistent resource."""
        tools = create_skill_tools(manager_with_skills)
        load_tool = tools[0]

        result = load_tool.call(skill_name="test-skill", resource_path="nonexistent.txt")

        assert result.success is False
        assert "not found" in result.error
        assert result.available_resources is not None

    def test_load_skill_no_manager(self) -> None:
        """Test loading skill without manager."""
        tool = LoadSkillTool()
        result = tool.call(skill_name="test")

        assert result.success is False
        assert "not available" in result.error


class TestLoadSkillArgs:
    """Tests for LoadSkillArgs model."""

    def test_create_args(self) -> None:
        """Test creating arguments."""
        args = LoadSkillArgs(skill_name="test-skill")
        assert args.skill_name == "test-skill"
        assert args.resource_path is None

    def test_create_args_with_resource(self) -> None:
        """Test creating arguments with resource path."""
        args = LoadSkillArgs(skill_name="test-skill", resource_path="scripts/run.sh")
        assert args.skill_name == "test-skill"
        assert args.resource_path == "scripts/run.sh"
