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
"""Tests for ExecuteCommandTool and SkillManager.validate_command."""
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from flink_agents.api.resource_context import ResourceContext
from flink_agents.api.skills import Skills
from flink_agents.runtime.skill.skill_manager import SkillManager
from flink_agents.runtime.skill.skill_tools import ExecuteCommandTool

base_dir = Path(__file__).parent
skills_dir = base_dir / "resources" / "skills"

# nano-banana-pro has: scripts/generate_image.py
# github has: no script resources


class TestValidateCommand:
    """Tests for SkillManager.validate_command."""

    @pytest.fixture
    def manager(self) -> SkillManager:
        """SkillManager with default config (shell + python scripts, no allowed_commands)."""
        return SkillManager(Skills(paths=[str(skills_dir)]))

    @pytest.fixture
    def manager_with_commands(self) -> SkillManager:
        """SkillManager with allowed_commands=["gh", "git"]."""
        return SkillManager(
            Skills(paths=[str(skills_dir)], allowed_commands=["gh", "git"])
        )

    # -- skill script execution (priority 1) ---------------------------------

    def test_allow_direct_script_execution(self, manager: SkillManager) -> None:
        """Direct execution of a skill resource script should be allowed."""
        result = manager.validate_command(
            "nano-banana-pro", "scripts/generate_image.py --size 1024"
        )
        assert result is None

    def test_allow_interpreter_plus_script(self, manager: SkillManager) -> None:
        """'python scripts/generate_image.py' should be allowed."""
        result = manager.validate_command(
            "nano-banana-pro", "python scripts/generate_image.py arg1"
        )
        assert result is None

    def test_allow_python3_interpreter(self, manager: SkillManager) -> None:
        """python3 is also a known interpreter for .py scripts."""
        result = manager.validate_command(
            "nano-banana-pro", "python3 scripts/generate_image.py"
        )
        assert result is None

    def test_reject_script_not_in_resources(self, manager: SkillManager) -> None:
        """A script path that is not a skill resource should be rejected."""
        result = manager.validate_command(
            "nano-banana-pro", "scripts/unknown.py"
        )
        assert result is not None
        assert "not allowed" in result

    def test_reject_disallowed_script_extension(self) -> None:
        """A skill resource with a non-allowed extension should be rejected."""
        manager = SkillManager(
            Skills(paths=[str(skills_dir)], allowed_script_types=["shell"])
        )
        # generate_image.py is a resource but .py is not allowed (only shell)
        result = manager.validate_command(
            "nano-banana-pro", "scripts/generate_image.py"
        )
        assert result is not None
        assert "unsupported type" in result

    # -- allowed_commands whitelist (priority 2) -----------------------------

    def test_allow_whitelisted_command(
        self, manager_with_commands: SkillManager
    ) -> None:
        """A command in allowed_commands should be allowed."""
        result = manager_with_commands.validate_command(
            "github", "gh issue list --repo owner/repo"
        )
        assert result is None

    def test_allow_git_whitelisted(
        self, manager_with_commands: SkillManager
    ) -> None:
        result = manager_with_commands.validate_command("github", "git status")
        assert result is None

    def test_reject_command_not_in_whitelist(self, manager: SkillManager) -> None:
        """A command not in whitelist (and not a script) should be rejected."""
        result = manager.validate_command("github", "rm -rf /")
        assert result is not None
        assert "not allowed" in result

    def test_reject_curl_when_not_whitelisted(
        self, manager_with_commands: SkillManager
    ) -> None:
        """Curl is not in allowed_commands=["gh", "git"]."""
        result = manager_with_commands.validate_command(
            "github", "curl https://example.com"
        )
        assert result is not None
        assert "not allowed" in result

    # -- chained commands: each sub-command validated individually -------------

    def test_allow_pipe_all_whitelisted(
        self, manager_with_commands: SkillManager
    ) -> None:
        """All sub-commands in whitelist → allow."""
        result = manager_with_commands.validate_command(
            "github", "gh issue list | git log"
        )
        assert result is None

    def test_reject_pipe_one_not_whitelisted(
        self, manager_with_commands: SkillManager
    ) -> None:
        """One sub-command not in whitelist → reject."""
        result = manager_with_commands.validate_command(
            "github", "gh issue list | grep bug"
        )
        assert result is not None
        assert "grep" in result

    def test_reject_and_one_not_whitelisted(
        self, manager_with_commands: SkillManager
    ) -> None:
        result = manager_with_commands.validate_command(
            "github", "gh issue list && rm -rf /"
        )
        assert result is not None
        assert "rm" in result

    def test_reject_semicolon_one_not_whitelisted(
        self, manager_with_commands: SkillManager
    ) -> None:
        result = manager_with_commands.validate_command(
            "github", "gh issue list; rm -rf /"
        )
        assert result is not None
        assert "rm" in result

    def test_reject_newline_one_not_whitelisted(
        self, manager_with_commands: SkillManager
    ) -> None:
        result = manager_with_commands.validate_command(
            "github", "gh issue list\nrm -rf /"
        )
        assert result is not None
        assert "rm" in result

    def test_allow_operators_inside_single_quotes(
        self, manager_with_commands: SkillManager
    ) -> None:
        """Operators inside single quotes are not separators."""
        result = manager_with_commands.validate_command(
            "github", "gh issue list --label 'bug|feature'"
        )
        assert result is None

    def test_allow_operators_inside_double_quotes(
        self, manager_with_commands: SkillManager
    ) -> None:
        """Operators inside double quotes are not separators."""
        result = manager_with_commands.validate_command(
            "github", 'gh issue list --label "a&&b"'
        )
        assert result is None

    def test_allow_escaped_operator(
        self, manager_with_commands: SkillManager
    ) -> None:
        """Escaped operators are not separators."""
        result = manager_with_commands.validate_command(
            "github", "gh issue list --query a\\|b"
        )
        assert result is None

    # -- edge cases ----------------------------------------------------------

    def test_reject_empty_command(self, manager: SkillManager) -> None:
        result = manager.validate_command("github", "")
        assert result is not None

    def test_skill_not_found(self, manager: SkillManager) -> None:
        with pytest.raises(ValueError, match="not found"):
            manager.validate_command("nonexistent", "echo hello")


