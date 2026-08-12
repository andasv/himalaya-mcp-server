import json
import logging
import subprocess
import tomllib
from pathlib import Path

from himalaya_mcp import cli
from himalaya_mcp.validation import (
    validate_account,
    validate_envelope_id,
    validate_folder_name,
    validate_recipients,
    validate_template,
)

logger = logging.getLogger("himalaya_mcp")

# Fallback names to try (in order) when a folder's IMAP special-use flag
# isn't reported by the server. The \Sent flag match always takes priority.
_SENT_FOLDER_FALLBACKS = ("sent messages", "sent items", "sent", "verzonden items", "verzonden")

# Candidate locations for himalaya's own config file, used only by the
# imaplib fallback below (see _save_via_imaplib) to read connection details
# for an account. Same file himalaya itself reads; not modified here.
_HIMALAYA_CONFIG_PATHS = (
    Path.home() / "Library" / "Application Support" / "himalaya" / "config.toml",
    Path.home() / ".config" / "himalaya" / "config.toml",
)


def _load_himalaya_config() -> dict:
    for path in _HIMALAYA_CONFIG_PATHS:
        if path.exists():
            with open(path, "rb") as f:
                return tomllib.load(f)
    return {}


def _resolve_password(auth: dict) -> str | None:
    if "raw" in auth:
        return auth["raw"]
    if "cmd" in auth:
        try:
            proc = subprocess.run(
                auth["cmd"], shell=True, capture_output=True, text=True, timeout=10
            )
            if proc.returncode == 0:
                return proc.stdout.strip()
        except Exception:
            logger.warning("[_resolve_password] auth.cmd failed")
    return None


def _save_via_imaplib(account: str | None, folder: str, raw_message: str) -> None:
    """Fallback save path for IMAP servers whose APPEND response himalaya's
    Rust client can't parse.

    Observed on Strato: the server includes an APPENDUID response code
    (RFC 4315) in the tagged OK reply, which himalaya v1.2.0 chokes on
    ("stream error: unexpected tag in command completion result") even
    though the append itself is accepted server-side... except it isn't
    actually accepted, since himalaya aborts the command on the parse
    error. Python's stdlib imaplib parses this response fine, so it's used
    here as a direct fallback rather than waiting on an upstream fix.
    """
    import imaplib

    config = _load_himalaya_config()
    accounts = config.get("accounts", {})
    acct_key = account or next(
        (name for name, cfg in accounts.items() if cfg.get("default")), None
    )
    if not acct_key or acct_key not in accounts:
        raise RuntimeError(f"account {acct_key!r} not found in himalaya config")

    imap_cfg = accounts[acct_key].get("backend", {})
    if imap_cfg.get("type") != "imap":
        raise RuntimeError(f"account {acct_key!r} has no imap backend configured")

    password = _resolve_password(imap_cfg.get("auth", {}))
    if not password:
        raise RuntimeError(f"could not resolve password for account {acct_key!r}")

    conn = imaplib.IMAP4_SSL(imap_cfg["host"], imap_cfg.get("port", 993))
    try:
        conn.login(imap_cfg["login"], password)
        typ, data = conn.append(f'"{folder}"', None, None, raw_message.encode("utf-8"))
        if typ != "OK":
            raise RuntimeError(f"IMAP APPEND failed: {typ} {data!r}")
    finally:
        try:
            conn.logout()
        except Exception:
            pass


def _find_sent_folder(account: str | None) -> str | None:
    """Find the account's real Sent folder name.

    Prefers the folder whose IMAP special-use attribute is \\Sent (this is
    reported regardless of what the folder happens to be named locally,
    e.g. "Sent Messages" on iCloud vs. "Sent Items" on Strato). Falls back
    to common name guesses only if no special-use flag is present at all.
    """
    try:
        folders = cli.run("folder", "list", account=account)
    except Exception:
        logger.warning("[_find_sent_folder] could not list folders for account=%r", account)
        return None

    if not isinstance(folders, list):
        return None

    for f in folders:
        desc = (f.get("desc") or "")
        if "\\sent" in desc.lower():
            return f.get("name")

    by_lower = {(f.get("name") or "").lower(): f.get("name") for f in folders}
    for candidate in _SENT_FOLDER_FALLBACKS:
        if candidate in by_lower:
            return by_lower[candidate]

    return None


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
        target_folder,
        envelope_id,
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
        target_folder,
        envelope_id,
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

    After a successful send, a copy is always separately saved to the
    account's real Sent folder (auto-detected via the IMAP \\Sent
    special-use flag). This does not rely on himalaya's own built-in
    send.save-copy config, which has been observed to fail the entire
    send with "Mailbox does not exist" on some providers even though the
    message was actually delivered. A failure to save the copy is
    reported in the return value but never raised — the send itself
    already succeeded by that point.

    Args:
        raw_message: The raw MIME email content to send.
        account: Account name. If omitted, uses the default account.
    """
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

    save_note = ""
    sent_folder = _find_sent_folder(account)
    if sent_folder:
        try:
            cli.run_raw(
                "message",
                "save",
                *(["--account", account] if account else []),
                "--folder",
                sent_folder,
                stdin_data=raw_message,
            )
            logger.info("[message_send] saved copy to '%s'", sent_folder)
        except Exception as exc:
            logger.warning(
                "[message_send] himalaya save failed for '%s': %s — trying imaplib fallback",
                sent_folder,
                exc,
            )
            try:
                _save_via_imaplib(account, sent_folder, raw_message)
                logger.info(
                    "[message_send] saved copy to '%s' via imaplib fallback", sent_folder
                )
            except Exception as exc2:
                logger.warning("[message_send] imaplib fallback also failed: %s", exc2)
                save_note = (
                    f" (warning: sent, but could not save a copy to '{sent_folder}': {exc2})"
                )
    else:
        logger.warning("[message_send] could not determine Sent folder for account=%r", account)
        save_note = " (warning: sent, but could not determine the Sent folder — no copy saved)"

    return (result or "Message sent.") + save_note
