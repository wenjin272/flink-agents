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
"""Unit tests for SkillManager and skill tools."""

import importlib
import shutil
import sys
import threading
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from flink_agents.api.skills import Skills
from flink_agents.runtime.skill.repository.package_repository import (
    PackageSkillRepository,
)
from flink_agents.runtime.skill.skill_manager import SkillManager

base_dir = Path(__file__).parent


class TestSkillManager:
    """Tests for SkillManager class."""

    @pytest.fixture
    def skills_dir(self) -> Path:
        """Create a temporary directory with test skills."""
        return base_dir / "resources" / "skills"

    def test_add_skills_from_path(self, skills_dir: Path) -> None:
        """Test adding skills from path."""
        manager = SkillManager(Skills.from_local_dir(str(skills_dir)))
        skill = manager.get_skill("github")
        assert skill.name == "github"
        assert skill.description == (
            "Interact with GitHub using the `gh` CLI. "
            "Use `gh issue`, `gh pr`, `gh run`, and `gh api` "
            "for issues, PRs, CI runs, and advanced queries."
        )

    def test_generate_discovery_prompt(self, skills_dir: Path) -> None:
        """Test generating discovery prompt."""
        manager = SkillManager(Skills.from_local_dir(str(skills_dir)))

        prompt = manager.generate_discovery_prompt("github", "nano-banana-pro")
        with Path.open(base_dir / "resources" / "skill_discovery_prompt.txt") as f:
            content = f.read()
            assert prompt == content

    def test_get_skill(self, skills_dir: Path) -> None:
        """Test getting a skill."""
        manager = SkillManager(Skills.from_local_dir(str(skills_dir)))

        skill = manager.get_skill("github")
        assert skill is not None
        assert skill.name == "github"
        assert (
            skill.description
            == "Interact with GitHub using the `gh` CLI. Use `gh issue`, `gh pr`, `gh run`, and `gh api` for issues, PRs, CI runs, and advanced queries."
        )

        skill2 = manager.get_skill("nano-banana-pro")
        assert skill2 is not None
        assert skill2.name == "nano-banana-pro"
        assert (
            skill2.description
            == "Generate/edit images with Nano Banana Pro (Gemini 3 Pro Image). Use for image create/modify requests incl. edits. Supports text-to-image + image-to-image; 1K/2K/4K; use --input-image."
        )

    def test_load_skill_resource(self, skills_dir: Path) -> None:
        """Test loading a skill resource."""
        manager = SkillManager(Skills.from_local_dir(str(skills_dir)))

        skill = manager.get_skill("nano-banana-pro")
        content = skill.get_resource("scripts/generate_image.py")
        assert content is not None
        assert "get_api_key" in content

        nonexistent = skill.get_resource("nonexistent")
        assert nonexistent is None


def _zip_dir(src: Path, dst_zip: Path) -> None:
    with zipfile.ZipFile(dst_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in src.rglob("*"):
            if path.is_file():
                zf.write(path, arcname=path.relative_to(src))


class _ZipHandler(BaseHTTPRequestHandler):
    zip_bytes: bytes = b""

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Length", str(len(type(self).zip_bytes)))
        self.end_headers()
        self.wfile.write(type(self).zip_bytes)

    def log_message(self, *_args: object) -> None:
        pass


@pytest.fixture
def mixed_sources(tmp_path: Path):
    """Yields (dir_path, zip_url, pkg_name, pkg_resource).

    Spins up a local http.server, builds a tmp package on sys.path with
    a skills/ subdirectory, and zips the existing skills tree for the
    URL fixture. Cleans up all three on teardown.
    """
    src = base_dir / "resources" / "skills"

    dir_path = str(src)

    zip_path = tmp_path / "skills.zip"
    _zip_dir(src, zip_path)
    _ZipHandler.zip_bytes = zip_path.read_bytes()
    server = HTTPServer(("127.0.0.1", 0), _ZipHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    pkg_root = tmp_path / "pkg_root"
    pkg_root.mkdir()
    pkg_name = "_flink_agents_test_mixed_pkg"
    pkg_dir = pkg_root / pkg_name
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    shutil.copytree(src, pkg_dir / "skills")
    sys.path.insert(0, str(pkg_root))
    importlib.invalidate_caches()

    try:
        yield (
            dir_path,
            f"http://127.0.0.1:{port}/skills.zip",
            pkg_name,
            "skills",
        )
    finally:
        server.shutdown()
        server.server_close()
        _ZipHandler.zip_bytes = b""
        sys.path.remove(str(pkg_root))
        sys.modules.pop(pkg_name, None)


class TestSkillManagerMixedSources:
    def test_url_only_loads_skills(self, mixed_sources) -> None:
        _dir, url, _pkg, _resource = mixed_sources
        config = Skills(urls=[url])
        manager = SkillManager(config)
        assert set(manager.get_all_skill_names()) == {"github", "nano-banana-pro"}

    def test_package_only_loads_skills(self, mixed_sources) -> None:
        _dir, _url, pkg, resource = mixed_sources
        config = Skills(packages=[(pkg, resource)])
        manager = SkillManager(config)
        assert set(manager.get_all_skill_names()) == {"github", "nano-banana-pro"}

    def test_loads_from_all_sources(self, mixed_sources) -> None:
        dir_path, url, pkg, resource = mixed_sources
        # All three sources expose the same skills. Since dispatch runs
        # paths -> urls -> packages and registration is last-wins, the
        # final repo for each skill must be a PackageSkillRepository if
        # all three branches actually executed.
        config = Skills(
            paths=[dir_path],
            urls=[url],
            packages=[(pkg, resource)],
        )
        manager = SkillManager(config)
        assert set(manager.get_all_skill_names()) == {"github", "nano-banana-pro"}
        assert all(
            isinstance(r, PackageSkillRepository) for r in manager._repos.values()
        )
