import os
from unittest.mock import patch

import pytest


class TestServerModes:
    def test_readonly_mode_registers_only_read_tools(self):
        with patch.dict(os.environ, {"HIMALAYA_MODE": "readonly"}, clear=False):
            import importlib

            import himalaya_mcp.server as server_module

            importlib.reload(server_module)

            tool_names = set(server_module.mcp._tool_manager._tools.keys())
            assert len(tool_names) == 10

            # Read tools should be present
            assert "account_list" in tool_names
            assert "folder_list" in tool_names
            assert "envelope_list" in tool_names
            assert "message_read" in tool_names
            assert "attachment_download" in tool_names
            assert "template_write" in tool_names

            # Write tools should NOT be present
            assert "folder_create" not in tool_names
            assert "flag_add" not in tool_names

            # Send tools should NOT be present
            assert "message_send" not in tool_names
            assert "template_send" not in tool_names

    def test_full_mode_registers_read_and_write_tools(self):
        with patch.dict(os.environ, {"HIMALAYA_MODE": "full"}, clear=False):
            import importlib

            import himalaya_mcp.server as server_module

            importlib.reload(server_module)

            tool_names = set(server_module.mcp._tool_manager._tools.keys())

            # 10 read + 8 write = 18 (no send tools)
            assert len(tool_names) == 18

            # Write tools should be present
            assert "folder_create" in tool_names
            assert "message_copy" in tool_names
            assert "message_move" in tool_names
            assert "message_save" in tool_names
            assert "flag_add" in tool_names
            assert "flag_set" in tool_names
            assert "flag_remove" in tool_names
            assert "template_save" in tool_names

            # Send tools should NOT be present in full mode
            assert "message_send" not in tool_names
            assert "template_send" not in tool_names

    def test_dangerzone_mode_registers_all_tools(self):
        with patch.dict(os.environ, {"HIMALAYA_MODE": "dangerzone"}, clear=False):
            import importlib

            import himalaya_mcp.server as server_module

            importlib.reload(server_module)

            tool_names = set(server_module.mcp._tool_manager._tools.keys())

            # 10 read + 8 write + 2 send = 20
            assert len(tool_names) == 20

            # Send tools should be present
            assert "message_send" in tool_names
            assert "template_send" in tool_names

            # Write tools should also be present
            assert "folder_create" in tool_names
            assert "message_copy" in tool_names
            assert "message_move" in tool_names

    def test_full_mode_tools_have_danger_write_descriptions(self):
        with patch.dict(os.environ, {"HIMALAYA_MODE": "full"}, clear=False):
            import importlib

            import himalaya_mcp.server as server_module

            importlib.reload(server_module)

            tools = server_module.mcp._tool_manager._tools

            danger_write_tools = [
                "folder_create",
                "message_copy",
                "message_move",
                "message_save",
                "flag_add",
                "flag_set",
                "flag_remove",
                "template_save",
            ]
            for name in danger_write_tools:
                assert "[DANGER: WRITE]" in tools[name].description, (
                    f"{name} missing [DANGER: WRITE] prefix"
                )

    def test_dangerzone_mode_send_tools_have_dangerzone_descriptions(self):
        with patch.dict(os.environ, {"HIMALAYA_MODE": "dangerzone"}, clear=False):
            import importlib

            import himalaya_mcp.server as server_module

            importlib.reload(server_module)

            tools = server_module.mcp._tool_manager._tools

            send_tools = ["message_send", "template_send"]
            for name in send_tools:
                assert "[DANGERZONE: SENDS EMAIL]" in tools[name].description, (
                    f"{name} missing [DANGERZONE: SENDS EMAIL] prefix"
                )

    def test_default_mode_is_readonly(self):
        env = os.environ.copy()
        env.pop("HIMALAYA_MODE", None)
        with patch.dict(os.environ, env, clear=True):
            import importlib

            import himalaya_mcp.server as server_module

            importlib.reload(server_module)

            tool_names = set(server_module.mcp._tool_manager._tools.keys())
            assert len(tool_names) == 10

    def test_invalid_mode_raises(self):
        with patch.dict(os.environ, {"HIMALAYA_MODE": "invalid"}, clear=False):
            import importlib

            import himalaya_mcp.server as server_module

            with pytest.raises(ValueError):
                importlib.reload(server_module)
