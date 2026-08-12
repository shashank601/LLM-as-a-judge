"""
Pointwise evaluation entry point.

Usage:
    python run.py --suite suites/judge_suite.json
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
        default="suites/judge_suite.json",
        help="Path to the test suite JSON file.",
    )

    parser.add_argument(
        "--judge-model",
        default="llama-3.1-8b-instant",
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

    print("\nEvaluation Results")
    print("=" * 50)
    print(f"Total cases: {len(test_cases)}")
    print(f"Evaluated: {len(verdicts)}")
    print(f"Failed: {len(test_cases) - len(verdicts)}")

    print("\nCriteria Scores:")
    for criterion, score in report["criteria_scores"].items():
        print(f"  {criterion}: {score:.2f}")

    print(f"\nOverall Score: {report['overall_score']:.2f}")

    print(f"\nReport saved to {report_path}")
    print(f"Run log saved to {log_file}")


if __name__ == "__main__":
    main()

