import json
from unittest.mock import patch

import pytest

from tests.conftest import make_completed_process


class TestAccountTools:
    @pytest.mark.asyncio
    async def test_account_list(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.account import account_list

        accounts = [{"name": "default", "backend": "imap", "default": True}]
        mock_subprocess.return_value = make_completed_process(stdout=json.dumps(accounts))

        result = await account_list()
        assert json.loads(result) == accounts


class TestFolderTools:
    @pytest.mark.asyncio
    async def test_folder_list(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.folder import folder_list

        folders = [{"name": "INBOX"}, {"name": "Sent"}]
        mock_subprocess.return_value = make_completed_process(stdout=json.dumps(folders))

        result = await folder_list()
        assert json.loads(result) == folders

    @pytest.mark.asyncio
    async def test_folder_list_with_account(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.folder import folder_list

        mock_subprocess.return_value = make_completed_process(stdout=json.dumps([]))

        await folder_list(account="work")
        cmd = mock_subprocess.call_args[0][0]
        assert "--account" in cmd
        assert "work" in cmd

    @pytest.mark.asyncio
    async def test_folder_create(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.folder import folder_create

        mock_subprocess.return_value = make_completed_process(stdout="")
        result = await folder_create("Archive")
        assert "Archive" in result
        assert "created" in result


class TestEnvelopeTools:
    @pytest.mark.asyncio
    async def test_envelope_list(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.envelope import envelope_list

        envelopes = [{"id": "1", "subject": "Hello", "from": "a@b.com"}]
        mock_subprocess.return_value = make_completed_process(stdout=json.dumps(envelopes))

        result = await envelope_list()
        assert json.loads(result) == envelopes

    @pytest.mark.asyncio
    async def test_envelope_list_with_pagination(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.envelope import envelope_list

        mock_subprocess.return_value = make_completed_process(stdout=json.dumps([]))

        await envelope_list(page=2, page_size=25)
        cmd = mock_subprocess.call_args[0][0]
        assert "--page" in cmd
        assert "2" in cmd
        assert "--page-size" in cmd
        assert "25" in cmd

    @pytest.mark.asyncio
    async def test_envelope_list_with_query(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.envelope import envelope_list

        mock_subprocess.return_value = make_completed_process(stdout=json.dumps([]))

        await envelope_list(query="from:test@test.com")
        cmd = mock_subprocess.call_args[0][0]
        assert "--" in cmd
        assert "from:test@test.com" in cmd

    @pytest.mark.asyncio
    async def test_envelope_thread(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.envelope import envelope_thread

        thread = [{"id": "1"}, {"id": "2"}]
        mock_subprocess.return_value = make_completed_process(stdout=json.dumps(thread))

        result = await envelope_thread("1")
        assert json.loads(result) == thread


class TestMessageTools:
    @pytest.mark.asyncio
    async def test_message_read(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.message import message_read

        msg = {"body": "Hello world"}
        mock_subprocess.return_value = make_completed_process(stdout=json.dumps(msg))

        result = await message_read("1")
        assert json.loads(result) == msg

    @pytest.mark.asyncio
    async def test_message_read_raw(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.message import message_read

        raw_mime = "From: a@b.com\r\nTo: c@d.com\r\n\r\nBody"
        mock_subprocess.return_value = make_completed_process(stdout=raw_mime)

        result = await message_read("1", raw=True)
        assert result == raw_mime

    @pytest.mark.asyncio
    async def test_message_read_with_headers(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.message import message_read

        mock_subprocess.return_value = make_completed_process(stdout=json.dumps({"body": "hi"}))

        await message_read("1", headers=True)
        cmd = mock_subprocess.call_args[0][0]
        assert "--headers" in cmd

    @pytest.mark.asyncio
    async def test_message_thread(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.message import message_thread

        thread = [{"id": "1", "body": "hi"}, {"id": "2", "body": "hello"}]
        mock_subprocess.return_value = make_completed_process(stdout=json.dumps(thread))

        result = await message_thread("1")
        assert json.loads(result) == thread

    @pytest.mark.asyncio
    async def test_message_copy(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.message import message_copy

        mock_subprocess.return_value = make_completed_process(stdout="")

        result = await message_copy("1", "Archive")
        assert "copied" in result
        assert "Archive" in result

    @pytest.mark.asyncio
    async def test_message_move(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.message import message_move

        mock_subprocess.return_value = make_completed_process(stdout="")

        result = await message_move("1", "Trash")
        assert "moved" in result
        assert "Trash" in result

    @pytest.mark.asyncio
    async def test_message_save(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.message import message_save

        mock_subprocess.return_value = make_completed_process(stdout="")

        result = await message_save("From: a@b.com\nTo: c@d.com\n\nBody")
        assert "saved" in result.lower()

    @pytest.mark.asyncio
    async def test_message_send(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.message import message_send

        mock_subprocess.return_value = make_completed_process(stdout="")

        with patch.dict("os.environ", {"APPROVED_RECIPIENTS": "c@d.com"}):
            result = await message_send("From: a@b.com\nTo: c@d.com\n\nBody")
        assert "sent" in result.lower()


class TestFlagTools:
    @pytest.mark.asyncio
    async def test_flag_add(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.flag import flag_add

        mock_subprocess.return_value = make_completed_process(stdout="")

        result = await flag_add("1", "seen")
        assert "added" in result

    @pytest.mark.asyncio
    async def test_flag_set(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.flag import flag_set

        mock_subprocess.return_value = make_completed_process(stdout="")

        result = await flag_set("1", "seen flagged")
        assert "set" in result

    @pytest.mark.asyncio
    async def test_flag_remove(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.flag import flag_remove

        mock_subprocess.return_value = make_completed_process(stdout="")

        result = await flag_remove("1", "flagged")
        assert "removed" in result


class TestAttachmentTools:
    @pytest.mark.asyncio
    async def test_attachment_download(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.attachment import attachment_download

        mock_subprocess.return_value = make_completed_process(stdout="")

        result = await attachment_download("1")
        assert "downloaded" in result


class TestTemplateTools:
    @pytest.mark.asyncio
    async def test_template_write(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.template import template_write

        tpl = "From: me@test.com\nTo: \nSubject: \n\n"
        mock_subprocess.return_value = make_completed_process(stdout=tpl)

        result = await template_write()
        assert "From:" in result

    @pytest.mark.asyncio
    async def test_template_reply(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.template import template_reply

        tpl = "From: me@test.com\nTo: sender@test.com\nSubject: Re: Hello\n\n> Original"
        mock_subprocess.return_value = make_completed_process(stdout=tpl)

        result = await template_reply("1")
        assert "Re:" in result

    @pytest.mark.asyncio
    async def test_template_reply_all(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.template import template_reply

        mock_subprocess.return_value = make_completed_process(stdout="reply template")

        await template_reply("1", reply_all=True)
        cmd = mock_subprocess.call_args[0][0]
        assert "--all" in cmd

    @pytest.mark.asyncio
    async def test_template_forward(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.template import template_forward

        tpl = "From: me@test.com\nTo: \nSubject: Fwd: Hello\n\n> Forwarded"
        mock_subprocess.return_value = make_completed_process(stdout=tpl)

        result = await template_forward("1")
        assert "Fwd:" in result

    @pytest.mark.asyncio
    async def test_template_save(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.template import template_save

        mock_subprocess.return_value = make_completed_process(stdout="")

        result = await template_save("From: a@b.com\nTo: c@d.com\n\nBody", folder="Drafts")
        assert "saved" in result.lower()

    @pytest.mark.asyncio
    async def test_template_send(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.template import template_send

        mock_subprocess.return_value = make_completed_process(stdout="")

        with patch.dict("os.environ", {"APPROVED_RECIPIENTS": "c@d.com"}):
            result = await template_send("From: a@b.com\nTo: c@d.com\n\nBody")
        assert "sent" in result.lower()
