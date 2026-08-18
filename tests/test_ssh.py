import os
from unittest.mock import MagicMock, patch

import pytest

from svt_core.ssh import SSHClient

# ---------------------------------------------------------------------------
# Helpers shared by integration tests
# ---------------------------------------------------------------------------

REAL_HOST = "192.168.2.200"
REAL_USER = "root"


def real_client(mock_logger):
    password = os.environ.get("SVT_SSH_PASS", "")
    return SSHClient(logger=mock_logger, host=REAL_HOST, username=REAL_USER, password=password)


def make_client(mock_logger):
    return SSHClient(
        logger=mock_logger,
        host="192.168.1.1",
        username="user",
        password="pass",
    )


def mock_exec(output: str = "some output", exit_code: int = 0):
    """Build a paramiko exec_command mock that returns the given output and exit code."""
    stdout = MagicMock()
    stdout.read.return_value = output.encode()
    stdout.channel.recv_exit_status.return_value = exit_code

    stderr = MagicMock()
    stderr.read.return_value = b""

    stdin = MagicMock()
    return stdin, stdout, stderr


@patch("svt_core.ssh.paramiko.SSHClient")
def test_to_log_true_logs_output(mock_paramiko_cls, mock_logger):
    mock_conn = MagicMock()
    mock_paramiko_cls.return_value = mock_conn
    mock_conn.exec_command.return_value = mock_exec("hello world")

    client = make_client(mock_logger)
    client.run("echo hello", to_log=True)

    logged_messages = [call.args[0] for call in mock_logger.info.call_args_list]
    assert any("hello world" in msg for msg in logged_messages)


@patch("svt_core.ssh.paramiko.SSHClient")
def test_to_log_false_does_not_log_output(mock_paramiko_cls, mock_logger):
    mock_conn = MagicMock()
    mock_paramiko_cls.return_value = mock_conn
    mock_conn.exec_command.return_value = mock_exec("secret output")

    client = make_client(mock_logger)
    client.run("echo secret", to_log=False)

    logged_messages = [call.args[0] for call in mock_logger.info.call_args_list]
    assert not any("secret output" in msg for msg in logged_messages)


@patch("svt_core.ssh.paramiko.SSHClient")
def test_to_log_false_still_returns_output(mock_paramiko_cls, mock_logger):
    mock_conn = MagicMock()
    mock_paramiko_cls.return_value = mock_conn
    mock_conn.exec_command.return_value = mock_exec("the value")

    client = make_client(mock_logger)
    result = client.run("cat /proc/something", to_log=False)

    assert result == "the value"


# ---------------------------------------------------------------------------
# Integration tests — require a live device at REAL_HOST
# ---------------------------------------------------------------------------

pytestmark_integration = pytest.mark.skipif(
    not os.environ.get("SVT_SSH_PASS"),
    reason="SVT_SSH_PASS not set — skipping integration tests",
)


@pytestmark_integration
def test_integration_to_log_true_logs_output(mock_logger, tmp_path):
    client = real_client(mock_logger)
    client.run("echo integration_hello", to_log=True)

    logged_messages = [call.args[0] for call in mock_logger.info.call_args_list]
    assert any("integration_hello" in msg for msg in logged_messages)


@pytestmark_integration
def test_integration_to_log_false_does_not_log_output(mock_logger):
    client = real_client(mock_logger)
    client.run("echo silent_output", to_log=False)

    logged_messages = [call.args[0] for call in mock_logger.info.call_args_list]
    assert not any("silent_output" in msg for msg in logged_messages)


@pytestmark_integration
def test_integration_to_log_false_still_returns_output(mock_logger):
    client = real_client(mock_logger)
    result = client.run("echo returned_value", to_log=False)

    assert "returned_value" in result
