import os
from unittest.mock import patch

import pytest

from himalaya_mcp.cli import HimalayaError
from himalaya_mcp.validation import (
    validate_account,
    validate_envelope_id,
    validate_flags,
    validate_folder_name,
    validate_page,
    validate_page_size,
    validate_recipients,
    validate_template,
)


class TestValidateEnvelopeId:
    def test_valid_numeric(self):
        assert validate_envelope_id("123") == "123"

    def test_valid_alphanumeric(self):
        assert validate_envelope_id("abc-123_456.789") == "abc-123_456.789"

    def test_strips_whitespace(self):
        assert validate_envelope_id("  123  ") == "123"

    def test_empty(self):
        with pytest.raises(HimalayaError, match="must not be empty"):
            validate_envelope_id("")

    def test_whitespace_only(self):
        with pytest.raises(HimalayaError, match="must not be empty"):
            validate_envelope_id("   ")

    def test_shell_metacharacters(self):
        with pytest.raises(HimalayaError, match="Invalid envelope ID"):
            validate_envelope_id("123; rm -rf /")

    def test_backticks(self):
        with pytest.raises(HimalayaError, match="Invalid envelope ID"):
            validate_envelope_id("`whoami`")

    def test_dollar_expansion(self):
        with pytest.raises(HimalayaError, match="Invalid envelope ID"):
            validate_envelope_id("$(cat /etc/passwd)")


class TestValidateFolderName:
    def test_valid_simple(self):
        assert validate_folder_name("INBOX") == "INBOX"

    def test_valid_with_slash(self):
        assert validate_folder_name("INBOX/subfolder") == "INBOX/subfolder"

    def test_valid_with_brackets(self):
        assert validate_folder_name("[Gmail]/All Mail") == "[Gmail]/All Mail"

    def test_strips_whitespace(self):
        assert validate_folder_name("  Drafts  ") == "Drafts"

    def test_empty(self):
        with pytest.raises(HimalayaError, match="must not be empty"):
            validate_folder_name("")

    def test_shell_injection(self):
        with pytest.raises(HimalayaError, match="Invalid folder name"):
            validate_folder_name("INBOX; rm -rf /")

    def test_backticks(self):
        with pytest.raises(HimalayaError, match="Invalid folder name"):
            validate_folder_name("`whoami`")


class TestValidateFlags:
    def test_valid_single(self):
        assert validate_flags("seen") == "seen"

    def test_valid_multiple(self):
        assert validate_flags("seen flagged") == "seen flagged"

    def test_valid_backslash_prefix(self):
        assert validate_flags("\\seen") == "\\seen"

    def test_valid_custom_flag(self):
        assert validate_flags("$custom") == "$custom"

    def test_empty(self):
        with pytest.raises(HimalayaError, match="must not be empty"):
            validate_flags("")

    def test_unknown_flag(self):
        with pytest.raises(HimalayaError, match="Unknown flag"):
            validate_flags("nonexistent")

    def test_mixed_valid_invalid(self):
        with pytest.raises(HimalayaError, match="Unknown flag"):
            validate_flags("seen badone")


class TestValidateTemplate:
    def test_valid(self):
        tpl = "From: a@b.com\nTo: c@d.com\nSubject: Hi\n\nHello"
        assert validate_template(tpl) == tpl

    def test_empty(self):
        with pytest.raises(HimalayaError, match="must not be empty"):
            validate_template("")

    def test_whitespace_only(self):
        with pytest.raises(HimalayaError, match="must not be empty"):
            validate_template("   ")

    def test_too_large(self):
        huge = "x" * (10 * 1024 * 1024 + 1)
        with pytest.raises(HimalayaError, match="too large"):
            validate_template(huge)


class TestValidateAccount:
    def test_none(self):
        assert validate_account(None) is None

    def test_empty_string(self):
        assert validate_account("") is None

    def test_valid(self):
        assert validate_account("work") == "work"

    def test_valid_with_at(self):
        assert validate_account("user@gmail.com") == "user@gmail.com"

    def test_invalid_characters(self):
        with pytest.raises(HimalayaError, match="Invalid account name"):
            validate_account("work; rm -rf /")


