import logging
import mimetypes
import re
from email import policy
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.parser import Parser
from pathlib import Path

from himalaya_mcp import cli
from himalaya_mcp.tools.message import _find_sent_folder, _save_via_imaplib
from himalaya_mcp.validation import (
    validate_account,
    validate_envelope_id,
    validate_folder_name,
    validate_recipients,
    validate_template,
)

# Matches himalaya's MML attachment tag, e.g.:
#   <#part type=image/jpeg filename="/path/to/file.jpg"><#/part>
#   <#part filename="/path/to/file.jpg"><#/part>
_MML_PART_RE = re.compile(
    r'<#part(?:\s+type=(?P<type>\S+))?\s+filename="(?P<filename>[^"]+)"\s*>\s*<#/part>',
    re.IGNORECASE,
)

# Headers himalaya derives itself when compiling (MIME framing, content
# negotiation) — dropped from the fallback compile so our own multipart
# structure isn't overridden by stale/conflicting values copied from the
# MML source.
_SKIP_HEADERS = {"content-type", "mime-version", "content-transfer-encoding"}


def _compile_mml_to_mime(template: str) -> str:
    """Best-effort MML -> MIME compiler, used only as a last-resort fallback
    when himalaya itself can't save a Sent-copy for a template (see
    _save_sent_copy_for_template below).

    This does NOT aim to replicate mml-lib in full (no PGP/S-MIME, no
    inline/cid parts, no nested multipart alternatives) — it only needs to
    turn "headers + plain-text body + <#part filename=...> attachments"
    (the shape actually produced by this MCP server's own send calls) into
    a faithful-enough MIME message to file away as a Sent-folder record.
    The message actually delivered to the recipient was already compiled
    and sent by himalaya itself; this fallback only affects the local copy.
    """
    parsed = Parser(policy=policy.default).parsestr(template)
    body = parsed.get_payload()
    if not isinstance(body, str):
        raise ValueError("cannot fall back on a non-plain-text MML template")

    attachments = list(_MML_PART_RE.finditer(body))
    clean_body = _MML_PART_RE.sub("", body).rstrip() + "\n"

    msg = MIMEMultipart("mixed")
    for key, value in parsed.items():
        if key.lower() not in _SKIP_HEADERS:
            msg[key] = str(value)
    msg.attach(MIMEText(clean_body, "plain", "utf-8"))

    for match in attachments:
        path = Path(match.group("filename"))
        data = path.read_bytes()
        declared_type = match.group("type")
        ctype = declared_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        maintype, _, subtype = ctype.partition("/")
        part = MIMEBase(maintype or "application", subtype or "octet-stream")
        part.set_payload(data)
        encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename=path.name)
        msg.attach(part)

    return msg.as_string()


def _save_sent_copy_for_template(
    template: str, account: str | None, logger: logging.Logger, log_prefix: str
) -> str:
    """Save a Sent-folder copy of a template that was just sent.

    Mirrors message.message_send's save-copy behavior (auto-detect the
    account's real Sent folder via its IMAP \\Sent special-use flag, never
    raise — the send itself already succeeded by the time this runs), but
    starting from an MML template instead of raw MIME.

    Deliberately does NOT use himalaya's own `template save` command:
    confirmed live (bare CLI, no MCP/Python involved) that on the roelofk
    account it appends the compiled message TWICE per single invocation —
    a distinct, separate bug from the two message_send had to route
    around. Instead this always compiles the MML itself and appends it
    directly via imaplib (the same mechanism message_send already uses as
    its Strato fallback), which only ever performs one APPEND.

    Returns a warning suffix to append to the tool's result on failure, or
    "" on success.
    """
    sent_folder = _find_sent_folder(account)
    if not sent_folder:
        logger.warning(
            "[%s] could not determine Sent folder for account=%r", log_prefix, account
        )
        return " (warning: sent, but could not determine the Sent folder — no copy saved)"

    try:
        compiled = _compile_mml_to_mime(template)
        _save_via_imaplib(account, sent_folder, compiled)
        logger.info("[%s] saved copy to '%s'", log_prefix, sent_folder)
        return ""
    except Exception as exc:
        logger.warning("[%s] could not save a copy to '%s': %s", log_prefix, sent_folder, exc)
        return f" (warning: sent, but could not save a copy to '{sent_folder}': {exc})"


