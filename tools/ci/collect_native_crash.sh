#!/usr/bin/env bash
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
set -uo pipefail

core_dir="$1"
report_dir="$2"
mkdir -p "$report_dir"
status=0

# A core is process memory. Export only debugger text, never the raw core.
shopt -s nullglob
cores=("$core_dir"/core.*)
printf 'core_count=%s\n' "${#cores[@]}" > "$report_dir/core-index.txt"
if [ "${#cores[@]}" -eq 0 ]; then
    echo "No core dump was found." >> "$report_dir/core-index.txt"
    exit 0
fi
if ! command -v gdb >/dev/null 2>&1; then
    echo "GDB is unavailable; core dumps could not be inspected." >> "$report_dir/core-index.txt"
    exit 1
fi
gdb --version > "$report_dir/gdb-version.txt" 2>&1

index=0
for core in "${cores[@]}"; do
    index=$((index + 1))
    name="${core##*/}"
    # kernel.core_pattern is core.%p.%t.%E; %E encodes executable '/' as '!'.
    executable="${name#core.}"
    executable="${executable#*.}"
    executable="${executable#*.}"
    executable="$(printf '%s' "$executable" | tr '!' '/')"
    report="$report_dir/core-${index}-threads.txt"
    printf '\ncore=%s\nexecutable=%s\n' "$name" "$executable" >> "$report_dir/core-index.txt"
    ls -lh "$core" >> "$report_dir/core-index.txt"
    if [ ! -f "$executable" ]; then
        echo "Executable unavailable; cannot inspect this core reliably." > "$report"
        status=1
        continue
    fi
    # Disable init files, auto-loaded scripts, network symbol downloads, and
    # frame argument values. Keep the matching executable/libraries on this runner.
    timeout 120 gdb --batch --nx \
        -iex 'set auto-load off' \
        -iex 'set debuginfod enabled off' \
        -iex 'set print frame-arguments none' \
        -ex 'set pagination off' \
        -ex 'info threads' \
        -ex 'thread apply all bt' \
        -ex 'info sharedlibrary' \
        -ex 'info proc mappings' \
        -ex 'info registers' \
        "$executable" "$core" > "$report" 2>&1
    gdb_rc=$?
    printf 'gdb_exit=%s\nreport=core-%s-threads.txt\n' "$gdb_rc" "$index" >> "$report_dir/core-index.txt"
    if [ "$gdb_rc" -ne 0 ] || ! grep -q '^#0 ' "$report" ||
        grep -Eq 'core file may not match|not compatible with reported target architecture|Unexpected size of section' "$report"; then
        echo "Native stack extraction failed or returned no stack." >> "$report"
        status=1
    fi
done
exit "$status"
