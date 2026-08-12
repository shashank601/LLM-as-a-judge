"""
Phase 2 entry point: compare two prompt configurations.

Config A = Prompt 1
Config B = Prompt 2

For every test case:
1. Judge Prompt 1 vs Prompt 2.
2. Swap their positions and judge again.
3. Convert positional winners back to the actual prompt.
4. Detect preference flips / position bias.
5. Aggregate wins, losses, ties, and win rates.
6. Declare a winner.

Usage:
    python compare.py --suite suites/test_suite.json
"""

import argparse
import json

from core.pipeline import load_suite
from core.judge import judge_case


# ---------------------------------------------------------------------------
# Convert the judge's positional winner into the actual configuration winner.
# ---------------------------------------------------------------------------

def actual_winner(winner: str | None, swapped: bool) -> str | None:
    """
    Convert A/B from the judge's perspective into Prompt 1 / Prompt 2.

    Normal:
        A = Prompt 1
        B = Prompt 2

    Swapped:
        A = Prompt 2
        B = Prompt 1
    """

    if winner is None:
        return None

    if winner == "tie":
        return "tie"

    if not swapped:
        # Normal order.
        return "prompt_1" if winner == "A" else "prompt_2"

    # Swapped order.
    return "prompt_2" if winner == "A" else "prompt_1"


# ---------------------------------------------------------------------------
# Compare one test case.
# ---------------------------------------------------------------------------

def compare_case(case):
    """
    Judge Prompt 1 vs Prompt 2 twice:

        normal:
            A = Prompt 1
            B = Prompt 2

        swapped:
            A = Prompt 2
            B = Prompt 1
    """

    normal = judge_case(
        case,
        mode="pairwise",
        swap=False,
    )

    swapped = judge_case(
        case,
        mode="pairwise",
        swap=True,
    )

    # If either judgment failed, we cannot reliably compare this case.
    if normal is None or swapped is None:
        return None

    normal_actual = actual_winner(
        normal.winner,
        swapped=False,
    )

    swapped_actual = actual_winner(
        swapped.winner,
        swapped=True,
    )

    # A flip means the actual preferred configuration changed
    # between the two judging orders.
    flipped = (
        normal_actual != "tie"
        and swapped_actual != "tie"
        and normal_actual != swapped_actual
    )

    return {
        "case_id": case.id,
        "normal_winner": normal.winner,
        "swapped_winner": swapped.winner,
        "normal_actual_winner": normal_actual,
        "swapped_actual_winner": swapped_actual,
        "flipped": flipped,
    }


# ---------------------------------------------------------------------------
# Aggregate all test cases.
# ---------------------------------------------------------------------------

def compare_suite(cases):
    results = []

    prompt_1_wins = 0
    prompt_2_wins = 0
    ties = 0
    flips = 0
    failed = 0

    for case in cases:
        result = compare_case(case)

        if result is None:
            failed += 1
            continue

        results.append(result)

        # Use the normal/swapped results to determine the actual
        # configuration preference.
        #
        # If both orders agree, count that winner.
        # If they disagree, treat it as a position-sensitive case.
        normal_winner = result["normal_actual_winner"]
        swapped_winner = result["swapped_actual_winner"]

        if result["flipped"]:
            flips += 1
            continue

        # Both orders agree.
        if normal_winner == "prompt_1":
            prompt_1_wins += 1

        elif normal_winner == "prompt_2":
            prompt_2_wins += 1

        else:
            ties += 1

    total_evaluated = len(results)

    decisive_cases = prompt_1_wins + prompt_2_wins

    prompt_1_win_rate = (
        prompt_1_wins / decisive_cases
        if decisive_cases
        else 0.0
    )

    prompt_2_win_rate = (
        prompt_2_wins / decisive_cases
        if decisive_cases
        else 0.0
    )

    flip_rate = (
        flips / total_evaluated
        if total_evaluated
        else 0.0
    )

    # Declare winner based on consistent non-tied comparisons.
    if prompt_1_wins > prompt_2_wins:
        declared_winner = "Prompt 1"

    elif prompt_2_wins > prompt_1_wins:
        declared_winner = "Prompt 2"

    else:
        declared_winner = "tie"

    return {
        "config_a": "Prompt 1",
        "config_b": "Prompt 2",

        "total_cases": len(cases),
        "evaluated_cases": total_evaluated,
        "failed_cases": failed,

        "prompt_1_wins": prompt_1_wins,
        "prompt_2_wins": prompt_2_wins,
        "ties": ties,

        "prompt_1_win_rate": prompt_1_win_rate,
        "prompt_2_win_rate": prompt_2_win_rate,

        "flip_count": flips,
        "flip_rate": flip_rate,

        "declared_winner": declared_winner,

        "cases": results,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Compare Prompt 1 against Prompt 2."
    )

    parser.add_argument(
        "--suite",
        default="suites/test_suite.json",
        help="Path to the test suite.",
    )

    args = parser.parse_args()

    cases = load_suite(args.suite)

    report = compare_suite(cases)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()