async def template_write(
    account: str | None = None,
    headers: str | None = None,
) -> str:
    """Generate a new email template (MML format).

    Returns a blank email template that can be filled in and sent via template_send.
    MML (MIME Meta Language) is himalaya's format for composing emails.

    Args:
        account: Account name. If omitted, uses the default account.
        headers: Optional pre-filled headers (e.g. "To: user@example.com\\nSubject: Hello").
    """
    account = validate_account(account)

    args: list[str] = ["template", "write"]
    if account:
        args.extend(["--account", account])
    if headers:
        args.extend(["--headers", headers])

    result = cli.run_raw(*args)
    return result


async def template_reply(
    envelope_id: str,
    folder: str | None = None,
    account: str | None = None,
    reply_all: bool = False,
) -> str:
    """Generate a reply template for a message.

    Returns an MML template pre-filled with reply headers and quoted original message.

    Args:
        envelope_id: The envelope/message ID to reply to.
        folder: Folder name. Defaults to INBOX.
        account: Account name. If omitted, uses the default account.
        reply_all: If True, reply to all recipients.
    """
    envelope_id = validate_envelope_id(envelope_id)
    folder = validate_folder_name(folder) if folder else None
    account = validate_account(account)

    args: list[str] = ["template", "reply"]
    if reply_all:
        args.append("--all")
    if account:
        args.extend(["--account", account])
    if folder:
        args.extend(["--folder", folder])
    args.append(envelope_id)

    result = cli.run_raw(*args)
    return result


async def template_forward(
    envelope_id: str,
    folder: str | None = None,
    account: str | None = None,
) -> str:
    """Generate a forward template for a message.

    Returns an MML template pre-filled with forwarded message content.

    Args:
        envelope_id: The envelope/message ID to forward.
        folder: Folder name. Defaults to INBOX.
        account: Account name. If omitted, uses the default account.
    """
    envelope_id = validate_envelope_id(envelope_id)
    folder = validate_folder_name(folder) if folder else None
    account = validate_account(account)

    args: list[str] = ["template", "forward"]
    if account:
        args.extend(["--account", account])
    if folder:
        args.extend(["--folder", folder])
    args.append(envelope_id)

    result = cli.run_raw(*args)
    return result


async def template_save(
    template: str,
    folder: str | None = None,
    account: str | None = None,
) -> str:
    """Compile an MML template to MIME and save it to a folder.

    Saves the compiled email to the specified folder without sending.
    Useful for saving drafts.

    Args:
        template: The MML template content to compile and save.
        folder: Target folder (e.g. "Drafts"). Defaults to INBOX.
        account: Account name. If omitted, uses the default account.
    """
    template = validate_template(template)
    folder = validate_folder_name(folder) if folder else None
    account = validate_account(account)

    args: list[str] = ["template", "save"]
    if account:
        args.extend(["--account", account])
    if folder:
        args.extend(["--folder", folder])

    result = cli.run_raw(*args, stdin_data=template)
    return result or "Template compiled and saved."


async def template_send(
    template: str,
    account: str | None = None,
) -> str:
    """Compile an MML template to MIME and send it.

    This sends the email immediately. The template must include To, Subject, and body.

    After a successful send, a copy is always separately saved to the
    account's real Sent folder (auto-detected via the IMAP \\Sent
    special-use flag) — see _save_sent_copy_for_template. This does not
    rely on himalaya's own built-in send.save-copy config, which is
    disabled account-wide because it fails the entire send with "Mailbox
    does not exist" on iCloud. A failure to save the copy is reported in
    the return value but never raised — the send itself already succeeded
    by that point.

    Args:
        template: The MML template content to compile and send.
        account: Account name. If omitted, uses the default account.
    """
    logger = logging.getLogger("himalaya_mcp")
    logger.info("[template_send] validating template (%d bytes)", len(template))
    template = validate_template(template)
    logger.info("[template_send] validating recipients")
    validate_recipients(template)
    account = validate_account(account)

    args: list[str] = ["template", "send"]
    if account:
        args.extend(["--account", account])

    logger.info("[template_send] calling himalaya...")
    from himalaya_mcp.types import SEND_TIMEOUT

    result = cli.run_raw(*args, stdin_data=template, timeout=SEND_TIMEOUT)
    logger.info("[template_send] done")

    save_note = _save_sent_copy_for_template(template, account, logger, "template_send")
    return (result or "Email sent.") + save_note
