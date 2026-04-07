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
"""Skills configuration resource for agent skills discovery.

Example usage::

    @skills
    @staticmethod
    def my_skills() -> Skills:
        return Skills(paths=["./skills"])

    @skills
    @staticmethod
    def combined() -> Skills:
        return Skills(paths=["./local"], urls=["https://example.com/skills"])
"""
from __future__ import annotations

from typing import List

from pydantic import Field
from typing_extensions import override

from flink_agents.api.resource import ResourceType, SerializableResource


class Skills(SerializableResource):
    """A resource that stores skill location configuration.

    This is the user-facing API for defining where skills are located.
    The runtime will use this configuration to discover and load skills
    at initialization time, creating an internal SkillManager.

    Example::

        Skills(paths=["./skills"], allowed_commands=["gh", "git"])
        Skills(paths=["./local"], urls=["https://example.com/skills"])

    Attributes:
        paths: List of filesystem paths to load skills from.
        urls: List of URLs to load skills from.
        resources: List of Python package resources to load skills from.
        allowed_script_types: Script types that are allowed to execute
            from skill directories. Defaults to ``["shell", "python"]``.
            Supported types: ``"shell"`` (.sh, .bash), ``"python"`` (.py).
        allowed_commands: Whitelist of executable command names that skills
            are permitted to run when the command is not a skill script.
            Only the first token of a command is checked against this list.
    """

    paths: List[str] = Field(default_factory=list)
    urls: List[str] = Field(default_factory=list)
    resources: List[str] = Field(default_factory=list)
    allowed_script_types: List[str] = Field(
        default_factory=lambda: ["shell", "python"]
    )
    allowed_commands: List[str] = Field(default_factory=list)

    @classmethod
    @override
    def resource_type(cls) -> ResourceType:
        """Return resource type of class."""
        return ResourceType.SKILL


# name of built-in tools needed by using skills
LOAD_SKILL_TOOL = "load_skill"
EXECUTE_COMMAND_TOOL = "execute_command"
