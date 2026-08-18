from dataclasses import dataclass


@dataclass
class Stats:
    total_failed: int = 0
    total_passed: int = 0
    cycle_failed: int = 0
    cycle_passed: int = 0
    last_cycle_failed: int = 0
    last_cycle_passed: int = 0

    def finalize_cycle(self) -> None:
        """Tally the current cycle result into totals, then reset cycle counters."""
        self.last_cycle_passed = self.cycle_passed
        self.last_cycle_failed = self.cycle_failed
        if self.cycle_failed > 0:
            self.total_failed += 1
        else:
            self.total_passed += 1
        self.cycle_failed = 0
        self.cycle_passed = 0

    def record(self, passed: bool) -> None:
        if passed:
            self.cycle_passed += 1
        else:
            self.cycle_failed += 1
