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
from abc import ABC, abstractmethod

from flink_agents.api.event import Event
from flink_agents.api.memoryobject import MemoryObject

class RunnerContext(ABC):
    """Abstract base class providing context for workflow execution.

    This context provides access to event handling.
    """

    @abstractmethod
    def send_event(self, event: Event) -> None:
        """Send an event to the workflow for processing.

        Parameters
        ----------
        event : Event
            The event to be processed by the workflow system.
        """

    @abstractmethod
    def get_short_term_memory(self) -> MemoryObject:
        """
        Get the short-term memory.

        Returns:
        -------
        MemoryObject
          The root object of the short-term memory.
        """
