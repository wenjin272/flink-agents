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
"""Package-resource based skill repository.

Resolves a resource (directory or zip) inside an installed Python package
via :mod:`importlib.resources` and delegates loading to the parent
``FileSystemSkillRepository``.
"""

from __future__ import annotations

import atexit
from importlib.resources import as_file, files
from pathlib import Path

from flink_agents.runtime.skill.repository.filesystem_repository import (
    FileSystemSkillRepository,
)


class PackageSkillRepository(FileSystemSkillRepository):
    """Skill repository backed by a resource inside an installed Python package.

    The resource may be a directory or a ``.zip`` file. For packages installed
    in egg/zip form, ``importlib.resources.as_file`` materializes the resource
    to a temp file/dir; the ``as_file`` context manager is held open for the
    lifetime of the process via an ``atexit`` hook so the materialized copy
    is not reclaimed early.
    """

    def __init__(self, package: str, resource: str) -> None:
        """Construct from a package + resource path.

        Args:
            package: A dotted package name (e.g. ``"my_skills_pkg"``).
            resource: A path inside the package, relative to the package root.
                May refer to a directory or a ``.zip`` file. The directory or
                zip top level must be the baseDir.

        Raises:
            ValueError: If the resource does not exist in the package, or is
                neither a directory nor a ``.zip`` file.
        """
        traversable = files(package).joinpath(resource)
        if not traversable.is_dir() and not traversable.is_file():
            msg = f"Resource {resource!r} not found in package {package!r}"
            raise ValueError(msg)

        ctx = as_file(traversable)
        materialized = Path(ctx.__enter__())
        # Hold the context open for the process lifetime; the parent
        # FileSystemSkillRepository may itself extract the zip into another
        # temp dir (with its own atexit), but we still need the source copy
        # to survive long enough for that to happen and (for directory
        # resources) to remain accessible.
        atexit.register(lambda: ctx.__exit__(None, None, None))

        super().__init__(materialized)
