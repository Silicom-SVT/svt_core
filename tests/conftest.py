"""
Pytest configuration and shared fixtures for SVT testing framework tests.
Provides mock Context objects and other utilities for unit testing.
"""

import pytest
from unittest.mock import MagicMock, Mock
from svt_core.stats import Stats


@pytest.fixture
def mock_logger():
    """Create a mock logger that tracks calls."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    logger.critical = MagicMock()
    logger.debug = MagicMock()
    logger.exception = MagicMock()
    logger.bind_context = MagicMock()
    logger.clear_context = MagicMock()
    return logger


@pytest.fixture
def mock_ssh():
    """Create a mock SSH client."""
    ssh = MagicMock()
    ssh.run = MagicMock(return_value="")
    ssh.file_exists = MagicMock(return_value=True)
    ssh.execute = MagicMock(return_value="")
    return ssh


@pytest.fixture
def mock_excel_log():
    """Create a mock Excel logger."""
    excel = MagicMock()
    excel.add_value = MagicMock()
    excel.save = MagicMock()
    return excel


@pytest.fixture
def mock_stats():
    """Create a real Stats object for testing."""
    return Stats()


@pytest.fixture
def mock_context(mock_logger, mock_ssh, mock_excel_log, mock_stats):
    """Create a fully mocked Context object."""
    context = MagicMock()
    context.logger = mock_logger
    context.ssh = mock_ssh
    context.excel_log = mock_excel_log
    context.stats = mock_stats
    context.credentials = ("192.168.1.1", "root", "password")
    
    # Default mock config
    context.config = {
        "general": {
            "dut": "test_device",
            "ip": "192.168.1.1",
            "username": "root",
            "password": "password",
            "ambient": 25,
            "name": "test",
            "usr": "test_user",
        },
        "_type": "ft",
        "_need_power_cycle": True,
        "power": {
            "type": "eboot",
            "ip": "192.168.1.100",
            "ports": [1, 2],
        },
    }
    return context


@pytest.fixture
def sample_ddr_config():
    """Sample DDR test configuration."""
    return {
        "general": {
            "dut": "ddr_test_device",
            "ip": "192.168.1.1",
            "username": "root",
            "password": "password",
            "ambient": 25,
            "name": "ddr_test",
            "usr": "test_user",
        },
        "_type": "reg",
        "_need_power_cycle": False,
        "vars": {
            "ddr_speed": 3200,
            "ddr_speed_slots": 4,
            "ddr_dimm_size": 16,
            "ddr_dimm_size_slots": 4,
            "ddr_vendor": "samsung",
            "stress_timeout": 120,
        },
    }
