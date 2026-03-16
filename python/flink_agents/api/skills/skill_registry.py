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
"""Skill Registry for managing skill registration and activation state.

This module provides the SkillRegistry class which is responsible for:
- Storing and retrieving skills
- Tracking skill metadata and activation state
"""
import threading
from typing import Dict, Set

from flink_agents.api.skills.agent_skill import AgentSkill, RegisteredSkill


class SkillRegistry:
    """Registry for managing skill registration and activation state.

    This class provides basic storage and retrieval operations for skills.

    Responsibilities:
    - Store and retrieve skills
    - Track skill metadata and activation state

    Design principle:
    This is a pure storage layer. All parameters are assumed to be non-null
    unless explicitly documented. Parameter validation should be performed
    at the SkillManager layer.

    Thread Safety:
    This class is thread-safe. All operations are protected by a lock.
    """

    def __init__(self) -> None:
        """Initialize the SkillRegistry."""
        self._lock = threading.RLock()
        self._skills: Dict[str, AgentSkill] = {}
        self._registered_skills: Dict[str, RegisteredSkill] = {}

    def register_skill(
        self, skill_id: str, skill: AgentSkill, registered: RegisteredSkill
    ) -> None:
        """Register a skill with its metadata.

        If the skill is already registered, it will be replaced.

        Parameters
        ----------
        skill_id : str
            The unique skill identifier.
        skill : AgentSkill
            The skill implementation.
        registered : RegisteredSkill
            The registered skill wrapper containing metadata.
        """
        with self._lock:
            self._skills[skill_id] = skill
            self._registered_skills[skill_id] = registered

    def set_skill_active(self, skill_id: str, active: bool) -> None:
        """Set the activation state of a skill.

        Parameters
        ----------
        skill_id : str
            The skill ID.
        active : bool
            Whether to activate the skill.
        """
        with self._lock:
            registered = self._registered_skills.get(skill_id)
            if registered is not None:
                registered.set_active(active)

    def set_all_skills_active(self, active: bool) -> None:
        """Set the activation state of all skills.

        Parameters
        ----------
        active : bool
            Whether to activate all skills.
        """
        with self._lock:
            for registered in self._registered_skills.values():
                registered.set_active(active)

    def get_skill(self, skill_id: str) -> AgentSkill | None:
        """Get a skill by ID.

        Parameters
        ----------
        skill_id : str
            The skill ID.

        Returns:
        -------
        AgentSkill | None
            The skill instance, or None if not found.
        """
        with self._lock:
            return self._skills.get(skill_id)

    def get_registered_skill(self, skill_id: str) -> RegisteredSkill | None:
        """Get a registered skill by ID.

        Parameters
        ----------
        skill_id : str
            The skill ID.

        Returns:
        -------
        RegisteredSkill | None
            The registered skill, or None if not found.
        """
        with self._lock:
            return self._registered_skills.get(skill_id)

    def get_skill_ids(self) -> Set[str]:
        """Get all skill IDs.

        Returns:
        -------
        Set[str]
            Set of skill IDs (never None, may be empty).
        """
        with self._lock:
            return set(self._skills.keys())

    def exists(self, skill_id: str) -> bool:
        """Check if a skill exists.

        Parameters
        ----------
        skill_id : str
            The skill ID.

        Returns:
        -------
        bool
            True if the skill exists, False otherwise.
        """
        with self._lock:
            return skill_id in self._skills

    def get_all_registered_skills(self) -> Dict[str, RegisteredSkill]:
        """Get all registered skills.

        Returns:
        -------
        Dict[str, RegisteredSkill]
            Map of skill IDs to registered skills (never None, may be empty).
        """
        with self._lock:
            return dict(self._registered_skills)

    def get_all_skills(self) -> Dict[str, AgentSkill]:
        """Get all skills.

        Returns:
        -------
        Dict[str, AgentSkill]
            Map of skill IDs to skills (never None, may be empty).
        """
        with self._lock:
            return dict(self._skills)

    def remove_skill(self, skill_id: str) -> bool:
        """Remove a skill completely.

        Parameters
        ----------
        skill_id : str
            The skill ID.

        Returns:
        -------
        bool
            True if the skill was removed, False if it didn't exist.
        """
        with self._lock:
            if skill_id in self._skills:
                del self._skills[skill_id]
                self._registered_skills.pop(skill_id, None)
                return True
            return False

    def clear(self) -> None:
        """Clear all registered skills."""
        with self._lock:
            self._skills.clear()
            self._registered_skills.clear()

    def get_active_skills(self) -> Dict[str, AgentSkill]:
        """Get all currently active skills.

        Returns:
        -------
        Dict[str, AgentSkill]
            Map of skill IDs to active skills.
        """
        with self._lock:
            return {
                skill_id: self._skills[skill_id]
                for skill_id, registered in self._registered_skills.items()
                if registered.active and skill_id in self._skills
            }

    def get_active_skill_ids(self) -> Set[str]:
        """Get IDs of all currently active skills.

        Returns:
        -------
        Set[str]
            Set of active skill IDs.
        """
        with self._lock:
            return {
                skill_id
                for skill_id, registered in self._registered_skills.items()
                if registered.active
            }

    def size(self) -> int:
        """Get the number of registered skills.

        Returns:
        -------
        int
            The number of skills.
        """
        with self._lock:
            return len(self._skills)

    def is_empty(self) -> bool:
        """Check if the registry is empty.

        Returns:
        -------
        bool
            True if no skills are registered.
        """
        with self._lock:
            return len(self._skills) == 0
