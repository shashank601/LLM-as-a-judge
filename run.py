"""
Pointwise evaluation entry point.

Usage:
    python run.py --suite suites/test_suite.json
"""

import argparse
import json
from pathlib import Path

from core.pipeline import evaluate_case, load_suite
from core.schemas import TestCase
from core.logger import init_logger
from core.aggregate import aggregate


def main():
    parser = argparse.ArgumentParser(
        description="Run pointwise LLM evaluation."
    )

    parser.add_argument(
        "--suite",
        default="suites/test_suite.json",
        help="Path to the test suite JSON file.",
    )

    parser.add_argument(
        "--judge-model",
        default="openai/gpt-oss-20b",
        help="Model used as the judge.",
    )

    args = parser.parse_args()

    # ---------------------------------------------------------
    # Create directories
    # ---------------------------------------------------------

    Path("logs").mkdir(exist_ok=True)
    Path("reports").mkdir(exist_ok=True)

    # ---------------------------------------------------------
    # Initialize logger
    # ---------------------------------------------------------

    run_id, log_file = init_logger(
        judge_model=args.judge_model,
    )

    # ---------------------------------------------------------
    # Load test suite
    # ---------------------------------------------------------

    test_cases = load_suite(args.suite)

    # ---------------------------------------------------------
    # Evaluate every case
    # ---------------------------------------------------------

    verdicts = []

    for case in test_cases:

        verdict = evaluate_case(
            case=case,
            mode="pointwise",
            judge_model=args.judge_model,
            log_file=log_file,
        )

        if verdict is not None:
            verdicts.append(verdict)

    # ---------------------------------------------------------
    # Aggregate results
    # ---------------------------------------------------------

    report = aggregate(verdicts)
    report["run_id"] = run_id
    report["judge_model"] = args.judge_model

    # ---------------------------------------------------------
    # Write report
    # ---------------------------------------------------------

    report_path = Path("reports") / f"report_{run_id}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Report saved to {report_path}")
    print(f"Run log saved to {log_file}")
    print(f"Total cases: {len(test_cases)}")
    print(f"Evaluated: {len(verdicts)}")


if __name__ == "__main__":
    main()

