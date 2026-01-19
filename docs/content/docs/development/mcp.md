---
title: MCP
weight: 7
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

MCP (Model Context Protocol) is a standardized protocol for integrating AI applications with external data sources and tools. Flink Agents provides the support for using prompts and tools from MCP server.

{{< hint warning >}}
**JDK Requirement (Java API Only):** If you are using the **Java API** to develop Flink Agents jobs with MCP, you need **JDK 17 or higher**. This requirement does not apply to **Python API** users - the Python SDK has its own MCP implementation and works with JDK 11+.
{{< /hint >}}

## Declare MCP in Agent

Developer can declare a mcp by decorator/annotation when creating an Agent.

{{< tabs "Use MCP Tools in Agent" >}}

{{< tab "Python" >}}
```python
class ReviewAnalysisAgent(Agent):

    @mcp_server
    @staticmethod
    def my_mcp_server() -> ResourceDescriptor:
        """Define MCP server connection."""
        return ResourceDescriptor(clazz=Constant.MCP_SERVER, 
                                  endpoint="http://127.0.0.1:8000/mcp")
```
{{< /tab >}}

{{< tab "Java" >}}
```java
public class ReviewAnalysisAgent extends Agent {

    @MCPServer
    public static ResourceDescriptor myMcp() {
        return ResourceDescriptor.Builder.newBuilder(Constant.MCP_SERVER)
                    .addInitialArgument("endpoint", MCP_ENDPOINT)
                    .addInitialArgument("timeout", 30)
                    .build();
    }
}
```
{{< /tab >}}

{{< /tabs >}}

**Key points:**
- Use decorator/annotation to define MCP server connection
  - In Python, use `@mcp_server`.
  - In Java, use `@MCPServer`.
- Use the builder pattern in Java to configure the MCP server with endpoint, timeout, headers, and authentication

### Authentication

MCP servers can be configured with authentication:

{{< tabs "MCP Server Authentication" >}}

{{< tab "Python" >}}
```python
@mcp_server
@staticmethod
def authenticated_mcp_server() -> MCPServer:
    """Connect to MCP server with authentication."""
    return ResourceDescriptor(clazz=Constant.MCP_SERVER, 
                              endpoint="http://api.example.com/mcp",
                              headers={"Authorization": "Bearer your-token"})
    # Or using Basic Authentication
    # credentials = base64.b64encode(b"username:password").decode("ascii")
    # headers={"Authorization": f"Basic {credentials}"}

    # Or using API Key Authentication
    # headers={"X-API-Key": "your-api-key"}
```
{{< /tab >}}

{{< tab "Java" >}}
```java
@MCPServer
public static org.apache.flink.agents.integrations.mcp.MCPServer authenticatedMcpServer() {
    // Using Bearer Token Authentication
    return ResourceDescriptor.Builder.newBuilder(Constant.MCP_SERVER)
                    .addInitialArgument("endpoint", "http://api.example.com/mcp")
                    .addInitialArgument("timeout", 30)
                    .addInitialArgument("auth", new BearerTokenAuth("your-oauth-token"))
                    .build();

    // Or using Basic Authentication
    .addInitialArgument("auth", new BasicAuth("username", "password"))

    // Or using API Key Authentication
    .addInitialArgument("auth", new ApiKeyAuth("X-API-Key", "your-api-key"))
}
```
{{< /tab >}}

{{< /tabs >}}

**Authentication options:**
- `BearerTokenAuth` - For OAuth 2.0 and JWT tokens
- `BasicAuth` - For username/password authentication
- `ApiKeyAuth` - For API key authentication via custom headers

## Use MCP prompts and tools in Agent


MCP prompts and tools are managed by external MCP servers and automatically discovered when you define an MCP server connection in your agent.

### Define a MCP Server

Create an MCP server that exposes tools and prompts using the `FastMCP` library:

```python
# mcp_server.py
mcp = FastMCP("ReviewServer")

@mcp.prompt()
def review_analysis_prompt(product_id: str, review: str) -> str:
    """Prompt for analyzing product reviews."""
    return f"""
    Analyze the following product review and provide a satisfaction score (1-5).

    Product ID: {product_id}
    Review: {review}

    Output format: {{"score": 1-5, "reasons": ["reason1", "reason2"]}}
    """

@mcp.tool()
async def notify_shipping_manager(id: str, review: str) -> None:
    """Notify the shipping manager when product received a negative review due to
    shipping damage.

    Parameters
    ----------
    id : str
        The id of the product that received a negative review due to shipping damage
    review: str
        The negative review content
    """
    ...

mcp.run("streamable-http")
```

**Key points:**
- Use `@mcp.tool()` decorator to define tools
- Use `@mcp.prompt()` decorator to define prompts
- The function name becomes the identifier

### Use in Agent

Connect to the MCP server and use its prompts and tools in your agent:

{{< tabs "Use MCP Prompts and Tools in Agent" >}}

{{< tab "Python" >}}
```python
class ReviewAnalysisAgent(Agent):
  
    @mcp_server
    @staticmethod
    def review_mcp_server() -> ResourceDescriptor:
        """Connect to MCP server."""
        return ResourceDescriptor(clazz=Constant.MCP_SERVER, 
                                  endpoint="http://127.0.0.1:8000/mcp")

    @chat_model_setup
    @staticmethod
    def review_model() -> ResourceDescriptor:
        return ResourceDescriptor(
            clazz=OllamaChatModelSetup,
            connection="ollama_server",
            model="qwen3:8b",
            prompt="review_analysis_prompt",   # Reference MCP prompt by name
            tools=["notify_shipping_manager"],  # Reference MCP tool by name
        )
```
{{< /tab >}}

{{< tab "Java" >}}
```java
public class ReviewAnalysisAgent extends Agent {

    @MCPServer
    public static ResourceDescriptor myMcp() {
        return ResourceDescriptor.Builder.newBuilder(Constant.MCP_SERVER)
                    .addInitialArgument("endpoint", "http://127.0.0.1:8000/mcp")
                    .addInitialArgument("timeout", 30)
                    .build();
    }

    @ChatModelSetup
    public static ResourceDescriptor reviewModel() {
        return ResourceDescriptor.Builder.newBuilder(OllamaChatModelSetup.class.getName())
                .addInitialArgument("connection", "ollamaChatModelConnection")
                .addInitialArgument("model", "qwen3:8b")
                .addInitialArgument("prompt", "review_analysis_prompt") // Reference MCP tool by name
                .addInitialArgument("tools", Collections.singletonList("notifyShippingManager")) // Reference MCP tool by name
                .build();
    }
}
```
{{< /tab >}}

{{< /tabs >}}

**Key points:**
- Reference MCP prompts by their function name (e.g., `"review_analysis_prompt"` in Python, `"reviewAnalysisPrompt"` in Java)
- Reference MCP tools by their function name (e.g., `"notify_shipping_manager"` in Python, `"notifyShippingManager"` in Java)
- All tools and prompts from the MCP server are automatically registered