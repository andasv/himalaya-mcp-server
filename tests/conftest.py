import subprocess
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_subprocess() -> Generator[MagicMock, None, None]:
    """Mock subprocess.run to simulate himalaya CLI calls."""
    with patch("himalaya_mcp.cli.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["himalaya"],
            returncode=0,
            stdout="",
            stderr="",
        )
        yield mock_run


@pytest.fixture
def mock_which() -> Generator[MagicMock, None, None]:
    """Mock shutil.which to simulate himalaya being found on PATH."""
    with patch("himalaya_mcp.cli.shutil.which", return_value="/usr/local/bin/himalaya") as mock:
        yield mock


def make_completed_process(
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
) -> subprocess.CompletedProcess[str]:
    """Helper to create a CompletedProcess for mocking."""
    return subprocess.CompletedProcess(
        args=["himalaya"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )
