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
"""Built-in tools for skill loading and shell execution.

These are internal runtime tools registered automatically when skills are
configured. They access the SkillManager through the runtime ResourceContext.
"""

from __future__ import annotations

import logging
import subprocess
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from flink_agents.runtime.skill.skill_manager import SkillManager

from pydantic import BaseModel, Field
from typing_extensions import override

from flink_agents.api.tools.tool import Tool, ToolMetadata, ToolType

logger = logging.getLogger(__name__)


class LoadSkillArgs(BaseModel):
    """Arguments for LoadSkillTool."""

    name: str = Field(
        ..., description="The name of the skill to load (e.g., 'pdf-processing')."
    )
    path: str | None = Field(
        default="SKILL.md",
        description=(
            "Optional path to a specific resource within the skill. "
            "If not provided, returns the full SKILL.md content."
        ),
    )


class LoadSkillTool(Tool):
    """Tool for loading skill content and resources.

    Accesses the SkillManager through the runtime ResourceContext
    (not the public ResourceContext interface).
    """

    metadata: ToolMetadata = Field(exclude=True)

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the load skill tool."""
        super().__init__(
            metadata=ToolMetadata(
                name="load_skill",
                description=(
                    "Load a skill's content or a specific resource. "
                    "Use this to access skill instructions and resources. "
                ),
                args_schema=LoadSkillArgs,
            ),
            **kwargs,
        )

    @classmethod
    def tool_type(cls) -> ToolType:
        """Return tool type of class."""
        return ToolType.FUNCTION

    def call(self, *args: Any, **kwargs: Any) -> str:
        """Call the tool to load a skill."""
        if args:
            parsed_args = LoadSkillArgs(name=args[0], **kwargs)
        else:
            parsed_args = LoadSkillArgs(**kwargs)

        skill_name = parsed_args.name
        resource_path = parsed_args.path
        logger.debug(f"Loading skill resource {resource_path} for {skill_name}.")

        manager = self._get_skill_manager()
        if manager is None:
            return "Skill manager not available. No skills have been registered."

        try:
            skill = manager.get_skill(skill_name)
        except ValueError:
            available = manager.get_all_skill_names()
            available_str = (
                ", ".join(available) if available else "No skills available."
            )
            return f"Skill '{skill_name}' not found. Available skills: {available_str}"

        if resource_path is None or resource_path == "SKILL.md":
            return skill.content

        content = skill.get_resource(resource_path)
        if content is None:
            available = sorted(skill.get_resource_paths())
            return f"Resource '{resource_path}' not found in skill '{skill_name}', Available resources: {available}"
        return content

    def _get_skill_manager(self) -> SkillManager | None:
        from flink_agents.runtime.resource_context import ResourceContextImpl

        ctx = self.resource_context
        if isinstance(ctx, ResourceContextImpl):
            return ctx.get_skill_manager()
        return None


class ExecuteCommandArgs(BaseModel):
    """Arguments for ExecuteCommandTool."""

    skill_name: str = Field(
        ..., description="The name of the skill this command belongs to."
    )
    command: str = Field(
        ...,
        description=(
            "The command to execute. Must be either a whitelisted command "
            "(e.g., 'gh issue list') or a script from the skill's resources "
            "(e.g., 'scripts/run.sh arg1 arg2')."
        ),
    )
    timeout: int = Field(
        default=60,
        description="Timeout in seconds. Defaults to 60.",
    )


class ExecuteCommandTool(Tool):
    """Tool for executing commands within the scope of a skill.

    Security:
    - The executable (first token) must be in the allowed_commands whitelist,
      OR be a script that is a known resource of the skill.
    - File arguments that reference paths inside the skill directory must
      be known skill resources.
    """

    metadata: ToolMetadata = Field(exclude=True)

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the tool."""
        super().__init__(
            metadata=ToolMetadata(
                name="execute_command",
                description=(
                    "Execute a command within the scope of a skill. "
                    "Only whitelisted commands and pre-defined skill scripts "
                    "are allowed. Use load_skill first to discover available "
                    "scripts and resources."
                ),
                args_schema=ExecuteCommandArgs,
            ),
            **kwargs,
        )

    @classmethod
    @override
    def tool_type(cls) -> ToolType:
        """Return tool type of class."""
        return ToolType.FUNCTION

    @override
    def call(self, *args: Any, **kwargs: Any) -> str:
        """Execute the command after validation."""
        if args:
            parsed_args = ExecuteCommandArgs(skill_name=args[0], **kwargs)
        else:
            parsed_args = ExecuteCommandArgs(**kwargs)

        skill_name = parsed_args.skill_name
        command = parsed_args.command
        timeout = parsed_args.timeout

        manager = self._get_skill_manager()
        if manager is None:
            return "Skill manager not available. No skills have been registered."

        # Validate skill exists
        try:
            manager.get_skill(skill_name)
        except ValueError:
            return f"Skill '{skill_name}' not found."

        # Validate command against whitelist and resource checks
        error = manager.validate_command(skill_name, command)
        if error is not None:
            return f"Command rejected: {error}"

        # Resolve skill script paths to absolute paths for execution
        command = self._resolve_command(manager, skill_name, command)

        logger.debug(
            f"Executing command for skill '{skill_name}': {command} "
            f"(timeout={timeout}s)"
        )
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode == 0:
                return result.stdout.strip() if result.stdout.strip() else "Success"
            else:
                return f"Error (exit code {result.returncode}): {result.stderr.strip()}"
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {timeout} seconds"
        except Exception as e:
            return f"Error: {e!s}"

    def _resolve_command(
        self, manager: SkillManager, skill_name: str, command: str,
    ) -> str:
        """Resolve relative skill script paths to absolute paths.

        Performs string replacement on the original command to preserve
        shell syntax (quotes, pipes, etc.).
        """
        skill = manager.get_skill(skill_name)
        for resource_path in skill.get_resource_paths():
            if resource_path in command:
                absolute = manager.resolve_resource_path(skill_name, resource_path)
                if absolute is not None:
                    command = command.replace(resource_path, str(absolute))
        return command

    def _get_skill_manager(self) -> SkillManager | None:
        from flink_agents.runtime.resource_context import ResourceContextImpl

        ctx = self.resource_context
        if isinstance(ctx, ResourceContextImpl):
            return ctx.get_skill_manager()
        return None
