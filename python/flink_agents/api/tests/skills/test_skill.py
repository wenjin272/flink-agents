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
"""Unit tests for Agent Skill components."""
import pytest

from flink_agents.api.skills.agent_skill import AgentSkill, AgentSkillBuilder, RegisteredSkill
from flink_agents.api.skills.skill_parser import MarkdownSkillParser, ParsedMarkdown, SkillParser
from flink_agents.api.skills.skill_registry import SkillRegistry


class TestAgentSkill:
    """Tests for AgentSkill class."""

    def test_create_skill_with_required_fields(self) -> None:
        """Test creating a skill with required fields only."""
        skill = AgentSkill(
            name="my-skill",
            description="A test skill",
            skill_content="Test content",
        )
        assert skill.name == "my-skill"
        assert skill.description == "A test skill"
        assert skill.skill_content == "Test content"
        assert skill.resources == {}
        assert skill.source == "custom"
        assert skill.license is None
        assert skill.compatibility is None
        assert skill.metadata is None
        assert skill.allowed_tools is None

    def test_create_skill_with_all_fields(self) -> None:
        """Test creating a skill with all fields."""
        skill = AgentSkill(
            name="pdf-processing",
            description="Extract PDF text, fill forms, merge files.",
            skill_content="Instructions here",
            resources={"scripts/run.sh": "#!/bin/bash\necho hello"},
            source="filesystem",
            license="Apache-2.0",
            compatibility="Requires python3",
            metadata={"author": "test", "version": "1.0"},
            allowed_tools="Bash(git:*) Read",
        )
        assert skill.name == "pdf-processing"
        assert skill.resources == {"scripts/run.sh": "#!/bin/bash\necho hello"}
        assert skill.source == "filesystem"
        assert skill.license == "Apache-2.0"
        assert skill.compatibility == "Requires python3"
        assert skill.metadata == {"author": "test", "version": "1.0"}
        assert skill.allowed_tools == "Bash(git:*) Read"

    def test_skill_id(self) -> None:
        """Test skill_id property."""
        skill = AgentSkill(
            name="my-skill",
            description="A test skill",
            skill_content="Content",
            source="filesystem",
        )
        assert skill.skill_id == "my-skill_filesystem"

    def test_get_resource(self) -> None:
        """Test get_resource method."""
        skill = AgentSkill(
            name="test",
            description="Test",
            skill_content="Content",
            resources={"file.txt": "content", "dir/nested.py": "# code"},
        )
        assert skill.get_resource("file.txt") == "content"
        assert skill.get_resource("dir/nested.py") == "# code"
        assert skill.get_resource("nonexistent.txt") is None

    def test_get_resource_paths(self) -> None:
        """Test get_resource_paths method."""
        skill = AgentSkill(
            name="test",
            description="Test",
            skill_content="Content",
            resources={"file.txt": "content", "dir/nested.py": "# code"},
        )
        paths = skill.get_resource_paths()
        assert "file.txt" in paths
        assert "dir/nested.py" in paths
        assert len(paths) == 2

    def test_validate_name_empty(self) -> None:
        """Test name validation with empty string."""
        with pytest.raises(ValueError):
            AgentSkill(name="", description="Test", skill_content="Content")

    def test_validate_name_uppercase(self) -> None:
        """Test name validation with uppercase letters."""
        with pytest.raises(ValueError):
            AgentSkill(name="My-Skill", description="Test", skill_content="Content")

    def test_validate_name_start_with_hyphen(self) -> None:
        """Test name validation with leading hyphen."""
        with pytest.raises(ValueError):
            AgentSkill(name="-skill", description="Test", skill_content="Content")

    def test_validate_name_end_with_hyphen(self) -> None:
        """Test name validation with trailing hyphen."""
        with pytest.raises(ValueError):
            AgentSkill(name="skill-", description="Test", skill_content="Content")

    def test_validate_name_consecutive_hyphens(self) -> None:
        """Test name validation with consecutive hyphens."""
        with pytest.raises(ValueError):
            AgentSkill(name="my--skill", description="Test", skill_content="Content")

    def test_validate_name_too_long(self) -> None:
        """Test name validation with too long name."""
        long_name = "a" * 65
        with pytest.raises(ValueError):
            AgentSkill(name=long_name, description="Test", skill_content="Content")

    def test_valid_names(self) -> None:
        """Test valid skill names."""
        valid_names = ["skill", "my-skill", "skill-123", "a", "abc-xyz-123"]
        for name in valid_names:
            skill = AgentSkill(name=name, description="Test", skill_content="Content")
            assert skill.name == name


