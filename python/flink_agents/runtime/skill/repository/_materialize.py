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
"""Internal helpers for materializing skills from non-filesystem sources."""

from __future__ import annotations

import atexit
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

_TEMP_DIR_PREFIX = "flink-agents-skills-"


def register_temp_cleanup(path: Path) -> None:
    """Register an atexit hook that removes ``path`` recursively on process exit."""
    atexit.register(lambda: shutil.rmtree(path, ignore_errors=True))


def extract_zip_safely(zip_path: Path) -> Path:
    """Extract a zip into a fresh temp directory and return that directory.

    Validates each entry against zip-slip (paths must resolve inside the
    extraction directory). Registers an atexit cleanup for the extraction
    directory so it's removed when the process exits.

    Args:
        zip_path: Path to the zip file to extract.

    Returns:
        The path to the directory containing the extracted contents.

    Raises:
        ValueError: if any zip entry resolves outside the extraction directory.
    """
    extract_dir = Path(tempfile.mkdtemp(prefix=_TEMP_DIR_PREFIX)).resolve()
    # Register cleanup before validation so the tempdir is always reclaimed,
    # even if validation raises (extract_dir is empty in that case).
    register_temp_cleanup(extract_dir)
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            target = (extract_dir / member.filename).resolve()
            if not target.is_relative_to(extract_dir):
                msg = f"Unsafe zip entry: {member.filename}"
                raise ValueError(msg)
        zf.extractall(extract_dir)
    return extract_dir


def download_to_tempfile(url: str, timeout: int = 90) -> Path:
    """Download ``url`` to a temp file and return its path.

    Uses ``urllib.request`` from the standard library. ``timeout`` is the
    socket-level timeout passed to ``urlopen`` and applies to both the
    connection and the read phases.

    Args:
        url: The URL to download.
        timeout: Socket timeout in seconds.

    Returns:
        Path to the downloaded temp file (caller is responsible for deletion).

    Raises:
        urllib.error.HTTPError / URLError on HTTP or transport failures.
    """
    req = Request(url, method="GET")
    # The .zip suffix is load-bearing: FileSystemSkillRepository uses
    # path.suffix == ".zip" to detect zip input. Do not change it.
    fd, tmp_path_str = tempfile.mkstemp(prefix=_TEMP_DIR_PREFIX, suffix=".zip")
    os.close(fd)
    tmp_path = Path(tmp_path_str)
    try:
        with urlopen(req, timeout=timeout) as resp, tmp_path.open("wb") as out:
            shutil.copyfileobj(resp, out)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise
    return tmp_path
