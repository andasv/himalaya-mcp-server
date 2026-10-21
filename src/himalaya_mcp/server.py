import logging
import os
from collections.abc import Callable
from typing import Any

from mcp.server.fastmcp import FastMCP

from himalaya_mcp import cli
from himalaya_mcp.tools import (
    account,
    attachment,
    envelope,
    flag,
    folder,
    message,
    template,
)
from himalaya_mcp.types import DANGER_SEND, DANGER_WRITE, LOG_LEVEL, Mode

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.WARNING),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

_mode = Mode(os.environ.get("HIMALAYA_MODE", "readonly"))

_server_description = f"Email operations via himalaya CLI. Current mode: {_mode.value.upper()}."
if _mode == Mode.READONLY:
    _server_description += (
        " Only read operations are available."
        " Set HIMALAYA_MODE=full to enable write operations,"
        " or HIMALAYA_MODE=dangerzone to also enable sending emails."
    )
elif _mode == Mode.FULL:
    _server_description += (
        " Write operations are enabled."
        " Tools prefixed with [DANGER: WRITE] modify mailbox data."
        " Sending emails is NOT enabled in this mode."
        " Set HIMALAYA_MODE=dangerzone to enable sending."
    )
else:
    _server_description += (
        " ALL operations are enabled, including sending emails."
        " Tools prefixed with [DANGER: WRITE] modify mailbox data."
        " Tools prefixed with [DANGERZONE: SENDS EMAIL] will send real emails"
        " to real recipients. THIS IS IRREVERSIBLE."
        " CRITICAL: Before sending any email, you MUST show the user the full"
        " email content (recipients, subject, body) and get their explicit"
        " confirmation. NEVER send an email without user approval."
    )

mcp = FastMCP(
    "himalaya",
    instructions=_server_description,
)

# Probe help only: unsupported commands must not be advertised to agents.
_COMMANDS = {
    "account_list": ("account", "list"),
    "folder_list": ("mailbox", "list"),
    "folder_create": ("folder", "create"),
    "envelope_list": ("envelope", "list"),
    "envelope_thread": ("envelope", "thread"),
    "message_thread": ("message", "thread"),
    "message_save": ("message", "add"),
}


def _register(func: Callable[..., Any], **kwargs: Any) -> None:
    command = _COMMANDS.get(func.__name__, tuple(func.__name__.split("_", 1)))
    if cli.supports(*command):
        mcp.tool(**kwargs)(func)
    else:
        logging.getLogger("himalaya_mcp").warning(
            "Skipping unsupported tool %s (%s)", func.__name__, " ".join(command)
        )


# --- Read-only tools (when supported by the installed CLI) ---

_register(account.account_list)
_register(folder.folder_list)
_register(envelope.envelope_list)
_register(envelope.envelope_thread)
_register(message.message_read)
_register(message.message_thread)
_register(attachment.attachment_download)
_register(template.template_write)
_register(template.template_reply)
_register(template.template_forward)

# --- Write tools (full and dangerzone modes) ---

if _mode in (Mode.FULL, Mode.DANGERZONE):
    _register(
        folder.folder_create,
        description=f"{DANGER_WRITE} Create a new folder/mailbox.",
    )
    _register(
        message.message_copy,
        description=f"{DANGER_WRITE} Copy a message to another folder.",
    )
    _register(
        message.message_move,
        description=f"{DANGER_WRITE} Move a message to another folder.",
    )
    _register(
        message.message_save,
        description=f"{DANGER_WRITE} Save a raw MIME message to a folder.",
    )
    _register(
        flag.flag_add,
        description=f"{DANGER_WRITE} Add flags to a message (e.g. seen, flagged).",
    )
    _register(
        flag.flag_set,
        description=f"{DANGER_WRITE} Replace all flags on a message.",
    )
    _register(
        flag.flag_remove,
        description=f"{DANGER_WRITE} Remove flags from a message.",
    )
    _register(
        template.template_save,
        description=f"{DANGER_WRITE} Compile an MML template and save to a folder (e.g. Drafts).",
    )

# --- Send tools (dangerzone mode only) ---

_SEND_CONFIRMATION_PROMPT = (
    " IMPORTANT: Before calling this tool, you MUST show the user the full"
    " email content (recipients, subject, body) and ask for their explicit"
    " confirmation to send. Do NOT call this tool without user approval."
)

if _mode == Mode.DANGERZONE:
    _register(
        message.message_send,
        description=(
            f"{DANGER_SEND} Send a raw MIME message."
            " This sends a real email to real recipients. IRREVERSIBLE." + _SEND_CONFIRMATION_PROMPT
        ),
    )
    _register(
        template.template_send,
        description=(
            f"{DANGER_SEND} Compile an MML template and SEND the email."
            " This sends a real email to real recipients. IRREVERSIBLE." + _SEND_CONFIRMATION_PROMPT
        ),
    )


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
