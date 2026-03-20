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
from typing import Any, ClassVar, List

from pydantic import BaseModel, Field

from flink_agents.api.resource import ResourceType
from flink_agents.api.skills.skill_manager import AgentSkillManager
from flink_agents.api.tools.tool import Tool, ToolMetadata, ToolType


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


class LoadSkillResult(BaseModel):
    """Result of loading a skill.

    Attributes:
    ----------
    success : bool
        Whether the skill was loaded successfully.
    content : Optional[str]
        The loaded content (SKILL.md or resource).
    skill_name : Optional[str]
        The skill name.
    available_resources : Optional[List[str]]
        List of available resource paths in the skill.
    error : Optional[str]
        Error message if failed.
    activated : bool
        Whether the skill was activated.
    """

    success: bool = Field(..., description="Whether the skill was loaded successfully.")
    content: str | None = Field(
        default=None, description="The loaded content (SKILL.md or resource)."
    )
    skill_name: str | None = Field(default=None, description="The skill name.")
    available_resources: List[str] | None = Field(
        default=None, description="List of available resource paths in the skill."
    )
    error: str | None = Field(default=None, description="Error message if failed.")
    activated: bool = Field(
        default=False, description="Whether the skill was activated."
    )


class LoadSkillTool(Tool):
    """Tool for loading skill content and resources.

    This tool allows agents to load a skill's full SKILL.md content
    (activates the skill), load specific resources from a skill, and
    list available resources when resource not found.

    When a skill is loaded without a resource_path, the skill is automatically
    activated, making its full content available in the conversation context.
    """

    def __init__(self):
        super().__init__(
            metadata=ToolMetadata(
                name="load_skill",
                description=(
                    "Load a skill's content or a specific resource. "
                    "Use this to access skill instructions and resources. "
                    "When loading the full skill (without resource_path), the skill is activated."
                ),
                args_schema=LoadSkillArgs,
            )
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

        # Get skill manager from the tool's context
        manager: AgentSkillManager = self._get_skill_manager()
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

    def _get_skill_manager(self) -> Any | None:
        """Get the skill manager from the resource context.

        Returns:
            The skill manager, or None if not available.
        """
        return self.get_resource("_skill_manager", ResourceType.SKILL)


class LoadSkillResourceArgs(BaseModel):
    """Arguments for LoadSkillResourceTool.

    Attributes:
    ----------
    skill_name : str
        The name of the skill.
    resource_path : str
        The path to the resource within the skill.
    """

    skill_name: str = Field(..., description="The name of the skill.")
    resource_path: str = Field(
        ...,
        description="The path to the resource within the skill (e.g., 'scripts/run.sh').",
    )


class LoadSkillResourceTool(Tool):
    """Tool for loading specific resources from skills.

    This tool is focused on loading individual resources from skills.
    It does not activate the skill.

    Example:
        >>> result = load_skill_resource(
        ...     skill_name="pdf-processing", resource_path="scripts/extract.py"
        ... )
        >>> print(result.content)
    """

    SKILL_MANAGER_ATTR: ClassVar[str] = "_skill_manager"

    metadata: ToolMetadata = Field(
        default=ToolMetadata(
            name="load_skill_resource",
            description=(
                "Load a specific resource file from a skill. "
                "Use this to access scripts, references, or other files within a skill."
            ),
            args_schema=LoadSkillResourceArgs,
        )
    )

    @classmethod
    def tool_type(cls) -> ToolType:
        """Return tool type of class."""
        return ToolType.FUNCTION

    def call(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> LoadSkillResult:
        """Call the tool to load a skill resource.

        Args:
            skill_name: The name of the skill.
            resource_path: The path to the resource.

        Returns:
            The result containing the resource content or error.
        """
        # Parse arguments
        if len(args) >= 2:
            parsed_args = LoadSkillResourceArgs(
                skill_name=args[0], resource_path=args[1], **kwargs
            )
        else:
            parsed_args = LoadSkillResourceArgs(**kwargs)

        skill_name = parsed_args.skill_name
        resource_path = parsed_args.resource_path

        # Get skill manager
        manager = self._get_skill_manager()
        if manager is None:
            return LoadSkillResult(
                success=False,
                error="Skill manager not available.",
            )

        # Get the skill
        skill = manager.get_skill_by_name(skill_name)
        if skill is None:
            return LoadSkillResult(
                success=False,
                skill_name=skill_name,
                error=f"Skill '{skill_name}' not found.",
            )

        # Load the resource
        content = skill.get_resource(resource_path)
        if content is None:
            available = sorted(skill.get_resource_paths())
            return LoadSkillResult(
                success=False,
                skill_name=skill_name,
                available_resources=available,
                error=f"Resource '{resource_path}' not found. Available: {available}",
            )

        return LoadSkillResult(
            success=True,
            content=content,
            skill_name=skill_name,
            available_resources=sorted(skill.get_resource_paths()),
        )

    def _get_skill_manager(self) -> Any | None:
        """Get the skill manager from the resource context.

        Returns:
            The skill manager, or None if not available.
        """
        if hasattr(self, self.SKILL_MANAGER_ATTR):
            return getattr(self, self.SKILL_MANAGER_ATTR)

        if self.get_resource is not None:
            try:
                return self.get_resource("_skill_manager", ResourceType.SKILL)
            except Exception:
                pass

        return None


def create_skill_tools(skill_manager: Any) -> List[Tool]:
    """Create skill tools with a skill manager.

    Args:
        skill_manager: The skill manager to use for loading skills.

    Returns:
        List of skill tools.
    """
    load_skill = LoadSkillTool()
    setattr(load_skill, LoadSkillTool.SKILL_MANAGER_ATTR, skill_manager)

    load_resource = LoadSkillResourceTool()
    setattr(load_resource, LoadSkillResourceTool.SKILL_MANAGER_ATTR, skill_manager)

    return [load_skill, load_resource]
