#!/usr/bin/env python3
"""Quick stress test on existing test fixtures to establish baseline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from stress_test import StressTestRunner

def main():
    """Run stress test on test fixtures."""
    base_dir = Path(__file__).parent.parent / "tests"
    runner = StressTestRunner(base_dir)
    runner.base_dir = base_dir  # Override to search tests dir

    report = runner.run()

    print(f"\n{'='*80}")
    print("TEST FIXTURES STRESS TEST")
    print(f"{'='*80}")
    print(f"Success Rate: {report['summary']['success_rate']}")
    print(f"{'='*80}\n")

    return 0 if report['summary']['failed'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
