import json

from himalaya_mcp import cli
from himalaya_mcp.validation import validate_account


async def account_list(account: str | None = None) -> str:
    """List all configured email accounts.

    Returns a list of accounts with their name, backend type, and default status.

    Args:
        account: Optional specific account name to query.
    """
    account = validate_account(account)
    result = cli.run("account", "list", account=account)
    return json.dumps(result, indent=2) if not isinstance(result, str) else result
