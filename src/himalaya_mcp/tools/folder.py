import json

from himalaya_mcp import cli
from himalaya_mcp.validation import validate_account, validate_folder_name


async def folder_list(account: str | None = None) -> str:
    """List all folders/mailboxes for an email account.

    Args:
        account: Account name. If omitted, uses the default account.
    """
    account = validate_account(account)
    result = cli.run("folder", "list", account=account)
    return json.dumps(result, indent=2) if not isinstance(result, str) else result


async def folder_create(name: str, account: str | None = None) -> str:
    """Create a new folder/mailbox.

    Args:
        name: Name of the folder to create.
        account: Account name. If omitted, uses the default account.
    """
    name = validate_folder_name(name)
    account = validate_account(account)
    result = cli.run("folder", "create", name, account=account, output_json=False)
    return result or f"Folder '{name}' created."
