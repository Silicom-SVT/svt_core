from __future__ import annotations

from pathlib import Path
from typing import Any
import tomllib


def load_config(
    config_path: str | Path,
    *,
    test_type: str = "ft",
    ambient: int | None = None,
    need_power_cycle: bool = True,
    stop_if_fail: bool = False,
    timeout: int | None = None,
    intervals: int | None = None,
    power_cycles: int | None = None,
    reboots: int | None = None,
) -> dict[str, Any]:
    config_path = Path(config_path)
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("rb") as f:
        config = tomllib.load(f)

    # add type to the config dict
    config["_type"] = test_type

    # infer project directory from config path (parent of configs/ or the config file's dir)
    config_dir = config_path.resolve().parent
    project_dir = config_dir.parent if config_dir.name == "configs" else config_dir
    config["_project_dir"] = str(project_dir)

    if ambient is None:
        raise ValueError("--ambient is required")

    config["_need_power_cycle"] = need_power_cycle
    config["_stop_if_fail"] = stop_if_fail

    config.setdefault("general", {})
    config["general"]["ambient"] = ambient

    if timeout is not None:
        config.setdefault("stab", {})["timeout"] = timeout
    if intervals is not None:
        config.setdefault("stab", {})["intervals"] = intervals
    if power_cycles is not None:
        config.setdefault("reg", {})["power_cycles"] = power_cycles
    if reboots is not None:
        config.setdefault("reg", {})["reboots"] = reboots

    return config
