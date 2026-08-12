"""
Offline replay CLI for saved judge responses.

Replay reads saved raw judge responses and reconstructs Verdict objects
without making any API calls.
"""

import argparse
import json

from core.replay import replay_run
from core.aggregate import aggregate


def main():
    parser = argparse.ArgumentParser(
        description="Replay a saved run log offline (no API calls)."
    )

    parser.add_argument(
        "--log",
        required=True,
        help="Path to the run log JSON file.",
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to save the aggregated report.",
    )

    args = parser.parse_args()

    # Replay the run
    verdicts, errors = replay_run(args.log)

    print(f"Replayed {len(verdicts)} verdicts successfully")

    if errors:
        print(f"Failed to replay {len(errors)} cases:")
        for error in errors:
            print(f"  - {error['case_id']}: {error['error']}")

    # Aggregate results
    report = aggregate(verdicts)
    report["run_log"] = args.log
    report["replayed_cases"] = len(verdicts)
    report["failed_cases"] = len(errors)

    print("\nAggregated Results:")
    print(f"Total cases: {report['total_cases']}")
    print(f"Criteria scores: {report['criteria_scores']}")
    print(f"Overall score: {report['overall_score']}")

    # Save report if requested
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to {args.output}")


if __name__ == "__main__":
    main()