class TestAgentSkillBuilder:
    """Tests for AgentSkillBuilder class."""

    def test_build_from_scratch(self) -> None:
        """Test building a skill from scratch."""
        skill = (
            AgentSkill.builder()
            .name("my-skill")
            .description("Test skill")
            .skill_content("Content")
            .add_resource("file.txt", "content")
            .source("test")
            .build()
        )
        assert skill.name == "my-skill"
        assert skill.description == "Test skill"
        assert skill.skill_content == "Content"
        assert skill.resources == {"file.txt": "content"}
        assert skill.source == "test"

    def test_build_from_existing(self) -> None:
        """Test building a skill from existing skill."""
        original = AgentSkill(
            name="original",
            description="Original",
            skill_content="Original content",
            resources={"file.txt": "original"},
        )
        modified = (
            original.to_builder()
            .description("Modified")
            .add_resource("new.txt", "new content")
            .build()
        )
        assert modified.name == "original"
        assert modified.description == "Modified"
        assert "file.txt" in modified.resources
        assert "new.txt" in modified.resources

    def test_build_missing_required_fields(self) -> None:
        """Test building without required fields."""
        with pytest.raises(ValueError):
            AgentSkill.builder().name("test").build()

        with pytest.raises(ValueError):
            AgentSkill.builder().description("test").build()


class TestRegisteredSkill:
    """Tests for RegisteredSkill class."""

    def test_create_registered_skill(self) -> None:
        """Test creating a registered skill."""
        registered = RegisteredSkill(skill_id="test_filesystem")
        assert registered.skill_id == "test_filesystem"
        assert registered.active is False
        assert registered.tools_group_name == "test_filesystem_skill_tools"

    def test_set_active(self) -> None:
        """Test setting active state."""
        registered = RegisteredSkill(skill_id="test_filesystem")
        registered.set_active(True)
        assert registered.active is True
        registered.set_active(False)
        assert registered.active is False


class TestMarkdownSkillParser:
    """Tests for MarkdownSkillParser class."""

    def test_parse_with_frontmatter(self) -> None:
        """Test parsing markdown with frontmatter."""
        markdown = """---
name: my-skill
description: A test skill
---
# My Skill

This is the skill content.
"""
        parsed = MarkdownSkillParser.parse(markdown)
        assert parsed.has_frontmatter()
        assert parsed.metadata["name"] == "my-skill"
        assert parsed.metadata["description"] == "A test skill"
        assert "# My Skill" in parsed.content

    def test_parse_without_frontmatter(self) -> None:
        """Test parsing markdown without frontmatter."""
        markdown = "# My Skill\n\nThis is just markdown."
        parsed = MarkdownSkillParser.parse(markdown)
        assert not parsed.has_frontmatter()
        assert parsed.metadata == {}
        assert markdown in parsed.content

    def test_parse_empty(self) -> None:
        """Test parsing empty content."""
        parsed = MarkdownSkillParser.parse("")
        assert not parsed.has_frontmatter()
        assert parsed.metadata == {}
        assert parsed.content == ""

    def test_parse_with_optional_fields(self) -> None:
        """Test parsing with optional frontmatter fields."""
        markdown = """---
name: pdf-processing
description: PDF skill
license: Apache-2.0
compatibility: Requires python3
allowed-tools: Bash(git:*) Read
author: test-user
---
Content here.
"""
        parsed = MarkdownSkillParser.parse(markdown)
        assert parsed.metadata["name"] == "pdf-processing"
        assert parsed.metadata["license"] == "Apache-2.0"
        assert parsed.metadata["compatibility"] == "Requires python3"
        assert parsed.metadata["allowed-tools"] == "Bash(git:*) Read"
        assert parsed.metadata["author"] == "test-user"

    def test_generate(self) -> None:
        """Test generating markdown with frontmatter."""
        metadata = {"name": "test", "description": "A test"}
        content = "# Content"
        result = MarkdownSkillParser.generate(metadata, content)
        assert "---" in result
        assert "name: test" in result
        assert "description: A test" in result
        assert "# Content" in result

    def test_parse_quoted_values(self) -> None:
        """Test parsing quoted YAML values."""
        markdown = '''---
name: test
description: "A description with: colons"
---
Content
'''
        parsed = MarkdownSkillParser.parse(markdown)
        assert parsed.metadata["description"] == "A description with: colons"


