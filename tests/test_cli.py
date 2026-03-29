import json
import subprocess
from unittest.mock import patch

import pytest

from himalaya_mcp.cli import HimalayaError, run, run_raw
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
