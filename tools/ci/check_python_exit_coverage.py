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

"""Check experiment coverage after pytest exits, without instrumenting pytest."""

import json
import re
import sys
from pathlib import Path

EXPECTED = {
    "e2e": {"passed": 82, "skipped": 10},
    "integration": {"passed": 69, "skipped": 22},
}


def check_coverage(text):
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)
    exits = re.compile(
        r"Python pytest exit: flink=1\.20 arm=(e2e|integration) raw_rc=(\d+)"
    )
    arms = {}
    start = 0
    for match in exits.finditer(text):
        arm, raw_exit = match.groups()
        summaries = [
            s
            for s in re.findall(r"^=+ (.+?) =+$", text[start : match.start()], re.M)
            if " in " in s and re.search(r"\d+ (?:passed|failed|skipped)", s)
        ]
        summary = summaries[-1] if summaries else ""
        counts = {
            name: int(count)
            for count, name in re.findall(
                r"(\d+) (passed|skipped|failed|errors?)\b", summary
            )
        }
        arms[arm] = {
            "summary": summary,
            "counts": counts,
            "raw_exit": int(raw_exit),
            "coverage_matches": (
                all(counts.get(k) == v for k, v in EXPECTED[arm].items())
                and not any(counts.get(k, 0) for k in ("failed", "error", "errors"))
            ),
        }
        start = match.end()
    return {
        "expected": EXPECTED,
        "arms": arms,
        # A nonzero process exit is the signal being investigated; it must not
        # change whether the test coverage matches. The test step retains it.
        "coverage_matches": all(
            arms.get(arm, {}).get("coverage_matches", False) for arm in EXPECTED
        ),
    }


def main():
    directory = Path(sys.argv[1])
    log = directory / "console.log"
    report = check_coverage(log.read_text(errors="replace") if log.exists() else "")
    directory.mkdir(parents=True, exist_ok=True)
    result = json.dumps(report, indent=2) + "\n"
    (directory / "coverage.json").write_text(result)
    print(result, end="")
    return 0 if report["coverage_matches"] else 1


if __name__ == "__main__":
    sys.exit(main())