class TestSkillParser:
    """Tests for SkillParser class."""

    def test_parse_skill(self) -> None:
        """Test parsing a complete skill."""
        skill_md = """---
name: my-skill
description: A test skill
license: Apache-2.0
---
# My Skill

Instructions here.
"""
        resources = {"scripts/run.sh": "#!/bin/bash\necho hello"}
        skill = SkillParser.parse_skill(skill_md, resources, "test")

        assert skill.name == "my-skill"
        assert skill.description == "A test skill"
        assert skill.license == "Apache-2.0"
        assert "Instructions here" in skill.skill_content
        assert skill.resources == resources
        assert skill.source == "test"

    def test_parse_skill_missing_name(self) -> None:
        """Test parsing skill without name."""
        skill_md = """---
description: A test skill
---
Content
"""
        with pytest.raises(ValueError):
            SkillParser.parse_skill(skill_md)

    def test_parse_skill_missing_description(self) -> None:
        """Test parsing skill without description."""
        skill_md = """---
name: test
---
Content
"""
        with pytest.raises(ValueError):
            SkillParser.parse_skill(skill_md)

    def test_generate_skill_md(self) -> None:
        """Test generating SKILL.md content."""
        skill = AgentSkill(
            name="test",
            description="A test skill",
            skill_content="# Content",
            license="Apache-2.0",
        )
        md = SkillParser.generate_skill_md(skill)
        assert "---" in md
        assert "name: test" in md
        assert "description: A test skill" in md
        assert "license: Apache-2.0" in md
        assert "# Content" in md


class TestSkillRegistry:
    """Tests for SkillRegistry class."""

    def test_register_and_get_skill(self) -> None:
        """Test registering and getting a skill."""
        registry = SkillRegistry()
        skill = AgentSkill(
            name="test",
            description="Test",
            skill_content="Content",
            source="test-source",
        )
        registered = RegisteredSkill(skill_id=skill.skill_id)

        registry.register_skill(skill.skill_id, skill, registered)

        assert registry.exists(skill.skill_id)
        assert registry.get_skill(skill.skill_id) == skill
        assert registry.get_registered_skill(skill.skill_id) == registered

    def test_set_skill_active(self) -> None:
        """Test setting skill active state."""
        registry = SkillRegistry()
        skill = AgentSkill(name="test", description="Test", skill_content="Content")
        registered = RegisteredSkill(skill_id=skill.skill_id)
        registry.register_skill(skill.skill_id, skill, registered)

        registry.set_skill_active(skill.skill_id, True)
        assert registry.get_registered_skill(skill.skill_id).active is True

        registry.set_skill_active(skill.skill_id, False)
        assert registry.get_registered_skill(skill.skill_id).active is False

    def test_set_all_skills_active(self) -> None:
        """Test setting all skills active state."""
        registry = SkillRegistry()
        for i in range(3):
            skill = AgentSkill(name=f"skill-{i}", description="Test", skill_content="Content")
            registered = RegisteredSkill(skill_id=skill.skill_id)
            registry.register_skill(skill.skill_id, skill, registered)

        registry.set_all_skills_active(True)
        for sid in registry.get_skill_ids():
            assert registry.get_registered_skill(sid).active is True

    def test_remove_skill(self) -> None:
        """Test removing a skill."""
        registry = SkillRegistry()
        skill = AgentSkill(name="test", description="Test", skill_content="Content")
        registered = RegisteredSkill(skill_id=skill.skill_id)
        registry.register_skill(skill.skill_id, skill, registered)

        assert registry.remove_skill(skill.skill_id) is True
        assert not registry.exists(skill.skill_id)
        assert registry.remove_skill("nonexistent") is False

    def test_get_all_skills(self) -> None:
        """Test getting all skills."""
        registry = SkillRegistry()
        for i in range(3):
            skill = AgentSkill(
                name=f"skill-{i}",
                description="Test",
                skill_content="Content",
                source=f"source-{i}",
            )
            registered = RegisteredSkill(skill_id=skill.skill_id)
            registry.register_skill(skill.skill_id, skill, registered)

        all_skills = registry.get_all_skills()
        assert len(all_skills) == 3

    def test_get_active_skills(self) -> None:
        """Test getting active skills."""
        registry = SkillRegistry()
        for i in range(3):
            skill = AgentSkill(name=f"skill-{i}", description="Test", skill_content="Content")
            registered = RegisteredSkill(skill_id=skill.skill_id)
            registry.register_skill(skill.skill_id, skill, registered)

        # Activate one skill
        registry.set_skill_active("skill-1_custom", True)

        active = registry.get_active_skills()
        assert len(active) == 1
        assert "skill-1_custom" in active

    def test_clear(self) -> None:
        """Test clearing registry."""
        registry = SkillRegistry()
        skill = AgentSkill(name="test", description="Test", skill_content="Content")
        registered = RegisteredSkill(skill_id=skill.skill_id)
        registry.register_skill(skill.skill_id, skill, registered)

        registry.clear()
        assert registry.is_empty()
        assert registry.size() == 0
