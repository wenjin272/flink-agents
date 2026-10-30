#!/usr/bin/env python3
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
"""Exercise the CI workaround in isolated Python processes without native Arrow."""

# These checks use only the standard library on the tools-test runner.
# ruff: noqa: PT009

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("patch_pyarrow11.py")
SOURCE = """try:
    from pyarrow._s3fs import initialize_s3, finalize_s3
except ImportError:
    pass
else:
    initialize_s3()


def __getattr__(name):
    raise AttributeError(name)
"""


class PyArrowPatchTest(unittest.TestCase):
    """Verify file guards and per-process cleanup without loading Arrow."""

    def setUp(self) -> None:
        """Create an isolated distribution with observable initialization/cleanup."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        package = self.root / "pyarrow"
        package.mkdir()
        (package / "__init__.py").write_text("")
        (package / "_s3fs.py").write_text(
            'def initialize_s3():\n    print("initialized")\n'
            'def finalize_s3():\n    print("finalized")\n'
        )
        self.fs = package / "fs.py"
        self.fs.write_text(SOURCE)
        metadata = self.root / "pyarrow-11.0.0.dist-info"
        metadata.mkdir()
        self.metadata = metadata / "METADATA"
        self.metadata.write_text("Name: pyarrow\nVersion: 11.0.0\n")
        self.env = {**os.environ, "PYTHONPATH": str(self.root)}

    def invoke(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run the patcher against the isolated package metadata."""
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_cleanup_in_independent_processes_preserves_exit_status(self) -> None:
        """Finalize on ordinary and nonzero exits in separate interpreters."""
        patched = self.invoke()
        self.assertEqual(patched.returncode, 0, patched.stderr)
        self.assertNotIn("initialized", patched.stdout)
        for status in (0, 7):
            with self.subTest(status=status):
                result = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        f"import pyarrow.fs; raise SystemExit({status})",
                    ],
                    env=self.env,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, status, result.stderr)
                self.assertEqual(
                    result.stdout.splitlines(), ["initialized", "finalized"]
                )

    def test_repeated_application_and_check_do_not_change_file(self) -> None:
        """Leave an already patched package untouched."""
        self.assertEqual(self.invoke().returncode, 0)
        content = self.fs.read_bytes()
        modified = self.fs.stat().st_mtime_ns
        for args in ((), ("--check",)):
            result = self.invoke(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.fs.read_bytes(), content)
            self.assertEqual(self.fs.stat().st_mtime_ns, modified)

    def test_missing_patch_fails_read_only_check(self) -> None:
        """Reject an unpatched package without changing it in check mode."""
        result = self.invoke("--check")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.fs.read_text(), SOURCE)

    def test_other_version_is_rejected_without_modification(self) -> None:
        """Reject unsupported package versions without changing their source."""
        self.metadata.write_text("Name: pyarrow\nVersion: 16.1.0\n")
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Expected PyArrow 11.0.0", result.stderr)
        self.assertEqual(self.fs.read_text(), SOURCE)

    def test_changed_layout_is_rejected_without_modification(self) -> None:
        """Reject a changed upstream initialization block."""
        changed = SOURCE.replace("    initialize_s3()", "    initialize_s3(0)")
        self.fs.write_text(changed)
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unexpected PyArrow", result.stderr)
        self.assertEqual(self.fs.read_text(), changed)

    def test_reinstalled_original_is_detected(self) -> None:
        """Detect installation that replaced the patched file."""
        self.assertEqual(self.invoke().returncode, 0)
        self.fs.write_text(SOURCE)
        self.assertNotEqual(self.invoke("--check").returncode, 0)
        self.assertEqual(self.fs.read_text(), SOURCE)


if __name__ == "__main__":
    unittest.main()
