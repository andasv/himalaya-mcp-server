import json
import logging

from himalaya_mcp import cli
from himalaya_mcp.validation import (
    validate_account,
    validate_envelope_id,
    validate_folder_name,
    validate_recipients,
    validate_template,
)


async def message_read(
    envelope_id: str,
    folder: str | None = None,
    account: str | None = None,
    headers: bool = False,
    raw: bool = False,
) -> str:
    """Read a message by its envelope ID.

    Returns the plain text body of the message by default.

    Args:
        envelope_id: The envelope/message ID to read.
        folder: Folder name. Defaults to INBOX.
        account: Account name. If omitted, uses the default account.
        headers: If True, include message headers.
        raw: If True, return raw MIME content.
    """
    envelope_id = validate_envelope_id(envelope_id)
    folder = validate_folder_name(folder) if folder else None
    account = validate_account(account)

    args: list[str] = ["message", "read"]
    if headers:
        args.append("--headers")
    if raw:
        args.append("--raw")
    args.append(envelope_id)

    result = cli.run(*args, account=account, folder=folder, output_json=not raw)
    if isinstance(result, (dict, list)):
        return json.dumps(result, indent=2)
    return str(result)


async def message_thread(
    envelope_id: str,
    folder: str | None = None,
    account: str | None = None,
) -> str:
    """Read a full message thread by envelope ID.

    Returns all messages in the conversation thread.

    Args:
        envelope_id: The envelope/message ID.
        folder: Folder name. Defaults to INBOX.
        account: Account name. If omitted, uses the default account.
    """
    envelope_id = validate_envelope_id(envelope_id)
    folder = validate_folder_name(folder) if folder else None
    account = validate_account(account)

    result = cli.run("message", "thread", envelope_id, account=account, folder=folder)
    return json.dumps(result, indent=2) if not isinstance(result, str) else result


async def message_copy(
    envelope_id: str,
    target_folder: str,
    folder: str | None = None,
    account: str | None = None,
) -> str:
    """Copy a message to another folder.

    Args:
        envelope_id: The envelope/message ID to copy.
        target_folder: Destination folder name.
        folder: Source folder name. Defaults to INBOX.
        account: Account name. If omitted, uses the default account.
    """
    envelope_id = validate_envelope_id(envelope_id)
    target_folder = validate_folder_name(target_folder)
    folder = validate_folder_name(folder) if folder else None
    account = validate_account(account)

    result = cli.run(
        "message",
        "copy",
        envelope_id,
        target_folder,
        account=account,
        folder=folder,
        output_json=False,
    )
    return result or f"Message {envelope_id} copied to '{target_folder}'."


async def message_move(
    envelope_id: str,
    target_folder: str,
    folder: str | None = None,
    account: str | None = None,
) -> str:
    """Move a message to another folder.

    The message is removed from the source folder.

    Args:
        envelope_id: The envelope/message ID to move.
        target_folder: Destination folder name.
        folder: Source folder name. Defaults to INBOX.
        account: Account name. If omitted, uses the default account.
    """
    envelope_id = validate_envelope_id(envelope_id)
    target_folder = validate_folder_name(target_folder)
    folder = validate_folder_name(folder) if folder else None
    account = validate_account(account)

    result = cli.run(
        "message",
        "move",
        envelope_id,
        target_folder,
        account=account,
        folder=folder,
        output_json=False,
    )
    return result or f"Message {envelope_id} moved to '{target_folder}'."


async def message_save(
    raw_message: str,
    folder: str | None = None,
    account: str | None = None,
) -> str:
    """Save a raw MIME message to a folder.

    Args:
        raw_message: The raw MIME email content to save.
        folder: Target folder. Defaults to INBOX.
        account: Account name. If omitted, uses the default account.
    """
    raw_message = validate_template(raw_message)
    folder = validate_folder_name(folder) if folder else None
    account = validate_account(account)

    args: list[str] = ["message", "save"]
    if account:
        args.extend(["--account", account])
    if folder:
        args.extend(["--folder", folder])

    result = cli.run_raw(*args, stdin_data=raw_message)
    return result or "Message saved."


async def message_send(raw_message: str, account: str | None = None) -> str:
    """Send a raw MIME message.

    Args:
        raw_message: The raw MIME email content to send.
        account: Account name. If omitted, uses the default account.
    """
    logger = logging.getLogger("himalaya_mcp")
    logger.info("[message_send] validating message (%d bytes)", len(raw_message))
    raw_message = validate_template(raw_message)
    logger.info("[message_send] validating recipients")
    validate_recipients(raw_message)
    account = validate_account(account)

    args: list[str] = ["message", "send"]
    if account:
        args.extend(["--account", account])

    logger.info("[message_send] calling himalaya...")
    from himalaya_mcp.types import SEND_TIMEOUT

    result = cli.run_raw(*args, stdin_data=raw_message, timeout=SEND_TIMEOUT)
    logger.info("[message_send] done")
    return result or "Message sent."
