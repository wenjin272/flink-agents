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
from typing import Dict

from pydantic import BaseModel, Field

from flink_agents.api.skills.repository.skill_repository import SkillRepository

class AgentSkill(BaseModel):
    """Represents an agent skill that can be loaded and used by agents.

    Attributes:
    ----------
    name : str
        Skill name (1-64 characters, lowercase letters, numbers, hyphens only).
        Must not start or end with a hyphen.
    description : str
        Skill description (1-1024 characters). Describes what the skill does
        and when to use it.
    license : Optional[str]
        License name or reference to a bundled license file.
    compatibility : Optional[str]
        Indicates environment requirements (intended product, system packages,
        network access, etc.) (max 500 characters).
    metadata : Optional[Dict[str, str]]
        Arbitrary key-value mapping for additional metadata.
    skill_content : str
        The skill implementation or instructions (the markdown body after
        frontmatter in SKILL.md).
    resources : Dict[str, str]
        Supporting resources referenced by the skill. Keys are relative paths
        from the skill root, values are file contents.
    """
    name: str = Field(..., min_length=1, max_length=64)
    description: str = Field(..., min_length=1, max_length=1024)
    license: str | None = Field(default=None)
    compatibility: str | None = Field(default=None, max_length=500)
    metadata: Dict[str, str] | None = Field(default=None)
    content: str = Field(..., min_length=1)
    
    _repo: SkillRepository | None = None
    _resources: Dict[str, str] | None = None

    def get_resource(self, resource_path: str) -> str | None:
        """Get resource content by path.

        Args:
            resource_path: The relative path of the resource from skill root.
        Returns:
            The resource content, or None if not found.
        """
        if resource_path not in self._resources:
            self._resources[resource_path] = self._repo.get_resource(self.name, resource_path)
        return self._resources[resource_path]
