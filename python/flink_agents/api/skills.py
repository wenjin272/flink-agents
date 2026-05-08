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

Use one of the factory methods to construct a :class:`Skills` resource:

* :meth:`Skills.from_local_dir` for local directories or local ``.zip`` files
* :meth:`Skills.from_url` for http(s) URLs pointing to a ``.zip``
* :meth:`Skills.from_package` for a resource inside an installed package

Example::

    @skills
    @staticmethod
    def my_skills() -> Skills:
        return Skills.from_local_dir("./skills")


    @skills
    @staticmethod
    def remote_skills() -> Skills:
        return Skills.from_url("https://example.com/skills.zip")


    @skills
    @staticmethod
    def packaged_skills() -> Skills:
        return Skills.from_package("my_skills_pkg", "skills")

Declare more than one ``@skills`` function on the same agent to combine
sources; the runtime merges them.
"""

from __future__ import annotations

from typing import List, Tuple

from pydantic import Field
from typing_extensions import override

from flink_agents.api.resource import ResourceType, SerializableResource


class Skills(SerializableResource):
    """A resource describing where to load agent skills from.

    Use one of the ``from_*`` factory methods to construct — direct field
    construction is reserved for internal serialization and not part of the
    public API.
    """

    # Filesystem paths. Each entry may be a directory whose immediate
    # subdirectories each contain a ``SKILL.md`` file, or a ``.zip`` file
    # whose top-level entries are the skill subdirectories.
    paths: List[str] = Field(default_factory=list)

    # http(s) URLs. Each URL must point to a ``.zip`` whose top level is
    # the baseDir.
    urls: List[str] = Field(default_factory=list)

    # (package_name, resource_path) pairs. Each entry references an installed
    # Python package and a path inside it; the resource may be a directory or
    # a ``.zip`` file.
    packages: List[Tuple[str, str]] = Field(default_factory=list)

    @classmethod
    def from_local_dir(cls, *paths: str) -> Skills:
        """Create a Skills resource from one or more local paths.

        Each path may be a directory or a ``.zip`` file. For a directory, its
        immediate subdirectories must each contain a ``SKILL.md`` file. For
        a zip, its top-level entries are the skill subdirectories.
        """
        return cls(paths=list(paths))

    @classmethod
    def from_url(cls, *urls: str) -> Skills:
        """Create a Skills resource from one or more http(s) URLs.

        Each URL must point to a ``.zip`` whose top level is the baseDir
        (i.e. skill subdirectories sit at the top of the zip).
        """
        return cls(urls=list(urls))

    @classmethod
    def from_package(cls, package: str, resource: str) -> Skills:
        """Create a Skills resource from a resource inside an installed package.

        Args:
            package: A dotted Python package name (e.g. ``"my_skills_pkg"``).
            resource: A path inside the package, relative to the package root.
                May refer to a directory or a ``.zip`` file. The directory or
                zip top level must be the baseDir.
        """
        return cls(packages=[(package, resource)])

    @classmethod
    @override
    def resource_type(cls) -> ResourceType:
        """Return resource type of class."""
        return ResourceType.SKILLS


# name of built-in tools needed by using skills
LOAD_SKILL_TOOL = "load_skill"
BASH_TOOL = "bash"
