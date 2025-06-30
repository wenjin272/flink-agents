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
from pydantic import BaseModel
from pyflink.common import Configuration
from pyflink.datastream import (
    KeySelector,
    RuntimeExecutionMode,
    StreamExecutionEnvironment,
)

from flink_agents.api.execution_enviroment import AgentsExecutionEnvironment
from flink_agents.examples.workflow_example import MyWorkflow


class WordCountData(BaseModel):
    """Data model for storing word count information.

    Attributes:
    ----------
    id : int
        Unique identifier for the word entry
    value : str
        The actual word string being counted
    """

    id: int
    value: str

    def getId(self) -> int:
        """Retrieve the unique identifier of the word entry.

        Returns:
        -------
        int
            The ID associated with this word record
        """
        return self.id

    def getValue(self) -> str:
        """Get the word string value being counted.

        Returns:
        -------
        str
            The original word text (case-sensitive)
        """
        return self.value

class WordCountDataKeySelector(KeySelector):
        
    def get_key(self, value: WordCountData) -> int:
        return value.getId()


if __name__ == "__main__":
    word_count_data = [
        WordCountData(
            id=1, value="Great product! Works perfectly and lasts a long time."
        ),
        WordCountData(
            id=1, value="The item arrived damaged, and the packaging was poor."
        ),
        WordCountData(
            id=1, value="Highly satisfied with the performance and value for money."
        ),
        WordCountData(
            id=1, value="Not as good as expected. It stopped working after a week."
        ),
        WordCountData(
            id=1, value="Fast shipping and excellent customer service. Would buy again!"
        ),
        WordCountData(
            id=2, value="Too complicated to set up. Instructions were unclear."
        ),
        WordCountData(id=2, value="Good quality, but overpriced for what it does."),
        WordCountData(
            id=2, value="Exactly what I needed. Easy to use and very reliable."
        ),
        WordCountData(id=2, value="Worst purchase ever. Waste of money and time."),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        WordCountData(
            id=2, value="Looks nice and functions well, but could be more durable."
        ),
        
    ]

    config = Configuration()
    config.set_string("", "INFO")
    env = StreamExecutionEnvironment.get_execution_environment(config)
    env.add_jars("file:////Users/jhin/Repo/oss/flink-agents/runtime/target/flink-agents-runtime-0.1-SNAPSHOT.jar")
    env.add_jars("file:////Users/jhin/Repo/oss/flink-agents/plan/target/flink-agents-plan-0.1-SNAPSHOT.jar")
    env.add_jars("file:////Users/jhin/Repo/oss/flink-agents/api/target/flink-agents-api-0.1-SNAPSHOT.jar")
    AgentsExecutionEnvironment.local = False
    agents_env = AgentsExecutionEnvironment.get_execution_environment()

    env.set_runtime_mode(RuntimeExecutionMode.STREAMING)
    env.set_parallelism(1)

    input_datastream = (
        env.from_collection(word_count_data)
    )

    output_datastream = (
        agents_env.from_datastream(input=input_datastream, key_selector=WordCountDataKeySelector())
        .apply(MyWorkflow())
        .to_datastream()
    )
    
    print("output type")
    print(output_datastream.get_type())

    output_datastream.print()

    env.execute()
