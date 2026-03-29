from himalaya_mcp import cli
from himalaya_mcp.validation import (
    validate_account,
    validate_envelope_id,
    validate_flags,
    validate_folder_name,
)


async def flag_add(
    envelope_id: str,
    flags: str,
    folder: str | None = None,
    account: str | None = None,
) -> str:
    """Add flags to a message.

    Common flags: seen, answered, flagged, deleted, draft.

    Args:
        envelope_id: The envelope/message ID.
        flags: Space-separated flag names to add (e.g. "seen flagged").
        folder: Folder name. Defaults to INBOX.
        account: Account name. If omitted, uses the default account.
    """
    envelope_id = validate_envelope_id(envelope_id)
    flags = validate_flags(flags)
    folder = validate_folder_name(folder) if folder else None
    account = validate_account(account)

    result = cli.run(
        "flag",
        "add",
        envelope_id,
        flags,
        account=account,
        folder=folder,
        output_json=False,
    )
    return result or f"Flags '{flags}' added to message {envelope_id}."


async def flag_set(
    envelope_id: str,
    flags: str,
    folder: str | None = None,
    account: str | None = None,
) -> str:
    """Replace all flags on a message.

    This replaces all existing flags with the specified ones.
    Common flags: seen, answered, flagged, deleted, draft.

    Args:
        envelope_id: The envelope/message ID.
        flags: Space-separated flag names to set (e.g. "seen").
        folder: Folder name. Defaults to INBOX.
        account: Account name. If omitted, uses the default account.
    """
    envelope_id = validate_envelope_id(envelope_id)
    flags = validate_flags(flags)
    folder = validate_folder_name(folder) if folder else None
    account = validate_account(account)

    result = cli.run(
        "flag",
        "set",
        envelope_id,
        flags,
        account=account,
        folder=folder,
        output_json=False,
    )
    return result or f"Flags on message {envelope_id} set to '{flags}'."


async def flag_remove(
    envelope_id: str,
    flags: str,
    folder: str | None = None,
    account: str | None = None,
) -> str:
    """Remove flags from a message.

    Common flags: seen, answered, flagged, deleted, draft.

    Args:
        envelope_id: The envelope/message ID.
        flags: Space-separated flag names to remove (e.g. "flagged").
        folder: Folder name. Defaults to INBOX.
        account: Account name. If omitted, uses the default account.
    """
    envelope_id = validate_envelope_id(envelope_id)
    flags = validate_flags(flags)
    folder = validate_folder_name(folder) if folder else None
    account = validate_account(account)

    result = cli.run(
        "flag",
        "remove",
        envelope_id,
        flags,
        account=account,
        folder=folder,
        output_json=False,
    )
    return result or f"Flags '{flags}' removed from message {envelope_id}."
