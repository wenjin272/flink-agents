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

from pathlib import Path

import pytest

from flink_agents.api.skills.skill_parser import MarkdownSkillParser, SkillParser

base_dir = Path(__file__).parent


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
        assert parsed.metadata["name"] == "my-skill"
        assert parsed.metadata["description"] == "A test skill"
        assert parsed.content == "# My Skill\n\nThis is the skill content.\n"

    def test_parse_without_frontmatter(self) -> None:
        """Test parsing markdown without frontmatter."""
        markdown = "# My Skill\n\nThis is just markdown."
        parsed = MarkdownSkillParser.parse(markdown)
        assert parsed.metadata == {}
        assert markdown in parsed.content

    def test_parse_empty(self) -> None:
        """Test parsing empty content."""
        parsed = MarkdownSkillParser.parse("")
        assert parsed.metadata == {}
        assert parsed.content == ""

    def test_parse_with_optional_fields(self) -> None:
        """Test parsing with optional frontmatter fields."""
        markdown = """---
name: pdf-processing
description: PDF skill
license: Apache-2.0
compatibility: Requires python3
metadata:
  author: example-org
  version: "1.0"
allowed-tools: Bash(git:*) Read
---
Content here.
"""
        parsed = MarkdownSkillParser.parse(markdown)
        assert parsed.metadata["name"] == "pdf-processing"
        assert parsed.metadata["license"] == "Apache-2.0"
        assert parsed.metadata["compatibility"] == "Requires python3"
        assert parsed.metadata["metadata"] == {"author": "example-org", "version": "1.0"}
        assert parsed.metadata["allowed-tools"] == "Bash(git:*) Read"
        assert parsed.content == "Content here.\n"

    def test_parse_quoted_values(self) -> None:
        """Test parsing quoted YAML values."""
        markdown = """---
name: test
description: "A description with: colons"
---
Content
"""
        parsed = MarkdownSkillParser.parse(markdown)
        assert parsed.metadata["description"] == "A description with: colons"

    def test_parse_skill(self) -> None:
        with open(base_dir / "resources" / "SKILL.md") as f:
            markdown = f.read()
        parsed = MarkdownSkillParser.parse(markdown)
        assert parsed.metadata["name"] == "github"
        assert parsed.metadata["description"] == (
            "Interact with GitHub using the `gh` CLI. "
            "Use `gh issue`, `gh pr`, `gh run`, and `gh "
            "api` for issues, PRs, CI runs, and advanced queries."
        )


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
        skill = SkillParser.parse_skill(skill_md)

        assert skill.name == "my-skill"
        assert skill.description == "A test skill"
        assert skill.license == "Apache-2.0"
        assert "Instructions here" in skill.skill_content
        assert skill.resources == resources
        assert skill.group == "test"

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


# class TestSkillRegistry:
#     """Tests for SkillRegistry class."""
#
#     def test_register_and_get_skill(self) -> None:
#         """Test registering and getting a skill."""
#         registry = SkillRegistry()
#         skill = AgentSkill(
#             name="test",
#             description="Test",
#             skill_content="Content",
#             group="test-source",
#         )
#         registered = RegisteredSkill(skill_id=skill.skill_id)
#
#         registry.register_skill(skill.skill_id, skill, registered)
#
#         assert registry.exists(skill.skill_id)
#         assert registry.get_skill(skill.skill_id) == skill
#         assert registry.get_registered_skill(skill.skill_id) == registered
#
#     def test_set_skill_active(self) -> None:
#         """Test setting skill active state."""
#         registry = SkillRegistry()
#         skill = AgentSkill(name="test", description="Test", skill_content="Content")
#         registered = RegisteredSkill(skill_id=skill.skill_id)
#         registry.register_skill(skill.skill_id, skill, registered)
#
#         registry.set_skill_active(skill.skill_id, True)
#         assert registry.get_registered_skill(skill.skill_id).active is True
#
#         registry.set_skill_active(skill.skill_id, False)
#         assert registry.get_registered_skill(skill.skill_id).active is False
#
#     def test_set_all_skills_active(self) -> None:
#         """Test setting all skills active state."""
#         registry = SkillRegistry()
#         for i in range(3):
#             skill = AgentSkill(name=f"skill-{i}", description="Test", skill_content="Content")
#             registered = RegisteredSkill(skill_id=skill.skill_id)
#             registry.register_skill(skill.skill_id, skill, registered)
#
#         registry.set_all_skills_active(True)
#         for sid in registry.get_skill_ids():
#             assert registry.get_registered_skill(sid).active is True
#
#     def test_remove_skill(self) -> None:
#         """Test removing a skill."""
#         registry = SkillRegistry()
#         skill = AgentSkill(name="test", description="Test", skill_content="Content")
#         registered = RegisteredSkill(skill_id=skill.skill_id)
#         registry.register_skill(skill.skill_id, skill, registered)
#
#         assert registry.remove_skill(skill.skill_id) is True
#         assert not registry.exists(skill.skill_id)
#         assert registry.remove_skill("nonexistent") is False
#
#     def test_get_all_skills(self) -> None:
#         """Test getting all skills."""
#         registry = SkillRegistry()
#         for i in range(3):
#             skill = AgentSkill(
#                 name=f"skill-{i}",
#                 description="Test",
#                 skill_content="Content",
#                 group=f"source-{i}",
#             )
#             registered = RegisteredSkill(skill_id=skill.skill_id)
#             registry.register_skill(skill.skill_id, skill, registered)
#
#         all_skills = registry.get_all_skills()
#         assert len(all_skills) == 3
#
#     def test_get_active_skills(self) -> None:
#         """Test getting active skills."""
#         registry = SkillRegistry()
#         for i in range(3):
#             skill = AgentSkill(name=f"skill-{i}", description="Test", skill_content="Content")
#             registered = RegisteredSkill(skill_id=skill.skill_id)
#             registry.register_skill(skill.skill_id, skill, registered)
#
#         # Activate one skill
#         registry.set_skill_active("skill-1_custom", True)
#
#         active = registry.get_active_skills()
#         assert len(active) == 1
#         assert "skill-1_custom" in active
#
#     def test_clear(self) -> None:
#         """Test clearing registry."""
#         registry = SkillRegistry()
#         skill = AgentSkill(name="test", description="Test", skill_content="Content")
#         registered = RegisteredSkill(skill_id=skill.skill_id)
#         registry.register_skill(skill.skill_id, skill, registered)
#
#         registry.clear()
#         assert registry.is_empty()
#         assert registry.size() == 0
