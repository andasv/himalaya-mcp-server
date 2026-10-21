"""Verify complete CLI arguments without executing mailbox operations."""

import importlib
import subprocess
from unittest.mock import patch

import pytest

from himalaya_mcp import cli
from himalaya_mcp.tools import account, attachment, envelope, flag, folder, message


@pytest.mark.parametrize(
    ("tool", "kwargs", "expected"),
    [
        (account.account_list, {}, ["--json", "account", "list"]),
        (
            folder.folder_list,
            {"account": "work"},
            ["--json", "--account", "work", "mailbox", "list"],
        ),
        (
            envelope.envelope_list,
            {"folder": "Sent", "page": 2, "page_size": 10},
            ["--json", "envelope", "list", "--mailbox", "Sent", "--page", "2", "--page-size", "10"],
        ),
        (
            envelope.envelope_list,
            {"query": "from alice@example.com"},
            ["--json", "envelope", "search", "--", "from alice@example.com"],
        ),
        (
            envelope.envelope_list,
            {"query": "--help"},
            ["--json", "envelope", "search", "--", "--help"],
        ),
        (
            message.message_read,
            {"envelope_id": "1", "headers": True},
            ["--json", "message", "read", "1"],
        ),
        (
            message.message_read,
            {"envelope_id": "1", "raw": True},
            ["message", "read", "--raw", "1"],
        ),
        (
            message.message_copy,
            {"envelope_id": "1", "target_folder": "Archive"},
            ["message", "copy", "1", "--to", "Archive", "--from", "INBOX"],
        ),
        (
            message.message_move,
            {"envelope_id": "1", "target_folder": "Archive", "folder": "Sent"},
            ["message", "move", "1", "--to", "Archive", "--from", "Sent"],
        ),
        (
            message.message_save,
            {"raw_message": "Subject: Test\n\nBody"},
            ["message", "add", "--mailbox", "INBOX"],
        ),
        (
            message.message_save,
            {"raw_message": "Subject: Test\n\nBody", "folder": "Drafts", "account": "work"},
            ["message", "add", "--mailbox", "Drafts", "--account", "work"],
        ),
        (
            flag.flag_add,
            {"envelope_id": "1", "flags": "seen flagged"},
            ["flag", "add", "1", "--flag", "seen", "--flag", "flagged"],
        ),
        (
            flag.flag_set,
            {"envelope_id": "1", "flags": "\\Seen"},
            ["flag", "set", "1", "--flag", "seen"],
        ),
        (
            flag.flag_remove,
            {"envelope_id": "1", "flags": "flagged"},
            ["flag", "remove", "1", "--flag", "flagged"],
        ),
        (
            attachment.attachment_download,
            {"envelope_id": "1", "folder": "INBOX"},
            ["attachment", "download", "--mailbox", "INBOX", "1"],
        ),
    ],
)
async def test_generated_command_arguments(tool, kwargs, expected, mock_subprocess, mock_which):
    await tool(**kwargs)

    mock_subprocess.assert_called_once()
    assert mock_subprocess.call_args.args[0] == ["/usr/local/bin/himalaya", *expected]
    if "raw_message" in kwargs:
        assert mock_subprocess.call_args.kwargs["input"] == kwargs["raw_message"]


def test_registration_omits_unsupported_commands(monkeypatch):
    monkeypatch.setenv("HIMALAYA_MODE", "dangerzone")
    supported = {
        ("account", "list"),
        ("mailbox", "list"),
        ("envelope", "list"),
        ("message", "read"),
        ("attachment", "download"),
        ("message", "copy"),
        ("message", "move"),
        ("message", "add"),
        ("message", "send"),
        ("flag", "add"),
        ("flag", "set"),
        ("flag", "remove"),
    }
    import himalaya_mcp.server as server

    try:
        with patch.object(cli, "supports", side_effect=lambda *args: args in supported):
            importlib.reload(server)
            names = set(server.mcp._tool_manager._tools)
            assert len(names) == 12
            assert not any(name.startswith("template_") for name in names)
            assert "envelope_thread" not in names
            assert "message_thread" not in names
            assert "folder_create" not in names
            assert "message_send" in names
    finally:
        monkeypatch.setenv("HIMALAYA_MODE", "readonly")
        importlib.reload(server)


def test_capability_probe_handles_missing_command(mock_subprocess, mock_which):
    mock_subprocess.return_value = subprocess.CompletedProcess([], 2, "", "unknown command")
    assert not cli.supports("envelope", "thread")
    assert mock_subprocess.call_args.args[0][-1] == "--help"
