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
"""Agent Skills API for flink-agents.

This module provides the Agent Skills integration for flink-agents, allowing
agents to discover, load, and use skills. Skills are folders containing
instructions, scripts, and resources that agents can use for more accurate
and efficient operations.

Key Components:
--------------
- AgentSkill: Represents a skill with metadata and content
- AgentSkillManager: Unified manager for loading and managing skills
- SkillRepository: Interface for loading skills from various sources
- LoadSkillTool: Built-in tool for loading skill content

Example:
-------
>>> from flink_agents.api.skills import AgentSkillManager, AgentSkill
>>>
>>> # Create a skill manager and add skills
>>> manager = AgentSkillManager()
>>> manager.add_skills_from_path("/path/to/skills")
>>>
>>> # Get a skill
>>> skill = manager.get_skill_by_name("my-skill")
>>> print(skill.description)
>>>
>>> # Generate prompts for LLM
>>> prompt = manager.generate_discovery_prompt()
>>> print(prompt)
"""

from flink_agents.api.skills.agent_skill import (
    AgentSkill,
    AgentSkillBuilder,
    RegisteredSkill,
)

# Repository imports
from flink_agents.api.skills.repository import (
    ClasspathSkillRepository,
    FileSystemSkillRepository,
    SkillRepository,
    SkillRepositoryInfo,
    UrlSkillRepository,
)
from flink_agents.api.skills.skill_manager import AgentSkillManager
from flink_agents.api.skills.skill_parser import (
    MarkdownSkillParser,
    ParsedMarkdown,
    SkillParser,
)
from flink_agents.api.skills.skill_registry import SkillRegistry
from flink_agents.api.skills.tools import (
    LoadSkillArgs,
    LoadSkillResourceArgs,
    LoadSkillResourceTool,
    LoadSkillResult,
    LoadSkillTool,
    create_skill_tools,
)

__all__ = [
    # Core classes
    "AgentSkill",
    "AgentSkillBuilder",
    "RegisteredSkill",
    "AgentSkillManager",
    "SkillRegistry",
    # Parser classes
    "MarkdownSkillParser",
    "ParsedMarkdown",
    "SkillParser",
    # Repository classes
    "SkillRepository",
    "SkillRepositoryInfo",
    "FileSystemSkillRepository",
    "ClasspathSkillRepository",
    "UrlSkillRepository",
    # Tool classes
    "LoadSkillTool",
    "LoadSkillArgs",
    "LoadSkillResult",
    "LoadSkillResourceTool",
    "LoadSkillResourceArgs",
    "create_skill_tools",
]
