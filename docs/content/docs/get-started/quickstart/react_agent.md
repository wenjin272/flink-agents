---
title: 'ReAct Agent'
weight: 2
type: docs
---
<!--
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
-->

## Overview

ReAct Agent is a general paradigm that combines reasoning and action capabilities to solve complex tasks. Leveraging this paradigm, the user only needs to specify the goal with prompt and provide available tools, and the LLM will decide how to achieve the goal and take actions autonomously.

This quickstart introduces a small example that demonstrate how to build a streaming ReAct Agent with Flink Agents:

The **Review Analysis** agent processes a stream of product reviews and uses a single agent to extract a rating (1–5) and unsatisfied reasons from each review. And notify the shipping manager if a review includes dissatisfaction with the shipping process.

## Code Walkthrough

### Prepare Agents Execution Environment

Create the agents execution environment, and register the available chat model connections and tools to the environment. 
```python
# Set up the Flink streaming environment and the Agents execution environment.
env = StreamExecutionEnvironment.get_execution_environment()
agents_env = AgentsExecutionEnvironment.get_execution_environment(env)

# Add Ollama chat model connection and notify shipping manager tool to be used
# by the Agent.
agents_env.add_resource(
    "ollama_server",
    ResourceDescriptor(clazz=OllamaChatModelConnection, request_timeout=120),
).add_resource(
    "notify_shipping_manager", Tool.from_callable(notify_shipping_manager)
)
```

### Create the ReAct Agent
Create the ReAct Agent instance, configure the chat model, prompt and the output schema of result to be used.
```python
review_analysis_react_agent = ReActAgent(
    chat_model=ResourceDescriptor(
        clazz=OllamaChatModelSetup,
        connection="ollama_server",
        model="qwen3:8b",
        tools=["notify_shipping_manager"],
    ),
    prompt=review_analysis_react_prompt,
    output_schema=ProductReviewAnalysisRes,
)
```

### Integrate the ReAct Agent with Flink
Produce a source DataStream by reading a product review text file, and use the ReAct Agent to analyze the review and generate result DataStream. Finally print the result DataStream.
```python
# Read product reviews from a text file as a streaming source.
# Each line in the file should be a JSON string representing a ProductReview.
product_review_stream = env.from_source(
    source=FileSource.for_record_stream_format(
        StreamFormat.text_line_format(),
        f"file:///{current_dir}/resources/",
    )
    .monitor_continuously(Duration.of_minutes(1))
    .build(),
    watermark_strategy=WatermarkStrategy.no_watermarks(),
    source_name="streaming_agent_example",
).map(
    lambda x: ProductReview.model_validate_json(
        x
    )  # Deserialize JSON to ProductReview.
)

# Use the ReAct agent to analyze each product review and notify the shipping manager
# when needed.
review_analysis_res_stream = (
    agents_env.from_datastream(
        input=product_review_stream, key_selector=lambda x: x.id
    )
    .apply(review_analysis_react_agent)
    .to_datastream()
)

# Print the analysis results to stdout.
review_analysis_res_stream.print()
```

## Run the Example

### Prerequisites

* Unix-like environment (we use Linux, Mac OS X, Cygwin, WSL)
* Git
* Java 11
* Python 3.10 or 3.11

### Preparation

#### Prepare Flink

Download a stable release of Flink 1.20.3, then extract the archive:

```bash
curl -LO https://archive.apache.org/dist/flink/flink-1.20.3/flink-1.20.3-bin-scala_2.12.tgz
tar -xzf flink-1.20.3-bin-scala_2.12.tgz

# Copy the flink-python jar from opt to lib
cp ./flink-1.20.3/opt/flink-python-1.20.3.jar ./flink-1.20.3/lib
```
You can refer to the [local installation](https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/try-flink/local_installation/) instructions for more detailed step.


#### Prepare Flink Agents

We recommend creating a Python virtual environment to install the Flink Agents Python library.

Follow the [installation]({{< ref "docs/get-started/installation" >}}) instructions to install the Flink Agents Python and Java libraries.

#### Deploy a Standalone Flink Cluster

You can deploy a standalone Flink cluster in your local environment with the following command.

```bash
export PYTHONPATH=$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')
./flink-1.20.3/bin/start-cluster.sh
```
You can refer to the [local cluster](https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/try-flink/local_installation/#starting-and-stopping-a-local-cluster) instructions for more detailed step.


> **NOTE:** If you can't navigate to the web UI at [localhost:8081](localhost:8081), you can find the reason in `./flink-1.20.3/log`. If the reason is port conflict, you can change the port in `./flink-1.20.3/conf/config.yaml`.

#### Prepare Ollama

Download and install Ollama from the official [website](https://ollama.com/download).

Then run the qwen3:8b model, which is required by the quickstart examples

```bash
ollama run qwen3:8b
```

### Submit Flink Agents Job to Standalone Flink Cluster

#### Clone the Flink Agents repo

```bash
git clone https://github.com/apache/flink-agents.git
```

#### Submit to Flink Cluster
```bash
export PYTHONPATH=$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')

# Run review analysis example
./flink-1.20.3/bin/flink run -py ./flink-agents/python/flink_agents/examples/quickstart/react_agent_example.py
```

Now you should see a Flink job submitted to the Flink Cluster in Flink web UI [localhost:8081](localhost:8081)

After a few minutes, you can check for the output in the TaskManager output log.

