"""
Pointwise evaluation entry point.

Usage:
    python run.py --suite suites/test_suite.json
"""

import argparse
import json

from core.pipeline import evaluate_case
from core.schemas import TestCase


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
        help="Groq model used as the judge.",
    )

    args = parser.parse_args()

    # ---------------------------------------------------------
    # Load test suite
    # ---------------------------------------------------------

    with open(args.suite, "r", encoding="utf-8") as f:
        data = json.load(f)

    test_cases = [
        TestCase(**case)
        for case in data
    ]

    # ---------------------------------------------------------
    # Evaluate every case
    # ---------------------------------------------------------

    verdicts = []

    for case in test_cases:

        verdict = evaluate_case(
            case=case,
            mode="pointwise",
            judge_model=args.judge_model,
        )

        if verdict is not None:
            verdicts.append(verdict)

    # ---------------------------------------------------------
    # Print results
    # ---------------------------------------------------------

    print(
        json.dumps(
            [verdict.model_dump() for verdict in verdicts],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

