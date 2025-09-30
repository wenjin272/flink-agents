---
title: 'Installation'
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
Flink Agents provides both Python and Java APIs to define a Flink Agents job.

The sections below show how to install the required dependencies.

{{< hint warning >}}
__NOTE:__ To run on flink cluster, Flink-Agents requires flink version be a stable release of Flink 1.20.3.
{{< /hint >}}
## Install the Official Release

#### Install Python Packages

{{< hint warning >}}
__Note:__ This will be available after Flink Agents is released.
{{< /hint >}}

We recommand creating a Python virtual environment to install the Flink Agents Python library.

To install the latest Flink Agents release, run:

```shell
python -m pip install flink-agents
```

#### Install Java Package
To run java job on a Flink cluster, ensure the Flink Agents Java JARs are placed in the Flink lib directory:

<!-- TODO: fill in the command after Flink Agents is released -->
```shell
# Download the Flink Agents released flink-agents-dist jar.

# After downloading the bundle jar, copy it to Flink's lib directory.
cp flink-agents-dist-$VERSION.jar $FLINK_HOME/lib/
```


## Build and Install from Source

Prerequisites for building Flink Agents:

* Unix-like environment (we use Linux, Mac OS X, Cygwin, WSL)
* Git
* Maven
* Java 11
* Python 3.10 or 3.11

To clone from Git, run:

```shell
git clone https://github.com/apache/flink-agents.git
```

### Build
To run on a Flink cluster, we need build the whole project.

We provide a script to run:

```shell
cd flink-agents
./tools/build.sh
```

### Install Flink Agents to Flink


To install the Java dependencies to Flink, run:

```shell
cd flink-agents
# copy the Flink Agents JARs to Flink's lib directory
cp dist/target/flink-agents-dist-0.1-SNAPSHOT.jar $FLINK_HOME/lib/
```
