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
"""Example demonstrating Agent Skills usage in flink-agents.

This example shows how to:
1. Load skills from filesystem paths
2. Use the skill manager to manage skills
3. Generate prompts for LLM integration
4. Use the built-in skill tools
"""
from pathlib import Path

from flink_agents.api.skills import (
    AgentSkillManager,
    create_skill_tools,
)


def main() -> None:
    """Run the skill example."""
    # Get path to example skills (inside flink_agents package)
    examples_dir = Path(__file__).parent / "skills"

    # Create skill manager
    manager = AgentSkillManager()

    # Add skills from filesystem
    print(f"Loading skills from: {examples_dir}")
    loaded_names = manager.add_skills_from_path(examples_dir)
    print(f"Loaded skills: {loaded_names}")

    # List all skills
    print("\n=== All Skills ===")
    for skill_id, skill in manager.get_all_skills().items():
        print(f"  - {skill.name}: {skill.description}")

    # Generate discovery prompt (for LLM context)
    print("\n=== Discovery Prompt ===")
    prompt = manager.generate_discovery_prompt()
    print(prompt)

    # Activate a skill and generate its prompt
    print("\n=== Activating 'data-analysis' skill ===")
    manager.activate_skill("data-analysis")
    active_prompt = manager.generate_active_skill_prompt("data-analysis")
    print(active_prompt)

    # Use the built-in skill tools
    print("\n=== Using Skill Tools ===")
    tools = create_skill_tools(manager)

    # Load skill tool
    load_tool = tools[0]
    result = load_tool.call(skill_name="data-analysis")
    print(f"Load result: success={result.success}, activated={result.activated}")
    print(f"Available resources: {result.available_resources}")

    # Load a specific resource
    result = load_tool.call(
        skill_name="data-analysis",
        resource_path="scripts/analyze.py"
    )
    if result.success:
        print(f"\n=== Resource Content (first 500 chars) ===")
        print(result.content[:500] if result.content else "Empty")

    # Check skill status
    print("\n=== Skill Status ===")
    print(f"Is 'data-analysis' active? {manager.is_skill_active('data-analysis')}")
    print(f"Active skills: {list(manager.get_active_skills().keys())}")


if __name__ == "__main__":
    main()
