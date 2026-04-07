#################################################################################
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


class SkillPromptProvider:
    """System prompt templates for skill discovery and activation.

    This class provides prompt templates used to generate system prompts
    for LLM integration with skills.
    """

    # System prompt template for skills discovery
    SKILL_DISCOVERY_PROMPT = """## Available Skills

<usage>
Skills provide specialized capabilities and domain knowledge. Use them when they match your current task.

How to use skills:
- Load skill: load_skill(name="<skill-name>", path="SKILL.md")
- The skill will be activated and its documentation loaded with detailed instructions
- Additional resources (scripts, assets, references) can be loaded using the same tool with different paths

Path Information:
When you load a skill, the response will include:
- Exact paths to all skill resources
- Usage instructions specific to that skill

Template fields explanation:
- <name>: The skill's display name
- <description>: When and how to use this skill
</usage>

<available_skills>
"""

    # System prompt template for available skills
    AVAILABLE_SKILL_TEMPLATE = """
<skill>
<name>{name}</name>
<description>{description}</description>
</skill>
"""

    AVAILABLE_SKILLS_TAG_END = """
</available_skills>
"""
