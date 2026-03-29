from himalaya_mcp import cli
from himalaya_mcp.validation import (
    validate_account,
    validate_envelope_id,
    validate_folder_name,
    validate_recipients,
    validate_template,
)


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

    Args:
        template: The MML template content to compile and send.
        account: Account name. If omitted, uses the default account.
    """
    template = validate_template(template)
    validate_recipients(template)
    account = validate_account(account)

    args: list[str] = ["template", "send"]
    if account:
        args.extend(["--account", account])

    result = cli.run_raw(*args, stdin_data=template)
    return result or "Email sent."
