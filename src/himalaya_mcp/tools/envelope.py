import json

from himalaya_mcp import cli
from himalaya_mcp.validation import (
    validate_account,
    validate_envelope_id,
    validate_folder_name,
    validate_page,
    validate_page_size,
)


async def envelope_list(
    folder: str | None = None,
    account: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
    query: str | None = None,
) -> str:
    """List message envelopes (headers) in a folder.

    Returns sender, subject, date, and flags for each message without downloading full bodies.

    Args:
        folder: Folder name (e.g. "INBOX"). Defaults to INBOX.
        account: Account name. If omitted, uses the default account.
        page: Page number for pagination (starts at 1).
        page_size: Number of envelopes per page.
        query: Search/filter query string (himalaya query syntax).
    """
    folder = validate_folder_name(folder) if folder else None
    account = validate_account(account)
    page = validate_page(page)
    page_size = validate_page_size(page_size)

    args: list[str] = ["envelope", "list"]
    if page is not None:
        args.extend(["--page", str(page)])
    if page_size is not None:
        args.extend(["--page-size", str(page_size)])
    if query:
        args.extend(["--", query])

    result = cli.run(*args, account=account, folder=folder)
    return json.dumps(result, indent=2) if not isinstance(result, str) else result


async def envelope_thread(
    envelope_id: str,
    folder: str | None = None,
    account: str | None = None,
) -> str:
    """Get thread view for a specific envelope.

    Shows the conversation thread structure for the given message.

    Args:
        envelope_id: The envelope/message ID.
        folder: Folder name. Defaults to INBOX.
        account: Account name. If omitted, uses the default account.
    """
    envelope_id = validate_envelope_id(envelope_id)
    folder = validate_folder_name(folder) if folder else None
    account = validate_account(account)

    result = cli.run("envelope", "thread", envelope_id, account=account, folder=folder)
    return json.dumps(result, indent=2) if not isinstance(result, str) else result
