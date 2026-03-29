import json
import shutil
import subprocess
from typing import Any


class HimalayaError(Exception):
    pass


def _find_binary() -> str:
    path = shutil.which("himalaya")
    if path is None:
        raise HimalayaError(
            "himalaya CLI not found on PATH. Install it from https://github.com/pimalaya/himalaya"
        )
    return path


def run(
    *args: str,
    account: str | None = None,
    folder: str | None = None,
    output_json: bool = True,
) -> Any:
    """Run a himalaya CLI command and return the result.

    Args:
        *args: Command and subcommand arguments (e.g., "account", "list").
        account: Optional account name to use (--account).
        folder: Optional folder name to use (--folder).
        output_json: If True, pass --output json and parse the result.

    Returns:
        Parsed JSON (dict or list) if output_json is True, otherwise raw stdout string.

    Raises:
        HimalayaError: If the command fails.
    """
    binary = _find_binary()
    cmd: list[str] = [binary]

    if output_json:
        cmd.extend(["--output", "json"])
    if account:
        cmd.extend(["--account", account])
    if folder:
        cmd.extend(["--folder", folder])

    cmd.extend(args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired as exc:
        raise HimalayaError(f"Command timed out: {' '.join(args)}") from exc
    except OSError as exc:
        raise HimalayaError(f"Failed to execute himalaya: {exc}") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise HimalayaError(f"himalaya error: {stderr}")

    stdout = result.stdout.strip()

    if output_json and stdout:
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise HimalayaError(f"Failed to parse himalaya JSON output: {stdout[:200]}") from exc

    return stdout


def run_raw(*args: str, stdin_data: str | None = None, timeout: int = 30) -> str:
    """Run a himalaya command with raw input/output (for template send, message send, etc.).

    Args:
        *args: Full command arguments.
        stdin_data: Optional data to pass via stdin.
        timeout: Command timeout in seconds.

    Returns:
        Raw stdout string.

    Raises:
        HimalayaError: If the command fails.
    """
    binary = _find_binary()
    cmd = [binary, *args]

    try:
        result = subprocess.run(
            cmd,
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise HimalayaError(f"Command timed out: {' '.join(args)}") from exc
    except OSError as exc:
        raise HimalayaError(f"Failed to execute himalaya: {exc}") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise HimalayaError(f"himalaya error: {stderr}")

    return result.stdout.strip()
