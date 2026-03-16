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
"""Markdown skill parser for SKILL.md files with YAML frontmatter.

This module provides utilities for parsing and generating Markdown files
with YAML frontmatter, following the Agent Skills specification from
https://agentskills.io/specification

Frontmatter format:
---
name: example_skill
description: Example skill description
license: Apache-2.0
---
# Skill Content
This is the markdown content.
"""
import re
from dataclasses import dataclass
from typing import Dict


@dataclass
class ParsedMarkdown:
    """Result of parsing markdown with frontmatter.

    Contains both the extracted metadata and the markdown content.

    Attributes:
    ----------
    metadata : Dict[str, str]
        YAML metadata extracted from frontmatter.
    content : str
        Markdown content (without frontmatter).
    """

    metadata: Dict[str, str]
    content: str

    def has_frontmatter(self) -> bool:
        """Check if frontmatter exists.

        Returns:
        -------
        bool
            True if metadata is not empty.
        """
        return bool(self.metadata)


class MarkdownSkillParser:
    """Utility for parsing and generating Markdown files with YAML frontmatter.

    This utility can:
    - Extract YAML frontmatter metadata and markdown content from text
    - Generate markdown files with YAML frontmatter from metadata and content

    Example:
    -------
    >>> # Parse markdown with frontmatter
    >>> parsed = MarkdownSkillParser.parse(markdown_content)
    >>> metadata = parsed.metadata
    >>> content = parsed.content

    >>> # Generate markdown with frontmatter
    >>> markdown = MarkdownSkillParser.generate(metadata, content)
    """

    # Pattern to match frontmatter: starts with ---, ends with ---
    # Group 1: frontmatter content (non-greedy)
    # Group 2: remaining content
    FRONTMATTER_PATTERN = re.compile(
        r"^---\s*[\r\n]+(.*?)[\r\n]*---(?:\s*[\r\n]+)?(.*)", re.DOTALL
    )

    # Pattern to match key: value format
    KEY_VALUE_PATTERN = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_-]*)\s*:\s*(.*)$")

    @classmethod
    def parse(cls, markdown: str) -> ParsedMarkdown:
        """Parse markdown content with YAML frontmatter.

        Extracts both the YAML metadata and the markdown content.
        If no frontmatter is found, returns empty metadata with the entire content.

        Parameters
        ----------
        markdown : str
            Markdown content (may or may not have frontmatter).

        Returns:
        -------
        ParsedMarkdown
            Contains metadata and content.

        Raises:
        ------
        ValueError
            If YAML syntax is invalid.
        """
        if not markdown:
            return ParsedMarkdown(metadata={}, content="")

        matcher = cls.FRONTMATTER_PATTERN.match(markdown)

        if not matcher:
            # No frontmatter found, treat entire content as markdown
            return ParsedMarkdown(metadata={}, content=markdown)

        yaml_content = matcher.group(1).strip()
        markdown_content = matcher.group(2)

        if not yaml_content:
            return ParsedMarkdown(metadata={}, content=markdown_content)

        try:
            metadata = cls._parse_yaml(yaml_content)
            return ParsedMarkdown(metadata=metadata, content=markdown_content)
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Invalid YAML frontmatter syntax: {e}") from e

    @classmethod
    def generate(
        cls, metadata: Dict[str, str] | None, content: str | None
    ) -> str:
        """Generate markdown content with YAML frontmatter.

        Creates a markdown file with the metadata serialized as YAML frontmatter
        at the beginning, followed by the content.

        Parameters
        ----------
        metadata : Optional[Dict[str, str]]
            Metadata to serialize as YAML frontmatter.
        content : Optional[str]
            Markdown content.

        Returns:
        -------
        str
            Complete markdown with frontmatter.
        """
        result = []

        # Add frontmatter if metadata exists
        if metadata:
            result.append("---")
            result.append(cls._generate_yaml(metadata))
            result.append("---")

        # Add content
        if content:
            # Add a blank line between frontmatter and content if frontmatter exists
            if metadata:
                result.append("")
            result.append(content)

        return "\n".join(result)

    @classmethod
    def _parse_yaml(cls, yaml: str) -> Dict[str, str]:
        """Parse YAML string into a map of key-value pairs.

        Only supports flat key-value structures with string values.

        Parameters
        ----------
        yaml : str
            YAML content to parse.

        Returns:
        -------
        Dict[str, str]
            Map of key-value pairs.

        Raises:
        ------
        ValueError
            If YAML syntax is invalid.
        """
        result: Dict[str, str] = {}

        if not yaml:
            return result

        lines = yaml.split("\n")

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip comments
            if line.startswith("#"):
                continue

            matcher = cls.KEY_VALUE_PATTERN.match(line)
            if not matcher:
                raise ValueError(
                    f"Invalid YAML line (expected 'key: value' format): {line}"
                )

            key = matcher.group(1)
            value = cls._parse_value(matcher.group(2))

            result[key] = value

        return result

    @classmethod
    def _parse_value(cls, raw_value: str) -> str:
        """Parse a YAML value, handling quoted strings.

        Parameters
        ----------
        raw_value : str
            Raw value string from YAML.

        Returns:
        -------
        str
            Parsed value with quotes removed if present.
        """
        if raw_value is None:
            return ""

        value = raw_value.strip()

        if not value:
            return ""

        # Handle double-quoted strings
        if value.startswith('"') and value.endswith('"') and len(value) >= 2:
            return cls._unescape_string(value[1:-1])

        # Handle single-quoted strings
        if value.startswith("'") and value.endswith("'") and len(value) >= 2:
            # Single-quoted strings don't process escapes, except '' for '
            return value[1:-1].replace("''", "'")

        return value

    @classmethod
    def _unescape_string(cls, s: str) -> str:
        """Unescape a double-quoted YAML string.

        Parameters
        ----------
        s : str
            String content without surrounding quotes.

        Returns:
        -------
        str
            Unescaped string.
        """
        if not s:
            return s

        result = []
        escape = False

        for c in s:
            if escape:
                if c == "n":
                    result.append("\n")
                elif c == "t":
                    result.append("\t")
                elif c == "r":
                    result.append("\r")
                elif c == "\\":
                    result.append("\\")
                elif c == '"':
                    result.append('"')
                else:
                    result.append("\\")
                    result.append(c)
                escape = False
            elif c == "\\":
                escape = True
            else:
                result.append(c)

        # Handle trailing backslash
        if escape:
            result.append("\\")

        return "".join(result)

    @classmethod
    def _generate_yaml(cls, data: Dict[str, str]) -> str:
        """Generate YAML string from a map of key-value pairs.

        Parameters
        ----------
        data : Dict[str, str]
            Map to serialize.

        Returns:
        -------
        str
            YAML string.
        """
        if not data:
            return ""

        lines = []
        for key, value in data.items():
            if value is None or value == "":
                lines.append(f"{key}: ")
            elif cls._needs_quoting(value):
                lines.append(f"{key}: {cls._quote_value(value)}")
            else:
                lines.append(f"{key}: {value}")

        return "\n".join(lines)

    @classmethod
    def _needs_quoting(cls, value: str) -> bool:
        """Check if a value needs to be quoted in YAML.

        Parameters
        ----------
        value : str
            Value to check.

        Returns:
        -------
        bool
            True if quoting is needed.
        """
        if not value:
            return False

        # Quote if contains special characters
        special_chars = [":", "#", "\n", "\r", "\t"]
        if any(c in value for c in special_chars):
            return True

        # Quote if starts/ends with whitespace
        if value[0].isspace() or value[-1].isspace():
            return True

        # Quote if starts with special YAML characters
        special_start_chars = ['"', "'", "[", "]", "{", "}", ">", "|", "*", "&", "!", "%", "@", "`"]
        if value[0] in special_start_chars:
            return True

        return False

    @classmethod
    def _quote_value(cls, value: str) -> str:
        """Quote a value for YAML output using double quotes.

        Parameters
        ----------
        value : str
            Value to quote.

        Returns:
        -------
        str
            Quoted and escaped value.
        """
        result = ['"']

        for c in value:
            if c == '"':
                result.append('\\"')
            elif c == "\\":
                result.append("\\\\")
            elif c == "\n":
                result.append("\\n")
            elif c == "\r":
                result.append("\\r")
            elif c == "\t":
                result.append("\\t")
            else:
                result.append(c)

        result.append('"')
        return "".join(result)