class TestValidatePage:
    def test_none(self):
        assert validate_page(None) is None

    def test_valid(self):
        assert validate_page(1) == 1

    def test_zero(self):
        with pytest.raises(HimalayaError, match="must be >= 1"):
            validate_page(0)

    def test_negative(self):
        with pytest.raises(HimalayaError, match="must be >= 1"):
            validate_page(-1)


class TestValidatePageSize:
    def test_none(self):
        assert validate_page_size(None) is None

    def test_valid(self):
        assert validate_page_size(50) == 50

    def test_zero(self):
        with pytest.raises(HimalayaError, match="must be between"):
            validate_page_size(0)

    def test_too_large(self):
        with pytest.raises(HimalayaError, match="must be between"):
            validate_page_size(1001)


class TestValidateRecipients:
    def test_no_approved_recipients_configured(self):
        env = os.environ.copy()
        env.pop("APPROVED_RECIPIENTS", None)
        with (
            patch.dict(os.environ, env, clear=True),
            pytest.raises(HimalayaError, match="no approved recipients configured"),
        ):
            validate_recipients("To: alice@example.com\nSubject: Hi\n\nBody")

    def test_approved_recipient_passes(self):
        with patch.dict(os.environ, {"APPROVED_RECIPIENTS": "alice@example.com"}):
            validate_recipients("To: alice@example.com\nSubject: Hi\n\nBody")

    def test_unapproved_recipient_blocked(self):
        with (
            patch.dict(os.environ, {"APPROVED_RECIPIENTS": "alice@example.com"}),
            pytest.raises(HimalayaError, match="not approved"),
        ):
            validate_recipients("To: eve@evil.com\nSubject: Hi\n\nBody")

    def test_multiple_approved_recipients(self):
        with patch.dict(os.environ, {"APPROVED_RECIPIENTS": "alice@example.com,bob@example.com"}):
            validate_recipients("To: alice@example.com\nCc: bob@example.com\nSubject: Hi\n\nBody")

    def test_mixed_approved_and_unapproved(self):
        with (
            patch.dict(os.environ, {"APPROVED_RECIPIENTS": "alice@example.com"}),
            pytest.raises(HimalayaError, match=r"eve@evil\.com"),
        ):
            validate_recipients("To: alice@example.com, eve@evil.com\nSubject: Hi\n\nBody")

    def test_case_insensitive(self):
        with patch.dict(os.environ, {"APPROVED_RECIPIENTS": "Alice@Example.com"}):
            validate_recipients("To: alice@example.com\nSubject: Hi\n\nBody")

    def test_bcc_also_validated(self):
        with (
            patch.dict(os.environ, {"APPROVED_RECIPIENTS": "alice@example.com"}),
            pytest.raises(HimalayaError, match="not approved"),
        ):
            validate_recipients("To: alice@example.com\nBcc: spy@evil.com\nSubject: Hi\n\nBody")

    def test_no_recipients_in_message(self):
        with (
            patch.dict(os.environ, {"APPROVED_RECIPIENTS": "alice@example.com"}),
            pytest.raises(HimalayaError, match="no recipients found"),
        ):
            validate_recipients("Subject: Hi\n\nBody with no To header")

    def test_named_recipients(self):
        with patch.dict(os.environ, {"APPROVED_RECIPIENTS": "alice@example.com"}):
            validate_recipients('To: "Alice Smith" <alice@example.com>\nSubject: Hi\n\nBody')

    def test_error_message_shows_how_to_fix(self):
        with (
            patch.dict(os.environ, {"APPROVED_RECIPIENTS": "alice@example.com"}),
            pytest.raises(HimalayaError, match=r"claude_desktop_config\.json"),
        ):
            validate_recipients("To: unknown@test.com\nSubject: Hi\n\nBody")
