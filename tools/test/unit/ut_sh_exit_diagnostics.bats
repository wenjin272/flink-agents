#!/usr/bin/env bats

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


setup() {
    load '../helpers/shim'
    shim_setup
    UT_SH="${BATS_TEST_DIRNAME}/../../ut.sh"
    shim_bin_script uv '
case " $* " in
    *" e2e_tests_integration "*) exit "${E2E_RC:-0}" ;;
    *" -m integration "*) exit "${INTEGRATION_RC:-0}" ;;
esac
exit 0'
}

@test "prints an abnormal e2e exit before aggregation and still runs integration" {
    export E2E_RC=139
    run "${FLINK_AGENTS_SUT_BASH:-bash}" "$UT_SH" -p -e -f 1.20
    [ "$status" -eq 2 ]
    [[ "$output" == *"arm=e2e raw_rc=139"* ]]
    [[ "$output" == *"arm=integration raw_rc=0"* ]]
}

@test "prints no-tests exit before remapping it" {
    export INTEGRATION_RC=5
    run "${FLINK_AGENTS_SUT_BASH:-bash}" "$UT_SH" -p -e -f 1.20
    [ "$status" -eq 2 ]
    [[ "$output" == *"arm=e2e raw_rc=0"* ]]
    [[ "$output" == *"arm=integration raw_rc=5"* ]]
}

@test "disabled diagnostics retain the pytest command and success status" {
    unset PYTHON_EXIT_DIAGNOSTICS_DIR
    run "${FLINK_AGENTS_SUT_BASH:-bash}" "$UT_SH" -p -e -f 1.20
    [ "$status" -eq 0 ]
    [[ "$(shim_calls uv)" == *$'run\t--no-sync\tpytest\tflink_agents'* ]]
    [[ "$(shim_calls uv)" != *"pytest_diagnostics.py"* ]]
}

@test "enabled diagnostics select the wrapper without hiding failure" {
    export PYTHON_EXIT_DIAGNOSTICS_DIR="$BATS_TEST_TMPDIR/diagnostics"
    export E2E_RC=71
    run "${FLINK_AGENTS_SUT_BASH:-bash}" "$UT_SH" -p -e -f 1.20
    [ "$status" -eq 2 ]
    [[ "$output" == *"arm=e2e raw_rc=71"* ]]
    [[ "$(shim_calls uv)" == *"pytest_diagnostics.py"* ]]
}