class TestExecuteCommandTool:
    """Integration tests for ExecuteCommandTool.call."""

    @pytest.fixture
    def tool_with_manager(self) -> ExecuteCommandTool:
        """ExecuteCommandTool with a real SkillManager injected via mock context."""
        manager = SkillManager(
            Skills(
                paths=[str(skills_dir)],
                allowed_commands=["echo", "bc"],
            )
        )
        mock_ctx = MagicMock(spec=ResourceContext)
        tool = ExecuteCommandTool(resource_context=mock_ctx)

        # Wire up the runtime ResourceContext that _get_skill_manager expects
        from flink_agents.runtime.resource_context import ResourceContextImpl

        runtime_ctx = MagicMock(spec=ResourceContextImpl)
        runtime_ctx.get_skill_manager.return_value = manager
        tool.resource_context = runtime_ctx
        return tool

    def test_execute_whitelisted_command(
        self, tool_with_manager: ExecuteCommandTool
    ) -> None:
        result = tool_with_manager.call(
            skill_name="github", command="echo hello", timeout=10
        )
        assert result == "hello"
        result = tool_with_manager.call(
            skill_name="github", command='echo "(2 ^ 3)" | bc', timeout=10
        )
        assert result == "8"

    def test_reject_non_whitelisted_command(
        self, tool_with_manager: ExecuteCommandTool
    ) -> None:
        result = tool_with_manager.call(
            skill_name="github", command="rm -rf /", timeout=10
        )
        assert "Command rejected" in result

    def test_reject_piped_command(
        self, tool_with_manager: ExecuteCommandTool
    ) -> None:
        result = tool_with_manager.call(
            skill_name="github", command="echo hello | cat", timeout=10
        )
        assert "Command rejected" in result

    def test_skill_not_found(
        self, tool_with_manager: ExecuteCommandTool
    ) -> None:
        result = tool_with_manager.call(
            skill_name="nonexistent", command="echo hello", timeout=10
        )
        assert "not found" in result

    def test_no_skill_manager(self) -> None:
        """When no SkillManager is available, return error message."""
        mock_ctx = MagicMock(spec=ResourceContext)
        tool = ExecuteCommandTool(resource_context=mock_ctx)
        result = tool.call(skill_name="github", command="echo hello")
        assert "not available" in result
