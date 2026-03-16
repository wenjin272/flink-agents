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
"""Built-in tools for Agent Skills.

This module provides tools that agents can use to interact with skills:
- LoadSkillTool: Load a skill's full content
- LoadSkillResourceTool: Load a specific resource from a skill
"""
from typing import Any, ClassVar, List

from pydantic import BaseModel, Field

from flink_agents.api.resource import ResourceType
from flink_agents.api.tools.tool import Tool, ToolMetadata, ToolType


class LoadSkillArgs(BaseModel):
    """Arguments for LoadSkillTool."""

    skill_name: str = Field(
        ...,
        description="The name of the skill to load (e.g., 'pdf-processing')."
    )
    resource_path: str | None = Field(
        default=None,
        description=(
            "Optional path to a specific resource within the skill. "
            "If not provided, returns the full SKILL.md content."
        )
    )


class LoadSkillResult(BaseModel):
    """Result of loading a skill."""

    success: bool = Field(..., description="Whether the skill was loaded successfully.")
    content: str | None = Field(
        default=None,
        description="The loaded content (SKILL.md or resource)."
    )
    skill_name: str | None = Field(default=None, description="The skill name.")
    available_resources: List[str] | None = Field(
        default=None,
        description="List of available resource paths in the skill."
    )
    error: str | None = Field(default=None, description="Error message if failed.")
    activated: bool = Field(
        default=False,
        description="Whether the skill was activated."
    )


class LoadSkillTool(Tool):
    """Tool for loading skill content and resources.

    This tool allows agents to:
    1. Load a skill's full SKILL.md content (activates the skill)
    2. Load specific resources from a skill
    3. List available resources when resource not found

    When a skill is loaded without a resource_path, the skill is automatically
    activated, making its full content available in the conversation context.

    Example:
    -------
    >>> # Load full skill content
    >>> result = load_skill(skill_name="pdf-processing")
    >>> print(result.content)

    >>> # Load a specific resource
    >>> result = load_skill(skill_name="pdf-processing", resource_path="scripts/extract.py")
    >>> print(result.content)
    """

    SKILL_MANAGER_ATTR: ClassVar[str] = "_skill_manager"

    metadata: ToolMetadata = Field(
        default=ToolMetadata(
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
    ) -> LoadSkillResult:
        """Call the tool to load a skill.

        Parameters
        ----------
        skill_name : str
            The name of the skill to load.
        resource_path : Optional[str]
            Optional path to a specific resource.

        Returns:
        -------
        LoadSkillResult
            The result containing the loaded content or error.
        """
        # Parse arguments
        if args:
            parsed_args = LoadSkillArgs(skill_name=args[0], **kwargs)
        else:
            parsed_args = LoadSkillArgs(**kwargs)

        skill_name = parsed_args.skill_name
        resource_path = parsed_args.resource_path

        # Get skill manager from the tool's context
        manager = self._get_skill_manager()
        if manager is None:
            return LoadSkillResult(
                success=False,
                error="Skill manager not available. No skills have been registered.",
            )

        # Get the skill
        skill = manager.get_skill_by_name(skill_name)
        if skill is None:
            # List available skills
            available = list(manager.get_all_skill_names())
            available_str = ", ".join(available) if available else "No skills available."
            return LoadSkillResult(
                success=False,
                skill_name=skill_name,
                error=f"Skill '{skill_name}' not found. Available skills: {available_str}",
            )

        # Load specific resource if requested
        if resource_path:
            content = skill.get_resource(resource_path)
            if content is None:
                # List available resources
                available = sorted(skill.get_resource_paths())
                return LoadSkillResult(
                    success=False,
                    skill_name=skill_name,
                    available_resources=available if available else [],
                    error=(
                        f"Resource '{resource_path}' not found in skill '{skill_name}'. "
                        f"Available resources: {available}"
                    ),
                )
            return LoadSkillResult(
                success=True,
                content=content,
                skill_name=skill_name,
                available_resources=sorted(skill.get_resource_paths()),
            )

        # Load full skill content (SKILL.md body)
        # Activate the skill
        manager.activate_skill(skill.skill_id)

        return LoadSkillResult(
            success=True,
            content=skill.skill_content,
            skill_name=skill_name,
            available_resources=sorted(skill.get_resource_paths()),
            activated=True,
        )

    def _get_skill_manager(self) -> Any | None:
        """Get the skill manager from the resource context.

        Returns:
        -------
        Optional[AgentSkillManager]
            The skill manager, or None if not available.
        """
        if hasattr(self, self.SKILL_MANAGER_ATTR):
            return getattr(self, self.SKILL_MANAGER_ATTR)

        # Try to get from get_resource callback
        if self.get_resource is not None:
            try:
                manager = self.get_resource("_skill_manager", ResourceType.SKILL)
                return manager
            except Exception:
                pass

        return None


class LoadSkillResourceArgs(BaseModel):
    """Arguments for LoadSkillResourceTool."""

    skill_name: str = Field(
        ...,
        description="The name of the skill."
    )
    resource_path: str = Field(
        ...,
        description="The path to the resource within the skill (e.g., 'scripts/run.sh')."
    )


class LoadSkillResourceTool(Tool):
    """Tool for loading specific resources from skills.

    This tool is focused on loading individual resources from skills.
    It does not activate the skill.

    Example:
    -------
    >>> result = load_skill_resource(skill_name="pdf-processing", resource_path="scripts/extract.py")
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

        Parameters
        ----------
        skill_name : str
            The name of the skill.
        resource_path : str
            The path to the resource.

        Returns:
        -------
        LoadSkillResult
            The result containing the resource content or error.
        """
        # Parse arguments
        if len(args) >= 2:
            parsed_args = LoadSkillResourceArgs(skill_name=args[0], resource_path=args[1], **kwargs)
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
        -------
        Optional[AgentSkillManager]
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

    Parameters
    ----------
    skill_manager : AgentSkillManager
        The skill manager to use for loading skills.

    Returns:
    -------
    List[Tool]
        List of skill tools.
    """
    load_skill = LoadSkillTool()
    setattr(load_skill, LoadSkillTool.SKILL_MANAGER_ATTR, skill_manager)

    load_resource = LoadSkillResourceTool()
    setattr(load_resource, LoadSkillResourceTool.SKILL_MANAGER_ATTR, skill_manager)

    return [load_skill, load_resource]
