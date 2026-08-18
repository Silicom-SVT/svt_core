"""
Unit tests for svt_runner.config module.
Tests config loading, validation, and merging.
"""

import pytest
import tempfile
from pathlib import Path
import tomllib

from svt_core.config import load_config


class TestLoadConfig:
    """Test config loading functionality."""

    def test_load_config_success(self):
        """Test successful config file loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.toml"
            config_path.write_text("""
[general]
dut = "test_device"
ip = "192.168.1.1"
username = "root"
password = "password"

[tests]
names = ["test1", "test2"]
            """)
            
            config = load_config(
                config_path,
                test_type="ft",
                ambient=25,
                need_power_cycle=True
            )
            
            assert config["general"]["dut"] == "test_device"
            assert config["_type"] == "ft"
            assert config["_need_power_cycle"] is True
            assert config["general"]["ambient"] == 25

    def test_load_config_file_not_found(self):
        """Test error handling when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_config(
                "/nonexistent/path/config.toml",
                ambient=25
            )

    def test_load_config_ambient_required(self):
        """Test that ambient temperature is required."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.toml"
            config_path.write_text("[general]\ndut = 'test'")
            
            with pytest.raises(ValueError, match="ambient is required"):
                load_config(config_path, ambient=None)

    def test_load_config_test_type_override(self):
        """Test that test_type is properly set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.toml"
            config_path.write_text("[general]\ndut = 'test'")
            
            for test_type in ["ft", "reg", "stab", "update"]:
                config = load_config(config_path, test_type=test_type, ambient=25)
                assert config["_type"] == test_type

    def test_load_config_power_cycle_flag(self):
        """Test power cycle flag configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.toml"
            config_path.write_text("[general]\ndut = 'test'")
            
            config_with_cycle = load_config(
                config_path, 
                ambient=25, 
                need_power_cycle=True
            )
            assert config_with_cycle["_need_power_cycle"] is True
            
            config_without_cycle = load_config(
                config_path, 
                ambient=25, 
                need_power_cycle=False
            )
            assert config_without_cycle["_need_power_cycle"] is False

    def test_load_config_general_section_created_if_missing(self):
        """Test that general section is created if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.toml"
            config_path.write_text("[tests]\nnames = []")
            
            config = load_config(config_path, ambient=25)
            assert "general" in config
            assert config["general"]["ambient"] == 25

    def test_load_config_nested_values_preserved(self):
        """Test that nested config values are preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.toml"
            config_path.write_text("""
[general]
dut = "device"

[power]
ip = "192.168.1.100"
ports = [1, 2, 3]

[vars]
timeout = 120
retry_count = 3
            """)
            
            config = load_config(config_path, ambient=25)
            assert config["power"]["ip"] == "192.168.1.100"
            assert config["power"]["ports"] == [1, 2, 3]
            assert config["vars"]["timeout"] == 120

    def test_cli_overrides_take_precedence(self):
        """Test that CLI override kwargs overwrite values from the TOML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.toml"
            config_path.write_text("""
[general]
dut = "device"
ip = "192.168.1.1"
username = "root"
password = "pass"

[stab]
timeout = 3600
intervals = 30
main_tests = []
background_tests = []

[reg]
power_cycles = 100
reboots = 100
            """)

            config = load_config(
                config_path,
                ambient=25,
                timeout=600,
                intervals=10,
                power_cycles=5,
                reboots=3,
            )
            assert config["stab"]["timeout"] == 600
            assert config["stab"]["intervals"] == 10
            assert config["reg"]["power_cycles"] == 5
            assert config["reg"]["reboots"] == 3

    def test_cli_overrides_create_sections_if_missing(self):
        """Test that CLI overrides create config sections if they don't exist in TOML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.toml"
            config_path.write_text("""
[general]
dut = "device"
            """)

            config = load_config(
                config_path,
                ambient=25,
                timeout=120,
                power_cycles=10,
            )
            assert config["stab"]["timeout"] == 120
            assert config["reg"]["power_cycles"] == 10

    def test_cli_overrides_ignored_when_none(self):
        """Test that None override values don't overwrite TOML config values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.toml"
            config_path.write_text("""
[general]
dut = "device"

[stab]
timeout = 7200
intervals = 60
main_tests = []
background_tests = []
            """)

            config = load_config(config_path, ambient=25)
            assert config["stab"]["timeout"] == 7200
            assert config["stab"]["intervals"] == 60
