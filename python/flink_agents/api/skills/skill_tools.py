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
import logging
import subprocess
from typing import Any, cast

from pydantic import BaseModel, Field

from flink_agents.api.resource import ResourceType
from flink_agents.api.skills.skill_manager import SKILL_MANAGER, BaseAgentSkillManager
from flink_agents.api.tools.tool import Tool, ToolMetadata, ToolType

logger = logging.getLogger(__name__)


class LoadSkillArgs(BaseModel):
    """Arguments for LoadSkillTool.

    Attributes:
    ----------
    name : str
        The name of the skill to load.
    path : Optional[str]
        Optional path to a specific resource within the skill.
    """

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

    This tool allows agents to load a skill's full SKILL.md content
    (activates the skill), load specific resources from a skill, and
    list available resources when resource not found.

    When a skill is loaded without a resource_path, the skill is automatically
    activated, making its full content available in the conversation context.
    """

    metadata: ToolMetadata = Field(exclude=True)

    def __init__(self, **kwargs: Any) -> None:
        """Initialize method for load skill tool."""
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

    def call(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Call the tool to load a skill."""
        # Parse arguments
        if args:
            parsed_args = LoadSkillArgs(name=args[0], **kwargs)
        else:
            parsed_args = LoadSkillArgs(**kwargs)

        skill_name = parsed_args.name
        resource_path = parsed_args.path
        logger.debug(f"Loading skill resource {resource_path} for {skill_name}.")

        # Get skill manager from the tool's context
        manager: BaseAgentSkillManager = self._get_skill_manager()
        if manager is None:
            return "Skill manager not available. No skills have been registered."

        # Get the skill
        skill = manager.get_skill(skill_name)
        if skill is None:
            # List available skills
            available = list(manager.get_all_skill_names())
            available_str = (
                ", ".join(available) if available else "No skills available."
            )
            return f"Skill '{skill_name}' not found. Available skills: {available_str}"

        if resource_path is None or resource_path == "SKILL.md":
            return skill.content

        content = skill.get_resource(resource_path)
        if content is None:
            # List available resources
            available = sorted(skill.get_resource_paths())
            return f"Resource '{resource_path}' not found in skill '{skill_name}', Available resources: {available}"
        return content

    def _get_skill_manager(self) -> BaseAgentSkillManager:
        """Get the skill manager from the resource context.

        Returns:
            The skill manager, or None if not available.
        """
        return cast(
            "BaseAgentSkillManager",
            self.get_resource(SKILL_MANAGER, ResourceType.SKILL),
        )


class ShellCommandArgs(BaseModel):
    """Arguments for ExecBashTool.

    Attributes:
    ----------
    command : str
        The bash command to execute.
    timeout : int | None
        Optional timeout in seconds. Defaults to 60 seconds.
    """

    command: str = Field(..., description="The shell command to execute.")
    timeout: int | None = Field(
        default=60,
        description="Optional timeout in seconds. Defaults to 60 seconds.",
    )


class ExecuteShellCommandTool(Tool):
    """Tool for executing shell commands.

    This tool allows agents to execute shell commands and return the result
    or error message.
    """

    metadata: ToolMetadata = Field(exclude=True)

    def __init__(self, **kwargs: Any) -> None:
        """Initialize method for execute shell command tool."""
        super().__init__(
            metadata=ToolMetadata(
                name="exec_shell_command",
                description=(
                    "Execute a shell command and return the result. "
                    "Returns stdout on success, or stderr on failure."
                ),
                args_schema=ShellCommandArgs,
            ),
            **kwargs,
        )

    @classmethod
    def tool_type(cls) -> ToolType:
        """Return tool type of class."""
        return ToolType.FUNCTION

    def call(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Call the tool to execute a bash command."""
        # Parse arguments
        if args:
            parsed_args = ShellCommandArgs(command=args[0], **kwargs)
        else:
            parsed_args = ShellCommandArgs(**kwargs)

        command = parsed_args.command
        timeout = parsed_args.timeout
        logger.debug(f"Executing command: {command} with timeout: {timeout}")
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

LOAD_SKILL_TOOL = "load_skill"
EXEC_SHELL_COMMAND_TOOL = "exec_shell_command"
