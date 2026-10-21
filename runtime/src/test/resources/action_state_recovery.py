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
"""Python Actions for the explicit native recovery integration test."""

from pathlib import Path

from flink_agents.api.events.event import Event, OutputEvent
from flink_agents.api.runner_context import RunnerContext


def root(event: Event, ctx: RunnerContext) -> None:
    """Record a real invocation outside checkpointed state and emit a child."""
    path = event.attributes["input"]
    with Path(path).open("a") as log:
        log.write("root\n")
    ctx.send_event(Event(type="step", attributes={"path": path}))


def child(event: Event, ctx: RunnerContext) -> None:
    """Record a child invocation; replaying its completion must skip this write."""
    with Path(event.attributes["path"]).open("a") as log:
        log.write("child\n")
    ctx.send_event(OutputEvent(output="ok"))
