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
"""URL-based skill repository.

Downloads a zip from an http(s) URL and delegates loading to the parent
``FileSystemSkillRepository``.
"""

from __future__ import annotations

from flink_agents.runtime.skill.repository._materialize import download_to_tempfile
from flink_agents.runtime.skill.repository.filesystem_repository import (
    FileSystemSkillRepository,
)

_REQUEST_TIMEOUT_SEC = 90


class URLSkillRepository(FileSystemSkillRepository):
    """Skill repository backed by an http(s) URL pointing to a zip.

    The zip is downloaded to a temp file and extracted into a process-local
    temp directory (cleaned up at process exit). The downloaded zip itself
    is removed once extraction completes.
    """

    def __init__(self, url: str) -> None:
        """Construct from an http(s) URL pointing to a ``.zip``.

        Args:
            url: An ``http://`` or ``https://`` URL whose response body is a
                zip with the standard skills layout (zip top level is the
                baseDir).

        Raises:
            ValueError: If the URL is not http or https.
            urllib.error.HTTPError / URLError: On transport/HTTP failures.
        """
        if not url.startswith(("http://", "https://")):
            msg = f"Only http(s) URLs are supported: {url}"
            raise ValueError(msg)

        tmp_zip = download_to_tempfile(url, timeout=_REQUEST_TIMEOUT_SEC)
        try:
            super().__init__(tmp_zip)
        finally:
            tmp_zip.unlink(missing_ok=True)
