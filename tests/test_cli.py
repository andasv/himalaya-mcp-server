import json
import subprocess
from unittest.mock import patch

import pytest

from himalaya_mcp.cli import HimalayaError, _sanitize_stderr, run, run_raw
from tests.conftest import make_completed_process


class TestRun:
    def test_basic_command(self, mock_subprocess, mock_which):
        mock_subprocess.return_value = make_completed_process(
            stdout=json.dumps([{"name": "default"}])
        )
        result = run("account", "list")
        assert result == [{"name": "default"}]
        mock_subprocess.assert_called_once()
        cmd = mock_subprocess.call_args[0][0]
        assert cmd == ["/usr/local/bin/himalaya", "--output", "json", "account", "list"]

    def test_with_account(self, mock_subprocess, mock_which):
        mock_subprocess.return_value = make_completed_process(stdout=json.dumps([]))
        run("folder", "list", account="work")
        cmd = mock_subprocess.call_args[0][0]
        assert "--account" in cmd
        assert "work" in cmd

    def test_with_folder(self, mock_subprocess, mock_which):
        mock_subprocess.return_value = make_completed_process(stdout=json.dumps([]))
        run("envelope", "list", folder="INBOX")
        cmd = mock_subprocess.call_args[0][0]
        assert "--folder" in cmd
        assert "INBOX" in cmd

    def test_no_json_output(self, mock_subprocess, mock_which):
        mock_subprocess.return_value = make_completed_process(stdout="OK")
        result = run("folder", "create", "Test", output_json=False)
        assert result == "OK"
        cmd = mock_subprocess.call_args[0][0]
        assert "--output" not in cmd

    def test_nonzero_exit_code(self, mock_subprocess, mock_which):
        mock_subprocess.return_value = make_completed_process(
            returncode=1, stderr="connection refused"
        )
        with pytest.raises(HimalayaError, match="connection refused"):
            run("account", "list")

    def test_malformed_json(self, mock_subprocess, mock_which):
        mock_subprocess.return_value = make_completed_process(stdout="not json{{{")
        with pytest.raises(HimalayaError, match="Failed to parse"):
            run("account", "list")

    def test_timeout(self, mock_subprocess, mock_which):
        mock_subprocess.side_effect = subprocess.TimeoutExpired(cmd="himalaya", timeout=30)
        with pytest.raises(HimalayaError, match="timed out"):
            run("account", "list")

    def test_os_error(self, mock_subprocess, mock_which):
        mock_subprocess.side_effect = OSError("Permission denied")
        with pytest.raises(HimalayaError, match="Permission denied"):
            run("account", "list")

    def test_empty_stdout_json(self, mock_subprocess, mock_which):
        mock_subprocess.return_value = make_completed_process(stdout="")
        result = run("account", "list")
        assert result == ""


class TestRunRaw:
    def test_basic_raw(self, mock_subprocess, mock_which):
        mock_subprocess.return_value = make_completed_process(stdout="From: test@test.com")
        result = run_raw("template", "write")
        assert result == "From: test@test.com"

    def test_with_stdin(self, mock_subprocess, mock_which):
        mock_subprocess.return_value = make_completed_process(stdout="sent")
        result = run_raw("template", "send", stdin_data="From: a@b.com\nTo: c@d.com")
        assert result == "sent"
        assert mock_subprocess.call_args[1]["input"] == "From: a@b.com\nTo: c@d.com"

    def test_raw_error(self, mock_subprocess, mock_which):
        mock_subprocess.return_value = make_completed_process(
            returncode=1, stderr="invalid template"
        )
        with pytest.raises(HimalayaError, match="invalid template"):
            run_raw("template", "send")


class TestBinaryNotFound:
    def test_himalaya_not_on_path(self):
        with (
            patch("himalaya_mcp.cli.shutil.which", return_value=None),
            pytest.raises(HimalayaError, match="not found"),
        ):
            run("account", "list")

    def test_run_raw_himalaya_not_on_path(self):
        with (
            patch("himalaya_mcp.cli.shutil.which", return_value=None),
            pytest.raises(HimalayaError, match="not found"),
        ):
            run_raw("template", "write")


class TestSanitizeStderr:
    def test_redacts_email_addresses(self):
        stderr = "Failed to authenticate as user@example.com on imap.server.com"
        result = _sanitize_stderr(stderr)
        assert "user@example.com" not in result
        assert "[REDACTED_EMAIL]" in result

    def test_redacts_password(self):
        stderr = "auth error: password=SuperSecret123 for account"
        result = _sanitize_stderr(stderr)
        assert "SuperSecret123" not in result
        assert "[REDACTED]" in result

    def test_redacts_token(self):
        stderr = "oauth failed: token=eyJhbGciOiJSUzI1NiIsInR5c for user"
        result = _sanitize_stderr(stderr)
        assert "eyJhbGciOiJSUzI1NiIsInR5c" not in result

    def test_preserves_safe_content(self):
        stderr = "connection refused: cannot connect to server on port 993"
        result = _sanitize_stderr(stderr)
        assert result == stderr

    def test_redacts_multiple_emails(self):
        stderr = "from alice@test.com to bob@test.com failed"
        result = _sanitize_stderr(stderr)
        assert "alice@test.com" not in result
        assert "bob@test.com" not in result
        assert result.count("[REDACTED_EMAIL]") == 2

    def test_error_message_is_sanitized(self, mock_subprocess, mock_which):
        mock_subprocess.return_value = make_completed_process(
            returncode=1,
            stderr="auth failed for user@secret.com password=hunter2",
        )
        with pytest.raises(HimalayaError) as exc_info:
            run("account", "list")
        assert "user@secret.com" not in str(exc_info.value)
        assert "hunter2" not in str(exc_info.value)
