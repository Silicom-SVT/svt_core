from pathlib import Path

from svt_core.logger import ExcelLog, Logger, LogLevel, PASS_LEVEL, FAIL_LEVEL


def test_logger_includes_thread_and_bound_context(tmp_path):
    logger = Logger.setup("dut-a", "ft", base_dir=str(tmp_path))
    logger.clear_context()  # Ensure clean state
    logger.bind_context(cycle=3, test_name="smoke")
    logger.info("hello")

    content = Path(logger.log_file).read_text(encoding="utf-8")
    assert "MainThread" in content
    assert "c=3" in content
    assert "t=smoke" in content
    logger.clear_context()  # Clean up


def test_logger_filename_includes_ambient_when_provided(tmp_path):
    logger = Logger.setup("dut-a", "ft", ambient=25, base_dir=str(tmp_path))
    assert Path(logger.log_file).name.startswith("dut-a_ft_amb25C_")


def test_excel_log_filename_matches_logger_convention(monkeypatch, tmp_path):
    class StubUUID:
        hex = "a1b2c3d4e5f6g7h8"

    monkeypatch.setattr("svt_core.logger.time.strftime", lambda _: "20260915-143022")
    monkeypatch.setattr("svt_core.logger.uuid4", lambda: StubUUID())

    excel_log = ExcelLog("device1", "stress_test", ambient=25, base_dir=str(tmp_path))

    assert (
        Path(excel_log.filename).name
        == "device1_stress_test_amb25C_20260915-143022_a1b2c3d4.xlsx"
    )
    assert excel_log.id == "device1_stress_test_amb25C_20260915-143022_a1b2c3d4"
    assert (
        Path(excel_log.filename).parent
        == tmp_path / "device1" / "stress_test_excel"
    )


def test_excel_log_filename_omits_ambient_when_not_provided(monkeypatch, tmp_path):
    class StubUUID:
        hex = "deadbeef12345678"

    monkeypatch.setattr("svt_core.logger.time.strftime", lambda _: "20260915-143022")
    monkeypatch.setattr("svt_core.logger.uuid4", lambda: StubUUID())

    excel_log = ExcelLog("device1", "stress_test", base_dir=str(tmp_path))

    assert (
        Path(excel_log.filename).name
        == "device1_stress_test_20260915-143022_deadbeef.xlsx"
    )


def test_logger_exception_includes_traceback(tmp_path):
    logger = Logger.setup("dut-b", "reg", base_dir=str(tmp_path))
    logger.clear_context()  # Ensure clean state

    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("division failure")

    content = Path(logger.log_file).read_text(encoding="utf-8")
    assert "division failure" in content
    assert "Traceback" in content
    assert "ZeroDivisionError" in content
    logger.clear_context()  # Clean up


def test_logger_rotates_file(tmp_path):
    logger = Logger.setup(
        "dut-c",
        "stab",
        base_dir=str(tmp_path),
        max_bytes=512,
        backup_count=2,
    )
    logger.clear_context()  # Ensure clean state

    for idx in range(120):
        logger.info(f"line-{idx}-" + ("x" * 40))

    log_path = Path(logger.log_file)
    rotated_files = list(log_path.parent.glob(log_path.name + ".*"))
    assert rotated_files
    logger.clear_context()  # Clean up


def test_log_level_filters_file_output(tmp_path):
    # Only WARNING and above should be written to the log file
    logger = Logger.setup(
        "dut-d", "ft",
        base_dir=str(tmp_path),
        min_level=LogLevel.WARNING,
        print_level=LogLevel.WARNING,
    )
    logger.clear_context()

    logger.debug("should be hidden (debug)")
    logger.info("should be hidden (info)")
    logger.warning("should appear (warning)")
    logger.error("should appear (error)")

    content = Path(logger.log_file).read_text(encoding="utf-8")
    assert "should be hidden (debug)" not in content
    assert "should be hidden (info)" not in content
    assert "should appear (warning)" in content
    assert "should appear (error)" in content
    logger.clear_context()


def test_print_level_does_not_affect_file_output(tmp_path, capsys):
    # print_level=ERROR means console gets only ERROR+,
    # but the log file (min_level=DEBUG) still records everything
    logger = Logger.setup(
        "dut-e", "ft",
        base_dir=str(tmp_path),
        min_level=LogLevel.DEBUG,
        print_level=LogLevel.ERROR,
    )
    logger.clear_context()

    logger.debug("debug msg")
    logger.info("info msg")
    logger.warning("warning msg")
    logger.error("error msg")

    content = Path(logger.log_file).read_text(encoding="utf-8")
    # All levels written to file
    assert "debug msg" in content
    assert "info msg" in content
    assert "warning msg" in content
    assert "error msg" in content

    # Console should only show ERROR+
    captured = capsys.readouterr()
    assert "debug msg" not in captured.out
    assert "info msg" not in captured.out
    assert "warning msg" not in captured.out
    assert "error msg" in captured.out
    logger.clear_context()


# ---------------------------------------------------------------------------
# Custom log levels: PASS and FAIL
# ---------------------------------------------------------------------------

