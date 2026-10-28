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

"""Opt-in pytest exit diagnostics; preserve pytest's return code and exceptions."""

import atexit
import faulthandler
import json
import os
import sys
import tempfile
import threading
import time
import traceback
from pathlib import Path


def main():
    root = Path(os.environ["PYTHON_EXIT_DIAGNOSTICS_DIR"])
    root.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix=f"pytest-{os.getpid()}-", dir=root))
    # Keep raw descriptors open until process exit, including interpreter teardown.
    events_fd = os.open(directory / "events.jsonl", os.O_WRONLY | os.O_CREAT, 0o600)
    trace_fd = os.open(directory / "tracebacks.log", os.O_WRONLY | os.O_CREAT, 0o600)

    def record(stage, **fields):
        data = {"stage": stage, "pid": os.getpid(), "time_ns": time.time_ns(), **fields}
        os.write(events_fd, (json.dumps(data) + "\n").encode())
        os.fsync(events_fd)

    def record_exception(stage, exc_type, value, tb):
        record(stage, exception_type=exc_type.__name__)
        os.write(
            trace_fd, "".join(traceback.format_exception(exc_type, value, tb)).encode()
        )
        os.fsync(trace_fd)

    def unraisable(args):
        record_exception(
            "unraisable", args.exc_type, args.exc_value, args.exc_traceback
        )
        sys.__unraisablehook__(args)

    def uncaught(exc_type, value, tb):
        record_exception("uncaught", exc_type, value, tb)
        sys.__excepthook__(exc_type, value, tb)

    def thread_exception(args):
        record_exception(
            "thread-exception", args.exc_type, args.exc_value, args.exc_traceback
        )
        threading.__excepthook__(args)

    def enable_exit_tracing():
        # pytest restores its own hooks and disables faulthandler during cleanup.
        # Reinstall after pytest.main returns so native shutdown crashes are captured.
        sys.unraisablehook = unraisable
        sys.excepthook = uncaught
        threading.excepthook = thread_exception
        # Enable only in this process. PYTHONFAULTHANDLER in the environment
        # also enables handlers in JVM-embedded Python and can conflict with HotSpot.
        faulthandler.enable(file=trace_fd, all_threads=True)

    def exit_begin():
        enable_exit_tracing()
        record("atexit-begin")

    # Registered before importing pytest/dependencies: atexit callbacks run LIFO.
    # This marker covers callbacks registered later, not all interpreter finalization.
    atexit.register(lambda: record("atexit-end"))
    enable_exit_tracing()
    record("start", argv=sys.argv[1:], python=sys.version)
    print(f"Python exit diagnostics: {directory}", flush=True)
    sys.path[0] = os.getcwd()

    import pytest

    class ExitPlugin:
        @pytest.hookimpl(wrapper=True, tryfirst=True)
        def pytest_sessionfinish(self, session, exitstatus):
            record("sessionfinish-enter", exitstatus=int(exitstatus))
            try:
                yield
            finally:
                record("sessionfinish-leave", exitstatus=int(session.exitstatus))

        @pytest.hookimpl(trylast=True)
        def pytest_unconfigure(self, config):
            record("unconfigure")

    try:
        result = pytest.main(sys.argv[1:], plugins=[ExitPlugin()])
        record("pytest-return", exitstatus=int(result))
        return result
    except BaseException as exc:
        record_exception("pytest-raised", type(exc), exc, exc.__traceback__)
        raise
    finally:
        enable_exit_tracing()
        record("shutdown-ready", threads=[t.name for t in threading.enumerate()])
        faulthandler.dump_traceback(file=trace_fd, all_threads=True)
        faulthandler.dump_traceback_later(90, repeat=True, file=trace_fd)
        atexit.register(exit_begin)


if __name__ == "__main__":
    sys.exit(main())