class SkillParser:
    """Parser for creating AgentSkill from SKILL.md content.

    This class provides high-level parsing functionality to create
    AgentSkill instances from raw SKILL.md file content and resources.

    Example:
    -------
    >>> skill_md = \"\"\"---
    ... name: my-skill
    ... description: Does something useful
    ... ---
    ... # My Skill
    ...
    ... Instructions here.
    ... \"\"\"
    >>> resources = {"scripts/run.sh": "#!/bin/bash\\necho hello"}
    >>> skill = SkillParser.parse_skill(skill_md, resources, "filesystem")
    """

    @classmethod
    def parse_skill(
        cls,
        skill_md_content: str,
        resources: Dict[str, str] | None = None,
        source: str = "custom",
    ) -> "AgentSkill":
        """Parse SKILL.md content and create an AgentSkill.

        Parameters
        ----------
        skill_md_content : str
            The raw content of SKILL.md file.
        resources : Optional[Dict[str, str]]
            Optional resource files (path -> content).
        source : str
            Source identifier for the skill.

        Returns:
        -------
        AgentSkill
            The parsed skill.

        Raises:
        ------
        ValueError
            If required fields (name, description) are missing.
        """
        from flink_agents.api.skills.agent_skill import AgentSkill

        parsed = MarkdownSkillParser.parse(skill_md_content)
        metadata = parsed.metadata

        # Required fields
        name = metadata.get("name")
        description = metadata.get("description")

        if not name:
            raise ValueError("Skill must have 'name' field in frontmatter")
        if not description:
            raise ValueError("Skill must have 'description' field in frontmatter")

        # Validate name matches the expected format
        name = name.strip()
        description = description.strip()

        # Optional fields
        license_value = metadata.get("license")
        compatibility = metadata.get("compatibility")
        allowed_tools = metadata.get("allowed-tools")

        # Parse metadata field (additional key-value pairs not in spec)
        # Exclude known fields
        known_fields = {
            "name",
            "description",
            "license",
            "compatibility",
            "allowed-tools",
        }
        additional_metadata = {
            k: v for k, v in metadata.items() if k not in known_fields
        }

        return AgentSkill(
            name=name,
            description=description,
            skill_content=parsed.content,
            resources=resources or {},
            source=source,
            license=license_value,
            compatibility=compatibility,
            metadata=additional_metadata if additional_metadata else None,
            allowed_tools=allowed_tools,
        )

    @classmethod
    def generate_skill_md(cls, skill: "AgentSkill") -> str:
        """Generate SKILL.md content from an AgentSkill.

        Parameters
        ----------
        skill : AgentSkill
            The skill to generate markdown for.

        Returns:
        -------
        str
            SKILL.md content with frontmatter.
        """
        metadata = {
            "name": skill.name,
            "description": skill.description,
        }

        if skill.license:
            metadata["license"] = skill.license
        if skill.compatibility:
            metadata["compatibility"] = skill.compatibility
        if skill.allowed_tools:
            metadata["allowed-tools"] = skill.allowed_tools

        # Add additional metadata
        if skill.metadata:
            metadata.update(skill.metadata)

        return MarkdownSkillParser.generate(metadata, skill.skill_content)
