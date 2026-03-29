import json
import logging
import shutil
import subprocess
import time
from typing import Any

logger = logging.getLogger("himalaya_mcp")


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

    cmd.extend(args)

    if account:
        cmd.extend(["--account", account])
    if folder:
        cmd.extend(["--folder", folder])

    cmd_str = " ".join(args)
    logger.info("[run] starting: %s", cmd_str)
    start = time.monotonic()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - start
        logger.error("[run] TIMEOUT after %.1fs: %s", elapsed, cmd_str)
        raise HimalayaError(f"Command timed out: {cmd_str}") from exc
    except OSError as exc:
        logger.error("[run] OS error: %s — %s", cmd_str, exc)
        raise HimalayaError(f"Failed to execute himalaya: {exc}") from exc

    elapsed = time.monotonic() - start
    logger.info("[run] finished in %.1fs (rc=%d): %s", elapsed, result.returncode, cmd_str)

    if result.returncode != 0:
        stderr = result.stderr.strip()
        logger.error("[run] stderr: %s", stderr[:500])
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

    cmd_str = " ".join(args)
    stdin_preview = f" (stdin: {len(stdin_data)} bytes)" if stdin_data else ""
    logger.info("[run_raw] starting: %s%s (timeout=%ds)", cmd_str, stdin_preview, timeout)
    start = time.monotonic()

    try:
        result = subprocess.run(
            cmd,
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - start
        logger.error("[run_raw] TIMEOUT after %.1fs: %s", elapsed, cmd_str)
        raise HimalayaError(f"Command timed out: {cmd_str}") from exc
    except OSError as exc:
        logger.error("[run_raw] OS error: %s — %s", cmd_str, exc)
        raise HimalayaError(f"Failed to execute himalaya: {exc}") from exc

    elapsed = time.monotonic() - start
    logger.info("[run_raw] finished in %.1fs (rc=%d): %s", elapsed, result.returncode, cmd_str)

    if result.returncode != 0:
        stderr = result.stderr.strip()
        logger.error("[run_raw] stderr: %s", stderr[:500])
        raise HimalayaError(f"himalaya error: {stderr}")

    return result.stdout.strip()
