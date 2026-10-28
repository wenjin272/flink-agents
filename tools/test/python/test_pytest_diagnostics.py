# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""Exercise actual child-process exits, including failures after pytest passes."""

import json
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

WRAPPER = Path(__file__).resolve().parents[2] / "ci" / "pytest_diagnostics.py"


class ExitDiagnosticsTest(unittest.TestCase):
    def run_child(self, test="def test_ok(): assert True", conftest=""):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test_sample.py").write_text(test)
            (root / "conftest.py").write_text(conftest)
            env = dict(
                os.environ,
                PYTHON_EXIT_DIAGNOSTICS_DIR=str(root / "logs"),
                PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
            )
            result = subprocess.run(
                [sys.executable, str(WRAPPER), "-q", "test_sample.py"],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
                timeout=20,
            )
            directory = next((root / "logs").iterdir())
            events = [
                json.loads(line)
                for line in (directory / "events.jsonl").read_text().splitlines()
            ]
            return result, events, (directory / "tracebacks.log").read_text()

    def test_pass_preserves_zero_and_exit_markers(self):
        result, events, _ = self.run_child()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            [e["stage"] for e in events],
            [
                "start",
                "sessionfinish-enter",
                "sessionfinish-leave",
                "unconfigure",
                "pytest-return",
                "shutdown-ready",
                "atexit-begin",
                "atexit-end",
            ],
        )
        self.assertEqual(events[4]["exitstatus"], 0)

    def test_test_failure_preserves_nonzero(self):
        result, events, _ = self.run_child("def test_fail(): assert False")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            next(e for e in events if e["stage"] == "pytest-return")["exitstatus"], 1
        )

    def test_atexit_exception_is_recorded_without_changing_exit(self):
        result, events, traces = self.run_child(
            conftest="""
import atexit
@atexit.register
def cleanup():
    raise RuntimeError("cleanup sentinel")
"""
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("unraisable", [e["stage"] for e in events])
        self.assertIn("cleanup sentinel", traces)

    def test_unconfigure_exception_propagates(self):
        result, events, traces = self.run_child(
            conftest="""
def pytest_unconfigure(config):
    raise RuntimeError("unconfigure sentinel")
"""
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("pytest-raised", [e["stage"] for e in events])
        self.assertIn("unconfigure sentinel", traces)

    def test_abrupt_atexit_is_distinct_from_pytest_return(self):
        result, events, _ = self.run_child(
            conftest="""
import atexit
import os
atexit.register(lambda: os._exit(71))
"""
        )
        self.assertEqual(result.returncode, 71)
        self.assertEqual(
            next(e for e in events if e["stage"] == "pytest-return")["exitstatus"], 0
        )
        self.assertEqual(events[-1]["stage"], "atexit-begin")

    @unittest.skipUnless(os.name == "posix", "POSIX signal exit")
    def test_native_abort_after_pytest_return_has_traceback(self):
        result, events, traces = self.run_child(
            conftest="""
import atexit
import os
import resource
import signal
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
atexit.register(lambda: os.kill(os.getpid(), signal.SIGABRT))
"""
        )
        self.assertEqual(result.returncode, -signal.SIGABRT)
        self.assertEqual(
            next(e for e in events if e["stage"] == "pytest-return")["exitstatus"], 0
        )
        self.assertIn("Fatal Python error: Aborted", traces)
        self.assertEqual(events[-1]["stage"], "atexit-begin")


if __name__ == "__main__":
    unittest.main()
