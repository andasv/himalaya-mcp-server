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

        # himalaya's CLI is `message copy <TARGET> <ID>...` — target folder
        # first, id last. Passing them in the wrong order makes himalaya
        # try to parse the folder name as an envelope id and fail outright.
        cmd = mock_subprocess.call_args[0][0]
        assert cmd.index("Archive") < cmd.index("1")

    @pytest.mark.asyncio
    async def test_message_move(self, mock_subprocess, mock_which):
        from himalaya_mcp.tools.message import message_move

        mock_subprocess.return_value = make_completed_process(stdout="")

        result = await message_move("1", "Trash")
        assert "moved" in result
        assert "Trash" in result

        # Same argument order requirement as `message copy` above.
        cmd = mock_subprocess.call_args[0][0]
        assert cmd.index("Trash") < cmd.index("1")

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

    @pytest.mark.asyncio
    async def test_template_send_saves_sent_copy(self, mock_subprocess, mock_which):
        """template_send must not rely on himalaya's own (disabled)
        send.save-copy, NOR on himalaya's `template save` (confirmed live to
        double-append on this account — see _save_sent_copy_for_template's
        docstring). It should compile the MML itself and append exactly
        once via imaplib once the account's real Sent folder is found."""
        from himalaya_mcp.tools import template as template_mod

        sent_folder_json = json.dumps([{"name": "Sent Messages", "desc": "\\Sent"}])

        def side_effect(cmd, **kwargs):
            if "folder" in cmd and "list" in cmd:
                return make_completed_process(stdout=sent_folder_json)
            return make_completed_process(stdout="")

        mock_subprocess.side_effect = side_effect

        with patch.object(template_mod, "_save_via_imaplib") as mock_imaplib:
            result = await template_mod.template_send(
                "From: a@b.com\nTo: c@d.com\nSubject: Hi\n\nBody"
            )

        assert "sent" in result.lower()
        assert "warning" not in result.lower()

        # Never shells out to the buggy `template save` command.
        save_calls = [
            call
            for call in mock_subprocess.call_args_list
            if "template" in call.args[0] and "save" in call.args[0]
        ]
        assert len(save_calls) == 0

        mock_imaplib.assert_called_once()
        assert mock_imaplib.call_args.args[1] == "Sent Messages"

    @pytest.mark.asyncio
    async def test_template_send_warns_when_save_copy_fails(self, mock_subprocess, mock_which):
        """If the compiled-MIME imaplib append itself fails, template_send
        should still report the send as successful but flag the missing
        copy, rather than raising and losing the "it did send" signal."""
        from himalaya_mcp.tools import template as template_mod

        sent_folder_json = json.dumps([{"name": "Sent Items", "desc": "\\Sent"}])

        def side_effect(cmd, **kwargs):
            if "folder" in cmd and "list" in cmd:
                return make_completed_process(stdout=sent_folder_json)
            return make_completed_process(stdout="")

        mock_subprocess.side_effect = side_effect

        with patch.object(
            template_mod, "_save_via_imaplib", side_effect=RuntimeError("boom")
        ):
            result = await template_mod.template_send(
                "From: a@b.com\nTo: c@d.com\nSubject: Hi\n\nBody"
            )

        assert "sent" in result.lower()
        assert "could not save a copy to 'sent items'" in result.lower()

    @pytest.mark.asyncio
    async def test_template_send_warns_when_sent_folder_unknown(
        self, mock_subprocess, mock_which
    ):
        """If the Sent folder can't be determined at all, template_send
        must still report success (the send itself worked) but flag that
        no copy was saved, rather than failing silently."""
        from himalaya_mcp.tools.template import template_send

        def side_effect(cmd, **kwargs):
            if "folder" in cmd and "list" in cmd:
                return make_completed_process(stdout=json.dumps([{"name": "INBOX", "desc": ""}]))
            return make_completed_process(stdout="")

        mock_subprocess.side_effect = side_effect

        result = await template_send("From: a@b.com\nTo: c@d.com\nSubject: Hi\n\nBody")

        assert "sent" in result.lower()
        assert "could not determine the sent folder" in result.lower()


class TestCompileMmlToMime:
    def test_compiles_headers_body_and_attachment(self, tmp_path):
        """The fallback compiler only needs to handle this MCP server's own
        output shape: headers + plain-text body + <#part filename=...>
        attachment tags — not the full MML feature set."""
        import email

        from himalaya_mcp.tools.template import _compile_mml_to_mime

        attachment = tmp_path / "photo.jpg"
        attachment.write_bytes(b"\xff\xd8\xff\xe0fake-jpeg-bytes")

        template = (
            "From: Roelof Koelewijn <roelofk@me.com>\n"
            "To: service@energieopmaat.net\n"
            "Subject: Test met bijlage\n"
            "\n"
            "Beste Christiaan,\n"
            "\n"
            "Hierbij de foto.\n"
            f'<#part filename="{attachment}"><#/part>\n'
        )

        compiled = _compile_mml_to_mime(template)
        msg = email.message_from_string(compiled)

        assert msg["To"] == "service@energieopmaat.net"
        assert msg["Subject"] == "Test met bijlage"
        assert msg.is_multipart()

        parts = msg.get_payload()
        assert len(parts) == 2
        body_text = parts[0].get_payload(decode=True).decode(
            parts[0].get_content_charset() or "utf-8"
        )
        assert "Hierbij de foto." in body_text
        assert "<#part" not in body_text
        assert parts[1].get_filename() == "photo.jpg"
        assert parts[1].get_payload(decode=True) == attachment.read_bytes()

    def test_compiles_without_attachment(self):
        import email

        from himalaya_mcp.tools.template import _compile_mml_to_mime

        compiled = _compile_mml_to_mime("From: a@b.com\nTo: c@d.com\nSubject: Hi\n\nJust text.\n")
        msg = email.message_from_string(compiled)

        assert msg["To"] == "c@d.com"
        part = msg.get_payload()[0]
        body_text = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8")
        assert "Just text." in body_text
