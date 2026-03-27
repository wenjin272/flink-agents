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
from typing import Dict, List

from typing_extensions import override

from flink_agents.api.skills.agent_skill import AgentSkill
from flink_agents.api.skills.skill_repository import (
    SkillRepository,
)


# TODO: Implement
class UrlSkillRepository(SkillRepository):
    """URL-based implementation of SkillRepository.

    This repository downloads skills from remote URLs (OSS, S3, HTTP servers).
    The URL should point to a zip archive containing skill directories.
    """

    @override
    def get_skill(self, name: str) -> str:
        pass

    @override
    def get_skills(self) -> List[AgentSkill]:
        pass

    @override
    def get_resources(self, name: str) -> Dict[str, str]:
        pass
