#    Licensed to the Apache Software Foundation (ASF) under one
#   or more contributor license agreements.  See the NOTICE file
#   distributed with this work for additional information
#   regarding copyright ownership.  The ASF licenses this file
#   to you under the Apache License, Version 2.0 (the
#   "License"); you may not use this file except in compliance
#   with the License.  You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#  limitations under the License.
#

class Prompt:
    # System prompt template for skills discovery
    SKILL_DISCOVERY_PROMPT = """## Available Skills

    The following skills are available. Use `load_skill` tool to load a skill's full content when you need it.

    {skill_list}

    ## How to Use Skills

    1. First, review the skill descriptions above to find relevant skills
    2. Use `load_skill` tool with the skill name to load the full skill content
    3. Follow the skill's instructions to complete the task
    """
    
    # System prompt template for active skill
    SKILL_ACTIVE_PROMPT = """## Active Skill: {skill_name}

    {skill_content}

    ## Available Resources

    {resource_list}

    ## How to Use Resources

    Use `load_skill_resource` tool with the resource path to load specific resource content.
    """