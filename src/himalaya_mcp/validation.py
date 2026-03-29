import email.utils
import os
import re

from himalaya_mcp.cli import HimalayaError

# Envelope IDs are typically numeric or alphanumeric (provider-dependent)
_ENVELOPE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9._\-]+$")

# Folder names: printable chars, no shell metacharacters
_FOLDER_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9._\-/\[\] ]+$")

# Known himalaya flags
VALID_FLAGS = frozenset(
    {
        "seen",
        "answered",
        "flagged",
        "deleted",
        "draft",
        "\\seen",
        "\\answered",
        "\\flagged",
        "\\deleted",
        "\\draft",
    }
)

_MAX_TEMPLATE_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_envelope_id(envelope_id: str) -> str:
    envelope_id = envelope_id.strip()
    if not envelope_id:
        raise HimalayaError("Envelope ID must not be empty.")
    if not _ENVELOPE_ID_PATTERN.match(envelope_id):
        raise HimalayaError(
            f"Invalid envelope ID: {envelope_id!r}. "
            "Must contain only alphanumeric characters, dots, hyphens, or underscores."
        )
    return envelope_id


def validate_folder_name(name: str) -> str:
    name = name.strip()
    if not name:
        raise HimalayaError("Folder name must not be empty.")
    if not _FOLDER_NAME_PATTERN.match(name):
        raise HimalayaError(
            f"Invalid folder name: {name!r}. "
            "Must contain only alphanumeric characters, dots, hyphens, slashes, "
            "brackets, or spaces."
        )
    return name


def validate_flags(flags: str) -> str:
    flags = flags.strip()
    if not flags:
        raise HimalayaError("Flags must not be empty.")
    flag_list = flags.split()
    for f in flag_list:
        if f.lower() not in VALID_FLAGS and not f.startswith("$"):
            raise HimalayaError(
                f"Unknown flag: {f!r}. "
                f"Known flags: {', '.join(sorted(VALID_FLAGS))}. "
                "Custom flags must start with '$'."
            )
    return flags


def validate_template(template: str) -> str:
    if not template or not template.strip():
        raise HimalayaError("Template content must not be empty.")
    if len(template) > _MAX_TEMPLATE_SIZE:
        raise HimalayaError(
            f"Template too large ({len(template)} bytes). Maximum is {_MAX_TEMPLATE_SIZE} bytes."
        )
    return template


def validate_account(account: str | None) -> str | None:
    if account is None:
        return None
    account = account.strip()
    if not account:
        return None
    if not re.match(r"^[a-zA-Z0-9._\-@]+$", account):
        raise HimalayaError(
            f"Invalid account name: {account!r}. "
            "Must contain only alphanumeric characters, dots, hyphens, underscores, or @."
        )
    return account


def validate_page(page: int | None) -> int | None:
    if page is None:
        return None
    if page < 1:
        raise HimalayaError(f"Page must be >= 1, got {page}.")
    return page


def validate_page_size(page_size: int | None) -> int | None:
    if page_size is None:
        return None
    if page_size < 1 or page_size > 1000:
        raise HimalayaError(f"Page size must be between 1 and 1000, got {page_size}.")
    return page_size


def _parse_recipients(message_content: str) -> list[str]:
    """Extract all recipient email addresses from To, Cc, and Bcc headers."""
    recipients: list[str] = []
    for line in message_content.splitlines():
        lower = line.lower()
        if lower.startswith(("to:", "cc:", "bcc:")):
            header_value = line.split(":", 1)[1]
            parsed = email.utils.getaddresses([header_value])
            for _name, addr in parsed:
                addr = addr.strip().lower()
                if addr:
                    recipients.append(addr)
        elif not line.startswith((" ", "\t")) and ":" not in line:
            break
    return recipients


def _get_approved_recipients() -> set[str] | None:
    """Read APPROVED_RECIPIENTS env var. Returns None if not set."""
    raw = os.environ.get("APPROVED_RECIPIENTS", "").strip()
    if not raw:
        return None
    return {addr.strip().lower() for addr in raw.split(",") if addr.strip()}


def validate_recipients(message_content: str) -> None:
    """Validate that all recipients are in the approved list.

    Raises HimalayaError if APPROVED_RECIPIENTS is set and any recipient
    is not in the list, or if no APPROVED_RECIPIENTS is configured.
    """
    approved = _get_approved_recipients()
    if approved is None:
        raise HimalayaError(
            "Cannot send email: no approved recipients configured. "
            "To allow sending, set the APPROVED_RECIPIENTS environment variable "
            "in your MCP server configuration with a comma-separated list of "
            "allowed email addresses. "
            "Example: APPROVED_RECIPIENTS=alice@example.com,bob@example.com"
        )

    recipients = _parse_recipients(message_content)
    if not recipients:
        raise HimalayaError(
            "Cannot send email: no recipients found in the message. "
            "Make sure the message includes To, Cc, or Bcc headers."
        )

    unapproved = [addr for addr in recipients if addr not in approved]
    if unapproved:
        unapproved_str = ", ".join(unapproved)
        approved_str = ", ".join(sorted(approved))
        raise HimalayaError(
            f"Cannot send email: the following recipients are not approved: "
            f"{unapproved_str}. "
            f"Currently approved recipients: {approved_str}. "
            f"To add new recipients, update the APPROVED_RECIPIENTS environment "
            f"variable in your MCP server configuration (claude_desktop_config.json)."
        )