def test_pass_level_is_between_info_and_warning():
    import logging
    assert logging.INFO < PASS_LEVEL < logging.WARNING
    assert LogLevel.PASS.level == PASS_LEVEL
    assert LogLevel.PASS.display == "PASS"


def test_fail_level_is_between_warning_and_error():
    import logging
    assert logging.WARNING < FAIL_LEVEL < logging.ERROR
    assert LogLevel.FAIL.level == FAIL_LEVEL
    assert LogLevel.FAIL.display == "FAIL"


def test_passed_logs_at_pass_level(tmp_path):
    logger = Logger.setup("dut-f", "ft", base_dir=str(tmp_path))
    logger.clear_context()
    logger.passed("my_test")

    content = Path(logger.log_file).read_text(encoding="utf-8")
    assert "PAS" in content
    assert "[PASS] my_test" in content
    logger.clear_context()


def test_failed_logs_at_fail_level(tmp_path):
    logger = Logger.setup("dut-g", "ft", base_dir=str(tmp_path))
    logger.clear_context()
    logger.failed("my_test", "something broke")

    content = Path(logger.log_file).read_text(encoding="utf-8")
    assert "FAIL" in content
    assert "[FAIL] my_test -- something broke" in content
    logger.clear_context()


# ---------------------------------------------------------------------------
# Summary log file
# ---------------------------------------------------------------------------

def test_summary_log_file_is_created(tmp_path):
    logger = Logger.setup("dut-h", "ft", base_dir=str(tmp_path))
    assert logger.summary_log_file != ""
    assert Path(logger.summary_log_file).exists()
    assert "_summary.log" in Path(logger.summary_log_file).name


def test_summary_log_excludes_debug_and_info(tmp_path):
    logger = Logger.setup("dut-i", "ft", base_dir=str(tmp_path))
    logger.clear_context()

    logger.debug("debug msg")
    logger.info("info msg")
    logger.passed("my_test")
    logger.warning("warning msg")
    logger.failed("my_test")

    summary = Path(logger.summary_log_file).read_text(encoding="utf-8")
    assert "debug msg" not in summary
    assert "info msg" not in summary
    assert "[PASS] my_test" in summary
    assert "warning msg" in summary
    assert "[FAIL] my_test" in summary
    logger.clear_context()


def test_summary_log_level_can_be_overridden(tmp_path):
    logger = Logger.setup(
        "dut-j", "ft",
        base_dir=str(tmp_path),
        summary_level=LogLevel.WARNING,
    )
    logger.clear_context()

    logger.passed("my_test")   # level 25, below WARNING (30)
    logger.warning("warn msg")

    summary = Path(logger.summary_log_file).read_text(encoding="utf-8")
    assert "[PASS] my_test" not in summary
    assert "warn msg" in summary
    logger.clear_context()


def test_full_log_still_contains_all_levels(tmp_path):
    logger = Logger.setup("dut-k", "ft", base_dir=str(tmp_path))
    logger.clear_context()

    logger.debug("debug msg")
    logger.info("info msg")
    logger.passed("my_test")

    content = Path(logger.log_file).read_text(encoding="utf-8")
    assert "debug msg" in content
    assert "info msg" in content
    assert "[PASS] my_test" in content
    logger.clear_context()


# ---------------------------------------------------------------------------
# Compact mode: print_level=PASS (level 25) filters console output
# ---------------------------------------------------------------------------

def test_compact_mode_suppresses_debug_and_info_on_console(tmp_path, capsys):
    logger = Logger.setup(
        "dut-l", "ft",
        base_dir=str(tmp_path),
        print_level=LogLevel.PASS,
    )
    logger.clear_context()

    logger.debug("debug hidden")
    logger.info("info hidden")
    logger.passed("should appear")
    logger.warning("warning appears")

    captured = capsys.readouterr()
    assert "debug hidden" not in captured.out
    assert "info hidden" not in captured.out
    assert "[PASS] should appear" in captured.out
    assert "warning appears" in captured.out
    logger.clear_context()


def test_compact_mode_shows_fail_and_error_on_console(tmp_path, capsys):
    logger = Logger.setup(
        "dut-m", "ft",
        base_dir=str(tmp_path),
        print_level=LogLevel.PASS,
    )
    logger.clear_context()

    logger.info("info hidden")
    logger.failed("my_test", "broke")
    logger.error("error appears")
    logger.critical("critical appears")

    captured = capsys.readouterr()
    assert "info hidden" not in captured.out
    assert "[FAIL] my_test -- broke" in captured.out
    assert "error appears" in captured.out
    assert "critical appears" in captured.out
    logger.clear_context()


def test_compact_mode_does_not_affect_file_log(tmp_path, capsys):
    logger = Logger.setup(
        "dut-n", "ft",
        base_dir=str(tmp_path),
        print_level=LogLevel.PASS,
    )
    logger.clear_context()

    logger.debug("debug in file")
    logger.info("info in file")
    logger.passed("pass in file")

    content = Path(logger.log_file).read_text(encoding="utf-8")
    assert "debug in file" in content
    assert "info in file" in content
    assert "[PASS] pass in file" in content

    captured = capsys.readouterr()
    assert "debug in file" not in captured.out
    assert "info in file" not in captured.out
    logger.clear_context()
