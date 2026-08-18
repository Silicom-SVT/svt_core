"""
Structural Protocol for the Context object consumed by svt_modules.

This Protocol describes only the attributes that test-module functions
actually access. The concrete implementation lives in svt_framework
(svt.core.context.Context) and satisfies this Protocol automatically
via duck-typing — no explicit inheritance required.
"""

from __future__ import annotations

from typing import Any, Protocol


class _Logger(Protocol):
    def info(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...
    def passed(self, test_name: str) -> None: ...
    def failed(self, test_name: str, reason: str = "") -> None: ...


class _SSH(Protocol):
    def run(self, command: str, **kwargs: Any) -> str: ...


class _ExcelLog(Protocol):
    def add_value(self, title: str, index: int, value: str) -> None: ...


class Context(Protocol):
    """Structural interface for the test-execution context."""

    config: dict[str, Any]
    logger: _Logger
    ssh: _SSH
    excel_log: _ExcelLog
