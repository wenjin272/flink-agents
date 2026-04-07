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
#################################################################################
import shlex
from pathlib import Path
from typing import ClassVar, Dict, List, Set

from flink_agents.api.skills import Skills
from flink_agents.runtime.skill.agent_skill import AgentSkill
from flink_agents.runtime.skill.repository.filesystem_repository import (
    FileSystemSkillRepository,
)
from flink_agents.runtime.skill.skill_prompt_provider import SkillPromptProvider
from flink_agents.runtime.skill.skill_repository import SkillRepository


class RegisteredSkill:
    """A wrapper that associates an AgentSkill with its source repository.

    Provides lazy activation for skill resources, loading them only when
    first needed (e.g., when get_resource or get_resource_paths is called).
    """

    def __init__(self, agent_skill: AgentSkill, repo: SkillRepository) -> None:
        """Initialize a new registered skill."""
        self.agent_skill = agent_skill
        self.repo = repo
        self.active = False

    @property
    def name(self) -> str:
        """Get the name of the skill."""
        return self.agent_skill.name

    @property
    def description(self) -> str:
        """Get the description of the skill."""
        return self.agent_skill.description

    @property
    def content(self) -> str:
        """Get the content of the skill."""
        return self.agent_skill.content

    def get_resource(self, resource_path: str) -> str:
        """Get the resource content by relative path."""
        self._activate()
        return self.agent_skill.get_resource(resource_path)

    def get_resource_paths(self) -> List[str]:
        """Get all the resource relative paths of the skill."""
        self._activate()
        return self.agent_skill.get_resource_paths()

    def _activate(self) -> None:
        if not self.active:
            self.agent_skill.resources = self.repo.get_resources(self.agent_skill.name)
            self.active = True


