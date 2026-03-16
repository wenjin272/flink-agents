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
"""Agent Skill module for defining and managing agent skills.

This module provides the AgentSkill class which represents a skill that can be
loaded and used by agents. A skill consists of metadata (name, description, etc.)
and content (instructions and resources).

Skills follow the Agent Skills specification from https://agentskills.io/
"""
from typing import Dict

from pydantic import BaseModel, Field, field_validator, model_validator


class AgentSkill(BaseModel):
    """Represents an agent skill that can be loaded and used by agents.

    A skill consists of:
    - Name and description: Identifying the skill
    - Skill content: The actual skill implementation or instructions
    - Resources: Supporting files or data referenced by the skill
    - Source: Tracking skill origin

    Attributes:
    ----------
    name : str
        Skill name (1-64 characters, lowercase letters, numbers, hyphens only).
        Must not start or end with a hyphen.
    description : str
        Skill description (1-1024 characters). Describes what the skill does
        and when to use it.
    skill_content : str
        The skill implementation or instructions (the markdown body after
        frontmatter in SKILL.md).
    resources : Dict[str, str]
        Supporting resources referenced by the skill. Keys are relative paths
        from the skill root, values are file contents.
    source : str
        Source identifier for the skill (e.g., "filesystem", "classpath",
        "url-xxx").
    license : Optional[str]
        License name or reference to a bundled license file.
    compatibility : Optional[str]
        Environment requirements (max 500 characters).
    metadata : Optional[Dict[str, str]]
        Additional metadata not defined by the spec.
    allowed_tools : Optional[str]
        Space-delimited list of pre-approved tools the skill may use.

    Example:
    -------
    >>> skill = AgentSkill(
    ...     name="pdf-processing",
    ...     description="Extract PDF text, fill forms, merge files.",
    ...     skill_content="Instructions for PDF processing...",
    ...     resources={"scripts/extract.py": "#!/usr/bin/env python3..."},
    ...     source="filesystem"
    ... )
    >>> skill.skill_id
    'pdf-processing_filesystem'
    """

    name: str = Field(..., min_length=1, max_length=64)
    description: str = Field(..., min_length=1, max_length=1024)
    skill_content: str = Field(..., min_length=1)
    resources: Dict[str, str] = Field(default_factory=dict)
    source: str = Field(default="custom")
    license: str | None = Field(default=None)
    compatibility: str | None = Field(default=None, max_length=500)
    metadata: Dict[str, str] | None = Field(default=None)
    allowed_tools: str | None = Field(default=None)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate skill name follows the specification.

        - 1-64 characters
        - Lowercase letters (a-z), numbers (0-9), and hyphens (-) only
        - Must not start or end with a hyphen
        - Must not contain consecutive hyphens
        """
        if not v:
            raise ValueError("Skill name cannot be empty")

        if len(v) > 64:
            raise ValueError(f"Skill name must be at most 64 characters, got {len(v)}")

        if v.startswith("-") or v.endswith("-"):
            raise ValueError(f"Skill name must not start or end with hyphen: {v}")

        if "--" in v:
            raise ValueError(f"Skill name must not contain consecutive hyphens: {v}")

        import re
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                f"Skill name must contain only lowercase letters, numbers, "
                f"and hyphens: {v}"
            )

        return v

    @model_validator(mode="after")
    def validate_metadata(self) -> "AgentSkill":
        """Ensure metadata is a valid mapping if provided."""
        if self.metadata is not None:
            for key, value in self.metadata.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise ValueError(
                        f"Metadata must be string key-value pairs, "
                        f"got {type(key)}:{type(value)}"
                    )
        return self

    @property
    def skill_id(self) -> str:
        """Get a unique identifier for this skill.

        The ID is composed of name and source: "name_source".
        """
        return f"{self.name}_{self.source}"

    def get_resource(self, resource_path: str) -> str | None:
        """Get resource content by path.

        Parameters
        ----------
        resource_path : str
            The relative path of the resource from skill root.

        Returns:
        -------
        Optional[str]
            The resource content, or None if not found.
        """
        return self.resources.get(resource_path)

    def get_resource_paths(self) -> set[str]:
        """Get all resource paths for this skill.

        Returns:
        -------
        Set[str]
            Set of resource paths.
        """
        return set(self.resources.keys())

    def to_builder(self) -> "AgentSkillBuilder":
        """Create a builder initialized with this skill's values.

        Useful for creating modified versions of existing skills.

        Returns:
        -------
        AgentSkillBuilder
            A new builder instance.
        """
        return AgentSkillBuilder(base_skill=self)

    @classmethod
    def builder(cls) -> "AgentSkillBuilder":
        """Create a new builder for creating a skill from scratch.

        Returns:
        -------
        AgentSkillBuilder
            A new builder instance with empty fields.
        """
        return AgentSkillBuilder()

    def __str__(self) -> str:
        """Return string representation of this skill."""
        return (
            f"AgentSkill{{name='{self.name}', description='{self.description}', "
            f"source='{self.source}'}}"
        )


class AgentSkillBuilder:
    """Builder for creating AgentSkill instances.

    This builder allows selective modification of skill fields to create
    new skill instances based on existing ones, or to create new skills
    from scratch.

    Example:
    -------
    >>> # Create from scratch
    >>> skill = (AgentSkill.builder()
    ...     .name("my_skill")
    ...     .description("Does something")
    ...     .skill_content("Instructions here")
    ...     .add_resource("file.txt", "content")
    ...     .build())

    >>> # Modify existing skill
    >>> modified = (skill.to_builder()
    ...     .description("Updated description")
    ...     .add_resource("new_file.txt", "new content")
    ...     .build())
    """

    def __init__(self, base_skill: AgentSkill | None = None) -> None:
        """Initialize the builder.

        Parameters
        ----------
        base_skill : Optional[AgentSkill]
            Existing skill to copy values from, or None to start fresh.
        """
        if base_skill is not None:
            self._name = base_skill.name
            self._description = base_skill.description
            self._skill_content = base_skill.skill_content
            self._resources = dict(base_skill.resources)
            self._source = base_skill.source
            self._license = base_skill.license
            self._compatibility = base_skill.compatibility
            self._metadata = dict(base_skill.metadata) if base_skill.metadata else None
            self._allowed_tools = base_skill.allowed_tools
        else:
            self._name: str | None = None
            self._description: str | None = None
            self._skill_content: str | None = None
            self._resources: Dict[str, str] = {}
            self._source: str = "custom"
            self._license: str | None = None
            self._compatibility: str | None = None
            self._metadata: Dict[str, str] | None = None
            self._allowed_tools: str | None = None

    def name(self, name: str) -> "AgentSkillBuilder":
        """Set the skill name.

        Parameters
        ----------
        name : str
            The skill name.

        Returns:
        -------
        AgentSkillBuilder
            This builder for chaining.
        """
        self._name = name
        return self

    def description(self, description: str) -> "AgentSkillBuilder":
        """Set the skill description.

        Parameters
        ----------
        description : str
            The skill description.

        Returns:
        -------
        AgentSkillBuilder
            This builder for chaining.
        """
        self._description = description
        return self

    def skill_content(self, skill_content: str) -> "AgentSkillBuilder":
        """Set the skill content.

        Parameters
        ----------
        skill_content : str
            The skill content/instructions.

        Returns:
        -------
        AgentSkillBuilder
            This builder for chaining.
        """
        self._skill_content = skill_content
        return self

    def resources(self, resources: Dict[str, str]) -> "AgentSkillBuilder":
        """Replace all resources with a new map.

        Parameters
        ----------
        resources : Dict[str, str]
            The new resources map.

        Returns:
        -------
        AgentSkillBuilder
            This builder for chaining.
        """
        self._resources = dict(resources)
        return self

    def add_resource(self, path: str, content: str) -> "AgentSkillBuilder":
        """Add or update a single resource.

        Parameters
        ----------
        path : str
            The resource path.
        content : str
            The resource content.

        Returns:
        -------
        AgentSkillBuilder
            This builder for chaining.
        """
        self._resources[path] = content
        return self

    def remove_resource(self, path: str) -> "AgentSkillBuilder":
        """Remove a resource.

        Parameters
        ----------
        path : str
            The resource path to remove.

        Returns:
        -------
        AgentSkillBuilder
            This builder for chaining.
        """
        self._resources.pop(path, None)
        return self

    def clear_resources(self) -> "AgentSkillBuilder":
        """Clear all resources.

        Returns:
        -------
        AgentSkillBuilder
            This builder for chaining.
        """
        self._resources.clear()
        return self

    def source(self, source: str) -> "AgentSkillBuilder":
        """Set the source identifier.

        Parameters
        ----------
        source : str
            The source identifier.

        Returns:
        -------
        AgentSkillBuilder
            This builder for chaining.
        """
        self._source = source
        return self

    def license(self, license: str | None) -> "AgentSkillBuilder":
        """Set the license.

        Parameters
        ----------
        license : Optional[str]
            The license name or reference.

        Returns:
        -------
        AgentSkillBuilder
            This builder for chaining.
        """
        self._license = license
        return self

    def compatibility(self, compatibility: str | None) -> "AgentSkillBuilder":
        """Set the compatibility information.

        Parameters
        ----------
        compatibility : Optional[str]
            The compatibility requirements.

        Returns:
        -------
        AgentSkillBuilder
            This builder for chaining.
        """
        self._compatibility = compatibility
        return self

    def metadata(self, metadata: Dict[str, str] | None) -> "AgentSkillBuilder":
        """Set additional metadata.

        Parameters
        ----------
        metadata : Optional[Dict[str, str]]
            Additional metadata key-value pairs.

        Returns:
        -------
        AgentSkillBuilder
            This builder for chaining.
        """
        self._metadata = dict(metadata) if metadata else None
        return self

    def add_metadata(self, key: str, value: str) -> "AgentSkillBuilder":
        """Add a single metadata entry.

        Parameters
        ----------
        key : str
            The metadata key.
        value : str
            The metadata value.

        Returns:
        -------
        AgentSkillBuilder
            This builder for chaining.
        """
        if self._metadata is None:
            self._metadata = {}
        self._metadata[key] = value
        return self

    def allowed_tools(self, allowed_tools: str | None) -> "AgentSkillBuilder":
        """Set the allowed tools.

        Parameters
        ----------
        allowed_tools : Optional[str]
            Space-delimited list of pre-approved tools.

        Returns:
        -------
        AgentSkillBuilder
            This builder for chaining.
        """
        self._allowed_tools = allowed_tools
        return self

    def build(self) -> AgentSkill:
        """Build the AgentSkill instance.

        Returns:
        -------
        AgentSkill
            A new AgentSkill instance.

        Raises:
        ------
        ValueError
            If required fields (name, description, skill_content) are missing.
        """
        if not self._name:
            raise ValueError("Skill name is required")
        if not self._description:
            raise ValueError("Skill description is required")
        if not self._skill_content:
            raise ValueError("Skill content is required")

        return AgentSkill(
            name=self._name,
            description=self._description,
            skill_content=self._skill_content,
            resources=self._resources,
            source=self._source,
            license=self._license,
            compatibility=self._compatibility,
            metadata=self._metadata,
            allowed_tools=self._allowed_tools,
        )


class RegisteredSkill(BaseModel):
    """Wrapper class for tracking skill registration state.

    This class wraps an AgentSkill and tracks whether it's currently
    active (being used by the LLM).

    Attributes:
    ----------
    skill_id : str
        The unique identifier of the skill.
    active : bool
        Whether the skill is currently active.
    tools_group_name : str
        The name of the tool group associated with this skill.
    """

    skill_id: str
    active: bool = Field(default=False)
    tools_group_name: str = Field(default="")

    def set_active(self, active: bool) -> None:
        """Set the activation state of the skill.

        Parameters
        ----------
        active : bool
            Whether to activate the skill.
        """
        self.active = active

    @model_validator(mode="after")
    def set_default_tools_group_name(self) -> "RegisteredSkill":
        """Set default tools group name if not provided."""
        if not self.tools_group_name:
            self.tools_group_name = f"{self.skill_id}_skill_tools"
        return self
