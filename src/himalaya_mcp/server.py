import os

from mcp.server.fastmcp import FastMCP

from himalaya_mcp.tools import (
    account,
    attachment,
    envelope,
    flag,
    folder,
    message,
    template,
)
from himalaya_mcp.types import DANGER_SEND, DANGER_WRITE, Mode

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

# --- Read-only tools (always registered) ---

mcp.tool()(account.account_list)
mcp.tool()(folder.folder_list)
mcp.tool()(envelope.envelope_list)
mcp.tool()(envelope.envelope_thread)
mcp.tool()(message.message_read)
mcp.tool()(message.message_thread)
mcp.tool()(attachment.attachment_download)
mcp.tool()(template.template_write)
mcp.tool()(template.template_reply)
mcp.tool()(template.template_forward)

# --- Write tools (full and dangerzone modes) ---

if _mode in (Mode.FULL, Mode.DANGERZONE):
    mcp.tool(
        description=f"{DANGER_WRITE} Create a new folder/mailbox.",
    )(folder.folder_create)
    mcp.tool(
        description=f"{DANGER_WRITE} Copy a message to another folder.",
    )(message.message_copy)
    mcp.tool(
        description=f"{DANGER_WRITE} Move a message to another folder.",
    )(message.message_move)
    mcp.tool(
        description=f"{DANGER_WRITE} Save a raw MIME message to a folder.",
    )(message.message_save)
    mcp.tool(
        description=f"{DANGER_WRITE} Add flags to a message (e.g. seen, flagged).",
    )(flag.flag_add)
    mcp.tool(
        description=f"{DANGER_WRITE} Replace all flags on a message.",
    )(flag.flag_set)
    mcp.tool(
        description=f"{DANGER_WRITE} Remove flags from a message.",
    )(flag.flag_remove)
    mcp.tool(
        description=f"{DANGER_WRITE} Compile an MML template and save to a folder (e.g. Drafts).",
    )(template.template_save)

# --- Send tools (dangerzone mode only) ---

_SEND_CONFIRMATION_PROMPT = (
    " IMPORTANT: Before calling this tool, you MUST show the user the full"
    " email content (recipients, subject, body) and ask for their explicit"
    " confirmation to send. Do NOT call this tool without user approval."
)

if _mode == Mode.DANGERZONE:
    mcp.tool(
        description=(
            f"{DANGER_SEND} Send a raw MIME message."
            " This sends a real email to real recipients. IRREVERSIBLE." + _SEND_CONFIRMATION_PROMPT
        ),
    )(message.message_send)
    mcp.tool(
        description=(
            f"{DANGER_SEND} Compile an MML template and SEND the email."
            " This sends a real email to real recipients. IRREVERSIBLE." + _SEND_CONFIRMATION_PROMPT
        ),
    )(template.template_send)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