class SkillManager:
    """Internal runtime component for loading, parsing, and managing skills.

    Created by the runtime from a :class:`Skills` configuration resource.
    Never exposed to users directly.

    Progressive Disclosure:
    - Discovery: Load only name/description at startup (~100 tokens)
    - Activation: Load full SKILL.md when skill matches task
    - Execution: Load resources/scripts only when needed
    """

    # Mapping from script type name to (file extensions, known interpreters)
    SCRIPT_TYPE_REGISTRY: ClassVar[Dict[str, tuple[set[str], set[str]]]] = {
        "shell": ({".sh", ".bash"}, {"sh", "bash"}),
        "python": ({".py"}, {"python", "python3"}),
    }

    def __init__(self, skills_config: Skills) -> None:
        """Initialize the SkillManager from a Skills configuration."""
        self._skills: Dict[str, RegisteredSkill] = {}
        self._config = skills_config
        self._allowed_commands: Set[str] = set(skills_config.allowed_commands)
        # Build allowed extensions and interpreters from configured script types
        self._allowed_extensions: Set[str] = set()
        self._allowed_interpreters: Set[str] = set()
        for script_type in skills_config.allowed_script_types:
            entry = self.SCRIPT_TYPE_REGISTRY.get(script_type)
            if entry:
                self._allowed_extensions.update(entry[0])
                self._allowed_interpreters.update(entry[1])
        self._load_skills_from_paths()
        self._load_skills_from_urls()
        self._load_skills_from_resources()

    @property
    def size(self) -> int:
        """Get the number of registered skills."""
        return len(self._skills)

    def get_skill(self, name: str) -> RegisteredSkill:
        """Get a registered skill by name."""
        if name not in self._skills:
            msg = f"Skill {name} not found, available skill names are: {list(self._skills.keys())}"
            raise ValueError(msg)
        return self._skills[name]

    def get_all_skill_names(self) -> List[str]:
        """Get the names of all registered skills."""
        return list(self._skills.keys())

    def load_skill_resource(self, skill_name: str, resource_path: str) -> str | None:
        """Load a specified resource of a skill."""
        skill = self.get_skill(skill_name)
        return skill.get_resource(resource_path)

    def generate_discovery_prompt(self, *names: str) -> str:
        """Generate a system prompt for skill discovery."""
        if self.size == 0:
            return ""

        skill_list = []
        for name in names:
            skill = self.get_skill(name)
            skill_list.append(
                SkillPromptProvider.AVAILABLE_SKILL_TEMPLATE.format(
                    name=skill.name, description=skill.description
                )
            )

        return (
            SkillPromptProvider.SKILL_DISCOVERY_PROMPT.format()
            + ("".join(skill_list))
            + SkillPromptProvider.AVAILABLE_SKILLS_TAG_END
        )

    def validate_command(self, skill_name: str, command: str) -> str | None:
        """Validate a command before execution.

        Returns None if the command is allowed, or an error message if rejected.

        If the command contains shell operators (``|``, ``&&``, ``;``, etc.),
        it is split into sub-commands and each is validated individually.

        For each sub-command:
        1. If it executes a skill script (directly or via interpreter),
           check that the script is a skill resource with an allowed extension.
        2. Otherwise, check the executable against the allowed_commands whitelist.
        """
        sub_commands = [s.strip() for s in self._split_commands(command) if s.strip()]
        if not sub_commands:
            return "Empty command."

        for sub_cmd in sub_commands:
            error = self._validate_single_command(skill_name, sub_cmd)
            if error is not None:
                return error
        return None

    def _validate_single_command(self, skill_name: str, command: str) -> str | None:
        """Validate a single command (no shell operators)."""
        tokens = shlex.split(command)
        if not tokens:
            return "Empty command."

        executable = tokens[0]

        # Case 1a: direct script execution — e.g. "scripts/run.sh arg1"
        if self.is_skill_resource(skill_name, executable):
            return self._validate_script_extension(executable)

        # Case 1b: interpreter + script — e.g. "python scripts/calc.py arg1"
        if executable in self._allowed_interpreters and len(tokens) > 1:
            script = tokens[1]
            if self.is_skill_resource(skill_name, script):
                return self._validate_script_extension(script)

        # Case 2: not a script — check allowed_commands whitelist
        if executable in self._allowed_commands:
            return None

        return (
            f"Command '{executable}' is not allowed. "
            f"Allowed commands: {sorted(self._allowed_commands)}."
        )

    def _validate_script_extension(self, script_path: str) -> str | None:
        """Check that a script has an allowed extension."""
        if any(script_path.endswith(ext) for ext in self._allowed_extensions):
            return None
        return (
            f"Script '{script_path}' has an unsupported type. "
            f"Allowed extensions: {sorted(self._allowed_extensions)}."
        )

    @staticmethod
    def _split_commands(command: str) -> List[str]:
        """Split a command string by shell operators, respecting quotes.

        Splits on ``&``, ``|``, ``;``, and newline outside of single/double
        quotes and backslash escapes. Returns a list of sub-command strings.
        """
        commands: List[str] = []
        current: List[str] = []
        in_single_quote = False
        in_double_quote = False
        escaped = False

        for ch in command:
            if escaped:
                escaped = False
                current.append(ch)
                continue

            if ch == "\\":
                escaped = True
                current.append(ch)
                continue

            if ch == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
                current.append(ch)
                continue

            if ch == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
                current.append(ch)
                continue

            if not in_single_quote and not in_double_quote and ch in ("&", "|", ";", "\n"):
                # Shell operator — flush current command
                commands.append("".join(current))
                current = []
                continue

            current.append(ch)

        commands.append("".join(current))
        return commands

    def is_skill_resource(self, skill_name: str, resource_path: str) -> bool:
        """Check if a path is a known resource of the given skill."""
        skill = self.get_skill(skill_name)
        return resource_path in skill.get_resource_paths()

    def resolve_resource_path(self, skill_name: str, resource_path: str) -> Path | None:
        """Resolve a skill resource's relative path to an absolute filesystem path.

        Returns None if the skill's repository doesn't support path resolution.
        """
        skill = self.get_skill(skill_name)
        repo = skill.repo
        if isinstance(repo, FileSystemSkillRepository):
            resolved = repo.base_dir / skill_name / resource_path
            if resolved.exists() and resolved.is_file():
                return resolved
        return None

    def _load_skills_from_paths(self) -> None:
        for path in self._config.paths:
            repo = FileSystemSkillRepository(path)
            for skill in repo.get_skills():
                self._skills[skill.name] = RegisteredSkill(agent_skill=skill, repo=repo)

    def _load_skills_from_resources(self) -> None:
        # TODO: Implement
        pass

    def _load_skills_from_urls(self) -> None:
        # TODO: Implement
        pass
