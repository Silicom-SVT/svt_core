"""
Unit tests for svt_runner.stats module.
Tests statistics recording and aggregation.
"""

import pytest
from svt_core.stats import Stats


class TestStats:
    """Test Statistics recording."""

    def test_stats_initial_state(self):
        """Test initial state of Stats object."""
        stats = Stats()
        assert stats.total_failed == 0
        assert stats.total_passed == 0
        assert stats.cycle_failed == 0
        assert stats.cycle_passed == 0

    def test_record_passed(self):
        """Test recording a passed test."""
        stats = Stats()
        stats.record(True)
        assert stats.cycle_passed == 1
        assert stats.cycle_failed == 0

    def test_record_failed(self):
        """Test recording a failed test."""
        stats = Stats()
        stats.record(False)
        assert stats.cycle_failed == 1
        assert stats.cycle_passed == 0

    def test_record_multiple(self):
        """Test recording multiple test results."""
        stats = Stats()
        stats.record(True)
        stats.record(True)
        stats.record(False)
        stats.record(True)
        
        assert stats.cycle_passed == 3
        assert stats.cycle_failed == 1

    def test_reset_cycle_with_failures(self):
        """Test cycle reset counts as failed cycle when there are failures."""
        stats = Stats()
        stats.record(True)
        stats.record(False)
        stats.finalize_cycle()
        
        assert stats.cycle_failed == 0
        assert stats.cycle_passed == 0
        assert stats.total_failed == 1
        assert stats.total_passed == 0

    def test_reset_cycle_with_all_passed(self):
        """Test cycle reset counts as passed cycle when all pass."""
        stats = Stats()
        stats.record(True)
        stats.record(True)
        stats.finalize_cycle()
        
        assert stats.cycle_failed == 0
        assert stats.cycle_passed == 0
        assert stats.total_failed == 0
        assert stats.total_passed == 1

    def test_reset_cycle_with_no_results(self):
        """Test cycle reset with no test results recorded."""
        stats = Stats()
        stats.finalize_cycle()
        
        # No failures, so defaults to passed
        assert stats.total_failed == 0
        assert stats.total_passed == 1

    def test_multiple_cycles(self):
        """Test tracking multiple cycles."""
        stats = Stats()
        
        # Cycle 1: All passed
        stats.record(True)
        stats.record(True)
        stats.finalize_cycle()
        
        # Cycle 2: One failure
        stats.record(True)
        stats.record(False)
        stats.finalize_cycle()
        
        # Cycle 3: All failed
        stats.record(False)
        stats.record(False)
        stats.finalize_cycle()
        
        assert stats.total_passed == 1
        assert stats.total_failed == 2
        assert stats.cycle_passed == 0
        assert stats.cycle_failed == 0

    def test_stats_accumulation(self):
        """Test that stats properly accumulate across cycles."""
        stats = Stats()
        
        for cycle in range(5):
            for i in range(10):
                stats.record(i % 3 != 0)  # 2 pass, 1 fail per cycle
            stats.finalize_cycle()
        
        # Each cycle has at least 1 failure, so all count as failed cycles
        assert stats.total_failed == 5
        assert stats.total_passed == 0

    def test_mixed_cycles_counter(self):
        """Test that total counters are correct when some cycles pass and some fail."""
        stats = Stats()

        # 3 passing cycles
        for _ in range(3):
            stats.record(True)
            stats.record(True)
            stats.finalize_cycle()

        # 2 failing cycles
        for _ in range(2):
            stats.record(True)
            stats.record(False)
            stats.finalize_cycle()

        assert stats.total_passed == 3
        assert stats.total_failed == 2
        # Cycle counters must be reset after finalize
        assert stats.cycle_passed == 0
        assert stats.cycle_failed == 0

    def test_last_cycle_counters_after_passing_cycle(self):
        """last_cycle_* should reflect the most recently finalized cycle (all passed)."""
        stats = Stats()

        stats.record(True)
        stats.record(True)
        stats.record(True)
        stats.finalize_cycle()

        assert stats.last_cycle_passed == 3
        assert stats.last_cycle_failed == 0

    def test_last_cycle_counters_after_failing_cycle(self):
        """last_cycle_* should reflect the most recently finalized cycle (some failed)."""
        stats = Stats()

        stats.record(True)
        stats.record(False)
        stats.record(False)
        stats.finalize_cycle()

        assert stats.last_cycle_passed == 1
        assert stats.last_cycle_failed == 2

    def test_last_cycle_counters_overwritten_each_cycle(self):
        """last_cycle_* must be overwritten on each finalize, not accumulated."""
        stats = Stats()

        # Cycle 1: 4 pass, 1 fail
        for _ in range(4):
            stats.record(True)
        stats.record(False)
        stats.finalize_cycle()

        # Cycle 2: 2 pass, 3 fail
        for _ in range(2):
            stats.record(True)
        for _ in range(3):
            stats.record(False)
        stats.finalize_cycle()

        assert stats.last_cycle_passed == 2
        assert stats.last_cycle_failed == 3

    def test_many_tests_per_cycle_counter(self):
        """Cycle-level pass/fail counters must track every individual test result."""
        stats = Stats()

        results = [True, False, True, True, False, False, True]
        for r in results:
            stats.record(r)

        expected_passed = results.count(True)   # 4
        expected_failed = results.count(False)  # 3
        assert stats.cycle_passed == expected_passed
        assert stats.cycle_failed == expected_failed

    def test_all_cycles_pass_total_failed_stays_zero(self):
        """total_failed must remain 0 when every cycle has zero failures."""
        stats = Stats()

        for _ in range(10):
            stats.record(True)
            stats.finalize_cycle()

        assert stats.total_failed == 0
        assert stats.total_passed == 10

    def test_all_cycles_fail_total_passed_stays_zero(self):
        """total_passed must remain 0 when every cycle has at least one failure."""
        stats = Stats()

        for _ in range(10):
            stats.record(False)
            stats.finalize_cycle()

        assert stats.total_passed == 0
        assert stats.total_failed == 10

    def test_single_failure_out_of_many_marks_cycle_failed(self):
        """Even one failure in a cycle of many passes must mark that cycle as failed."""
        stats = Stats()

        for _ in range(99):
            stats.record(True)
        stats.record(False)  # one bad test
        stats.finalize_cycle()

        assert stats.total_failed == 1
        assert stats.total_passed == 0

    def test_cycle_counters_do_not_bleed_between_cycles(self):
        """Records from a previous cycle must not affect the next cycle's counters."""
        stats = Stats()

        stats.record(True)
        stats.record(False)
        stats.finalize_cycle()

        # Second cycle starts fresh — no prior records visible
        assert stats.cycle_passed == 0
        assert stats.cycle_failed == 0

        stats.record(True)
        assert stats.cycle_passed == 1
        assert stats.cycle_failed == 0

    def test_total_cycles_invariant(self):
        """total_passed + total_failed must always equal the number of finalized cycles."""
        stats = Stats()
        n_cycles = 20

        for i in range(n_cycles):
            stats.record(i % 4 == 0)  # every 4th cycle has only a failure
            stats.finalize_cycle()

        assert stats.total_passed + stats.total_failed == n_cycles

    def test_last_cycle_initial_state(self):
        """last_cycle_passed and last_cycle_failed must both start at 0."""
        stats = Stats()
        assert stats.last_cycle_passed == 0
        assert stats.last_cycle_failed == 0

    def test_alternating_pass_fail_cycles(self):
        """Alternating cycles (pass, fail, pass, fail, pass) → 3 passed, 2 failed."""
        stats = Stats()

        for i in range(5):
            if i % 2 == 0:
                stats.record(True)   # even → passing cycle
            else:
                stats.record(False)  # odd → failing cycle
            stats.finalize_cycle()

        assert stats.total_passed == 3
        assert stats.total_failed == 2

    def test_multiple_consecutive_empty_cycles(self):
        """Finalizing with no records repeatedly must count each as a passed cycle."""
        stats = Stats()

        for _ in range(5):
            stats.finalize_cycle()

        assert stats.total_passed == 5
        assert stats.total_failed == 0

    def test_cycle_passed_plus_failed_equals_total_records(self):
        """cycle_passed + cycle_failed must equal the number of record() calls made."""
        stats = Stats()

        results = [True, False, True, False, False, True, True, False]
        for r in results:
            stats.record(r)

        assert stats.cycle_passed + stats.cycle_failed == len(results)

    def test_last_cycle_all_failed(self):
        """last_cycle_passed must be 0 and last_cycle_failed must equal records when all fail."""
        stats = Stats()

        for _ in range(5):
            stats.record(False)
        stats.finalize_cycle()

        assert stats.last_cycle_passed == 0
        assert stats.last_cycle_failed == 5

    def test_large_number_of_cycles(self):
        """Counters must remain accurate over a large number of cycles (100 pass, 100 fail)."""
        stats = Stats()

        for _ in range(100):
            stats.record(True)
            stats.finalize_cycle()

        for _ in range(100):
            stats.record(False)
            stats.finalize_cycle()

        assert stats.total_passed == 100
        assert stats.total_failed == 100
        assert stats.total_passed + stats.total_failed == 200
