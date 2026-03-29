import subprocess
from unittest.mock import patch

import pytest

from himalaya_mcp.cli import HimalayaError, run, run_raw
from tests.conftest import make_completed_process


class TestHimalayaNotInstalled:
    def test_run_fails_gracefully(self):
        with (
            patch("himalaya_mcp.cli.shutil.which", return_value=None),
            pytest.raises(HimalayaError, match="not found on PATH"),
        ):
            run("account", "list")

    def test_run_raw_fails_gracefully(self):
        with (
            patch("himalaya_mcp.cli.shutil.which", return_value=None),
            pytest.raises(HimalayaError, match="not found on PATH"),
        ):
            run_raw("template", "write")


class TestCLIErrors:
    def test_authentication_error(self, mock_subprocess, mock_which):
        mock_subprocess.return_value = make_completed_process(
            returncode=1,
            stderr="error: authentication failed: invalid credentials",
        )
        with pytest.raises(HimalayaError, match="authentication failed"):
            run("account", "list")

    def test_connection_error(self, mock_subprocess, mock_which):
        mock_subprocess.return_value = make_completed_process(
            returncode=1,
            stderr="error: cannot connect to imap server: connection refused",
        )
        with pytest.raises(HimalayaError, match="cannot connect"):
            run("envelope", "list")

    def test_folder_not_found(self, mock_subprocess, mock_which):
        mock_subprocess.return_value = make_completed_process(
            returncode=1,
            stderr="error: folder not found: NonExistent",
        )
        with pytest.raises(HimalayaError, match="folder not found"):
            run("envelope", "list", folder="NonExistent")

    def test_message_not_found(self, mock_subprocess, mock_which):
        mock_subprocess.return_value = make_completed_process(
            returncode=1,
            stderr="error: message not found: 99999",
        )
        with pytest.raises(HimalayaError, match="message not found"):
            run("message", "read", "99999")

    def test_empty_stderr_on_failure(self, mock_subprocess, mock_which):
        mock_subprocess.return_value = make_completed_process(
            returncode=1,
            stderr="",
        )
        with pytest.raises(HimalayaError):
            run("account", "list")


class TestTimeouts:
    def test_run_timeout(self, mock_subprocess, mock_which):
        mock_subprocess.side_effect = subprocess.TimeoutExpired(
            cmd=["himalaya", "account", "list"], timeout=30
        )
        with pytest.raises(HimalayaError, match="timed out"):
            run("account", "list")

    def test_run_raw_timeout(self, mock_subprocess, mock_which):
        mock_subprocess.side_effect = subprocess.TimeoutExpired(
            cmd=["himalaya", "template", "send"], timeout=30
        )
        with pytest.raises(HimalayaError, match="timed out"):
            run_raw("template", "send")


class TestOSErrors:
    def test_permission_denied(self, mock_subprocess, mock_which):
        mock_subprocess.side_effect = OSError("Permission denied")
        with pytest.raises(HimalayaError, match="Permission denied"):
            run("account", "list")

    def test_file_not_found(self, mock_subprocess, mock_which):
        mock_subprocess.side_effect = FileNotFoundError("No such file")
        with pytest.raises(HimalayaError, match="No such file"):
            run("account", "list")


class TestMalformedOutput:
    def test_invalid_json(self, mock_subprocess, mock_which):
        mock_subprocess.return_value = make_completed_process(stdout="not valid json {{{")
        with pytest.raises(HimalayaError, match="Failed to parse"):
            run("account", "list")

    def test_truncated_json(self, mock_subprocess, mock_which):
        mock_subprocess.return_value = make_completed_process(stdout='[{"name": "test"')
        with pytest.raises(HimalayaError, match="Failed to parse"):
            run("account", "list")

    def test_html_error_page(self, mock_subprocess, mock_which):
        mock_subprocess.return_value = make_completed_process(
            stdout="<html><body>503 Service Unavailable</body></html>"
        )
        with pytest.raises(HimalayaError, match="Failed to parse"):
            run("account", "list")


class TestToolValidationErrors:
    @pytest.mark.asyncio
    async def test_empty_envelope_id(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.message import message_read

        with pytest.raises(HimalayaError, match="must not be empty"):
            await message_read("")

    @pytest.mark.asyncio
    async def test_malicious_envelope_id(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.message import message_read

        with pytest.raises(HimalayaError, match="Invalid envelope ID"):
            await message_read("1; cat /etc/passwd")

    @pytest.mark.asyncio
    async def test_malicious_folder_name(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.folder import folder_create

        with pytest.raises(HimalayaError, match="Invalid folder name"):
            await folder_create("test$(whoami)")

    @pytest.mark.asyncio
    async def test_invalid_flags(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.flag import flag_add

        with pytest.raises(HimalayaError, match="Unknown flag"):
            await flag_add("1", "notaflag")

    @pytest.mark.asyncio
    async def test_empty_template(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.template import template_send

        with pytest.raises(HimalayaError, match="must not be empty"):
            await template_send("")

    @pytest.mark.asyncio
    async def test_invalid_page(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.envelope import envelope_list

        with pytest.raises(HimalayaError, match="must be >= 1"):
            await envelope_list(page=0)

    @pytest.mark.asyncio
    async def test_invalid_page_size(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.envelope import envelope_list

        with pytest.raises(HimalayaError, match="must be between"):
            await envelope_list(page_size=5000)

    @pytest.mark.asyncio
    async def test_invalid_account_name(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.folder import folder_list

        with pytest.raises(HimalayaError, match="Invalid account name"):
            await folder_list(account="work; rm -rf /")
