from himalaya_mcp import cli
from himalaya_mcp.validation import validate_account, validate_envelope_id, validate_folder_name


async def attachment_download(
    envelope_id: str,
    folder: str | None = None,
    account: str | None = None,
) -> str:
    """Download all attachments from a message.

    Attachments are saved to the current working directory.

    Args:
        envelope_id: The envelope/message ID.
        folder: Folder name. Defaults to INBOX.
        account: Account name. If omitted, uses the default account.
    """
    envelope_id = validate_envelope_id(envelope_id)
    folder = validate_folder_name(folder) if folder else None
    account = validate_account(account)

    result = cli.run(
        "attachment",
        "download",
        envelope_id,
        account=account,
        folder=folder,
        output_json=False,
    )
    return result or f"Attachments from message {envelope_id} downloaded."
