"""
Validate the LLM judge against human-labelled gold test cases.

Pointwise:
    GoldTestCase
        ↓
    TestCase
        ↓
    judge_case(mode="pointwise")
        ↓
    Verdict
        ↓
    compare against human scores
        ↓
    validation report

Pairwise:
    GoldTestCase
        ↓
    TestCase
        ↓
    judge_case(mode="pairwise")
        ↓
    Verdict
        ↓
    compare winner against human winner
        ↓
    validation report

Usage:

    python validate.py --suite suites/gold_pointwise.json --mode pointwise

    python validate.py --suite suites/gold_pairwise.json --mode pairwise
"""

import argparse
import json

from core.schemas import TestCase, GoldTestCase
from core.judge import judge_case


# ============================================================================
# GOLD -> TEST CASE
# ============================================================================

def gold_to_testcase(gold: GoldTestCase) -> TestCase:
    """
    Convert a GoldTestCase into the normal TestCase used by judge_case().

    Human labels are deliberately NOT passed to the judge.
    """

    return TestCase(
        id=gold.id,
        input=gold.input,
        system_prompt=gold.system_prompt,
        model_output=gold.model_output,
        model_output_b=gold.model_output_b,
        criteria=gold.criteria,
    )


# ============================================================================
# VALIDATE SINGLE CASE
# ============================================================================

def validate_case(
    gold: GoldTestCase,
    mode: str,
    judge_model: str = "openai/gpt-oss-20b",
):
    """
    Run the existing LLM judge on one gold testcase and compare
    its verdict against human labels.
    """

    # ------------------------------------------------------------
    # Validate mode
    # ------------------------------------------------------------

    if mode not in {"pointwise", "pairwise"}:
        raise ValueError(
            f"Invalid validation mode: {mode}. "
            "Expected 'pointwise' or 'pairwise'."
        )

    # ------------------------------------------------------------
    # Validate gold testcase requirements
    # ------------------------------------------------------------

    if mode == "pairwise":
        if gold.model_output_b is None:
            raise ValueError(
                f"{gold.id}: pairwise gold case requires model_output_b."
            )

        if gold.human_winner is None:
            raise ValueError(
                f"{gold.id}: pairwise gold case requires human_winner."
            )

    # ------------------------------------------------------------
    # Convert GoldTestCase -> normal TestCase
    # ------------------------------------------------------------

    case = gold_to_testcase(gold)

    # ------------------------------------------------------------
    # Call existing judge
    # ------------------------------------------------------------

    verdict = judge_case(
        case=case,
        mode=mode,
        model=judge_model,
    )

    # ------------------------------------------------------------
    # Judge failure
    # ------------------------------------------------------------

    if verdict is None:
        return {
            "case_id": gold.id,
            "status": "judge_failed",
            "mode": mode,
        }

    # ------------------------------------------------------------
    # Base result
    # ------------------------------------------------------------

    result = {
        "case_id": gold.id,
        "status": "success",
        "mode": mode,
    }

    # ========================================================================
    # POINTWISE VALIDATION
    # ========================================================================

    if mode == "pointwise":

        # ------------------------------------------------------------
        # Criterion agreement
        # ------------------------------------------------------------

        if gold.human_scores is not None:

            judge_scores = {
                criterion.name: criterion.score
                for criterion in verdict.criteria
            }

            criterion_agreement = {}

            for criterion, human_score in gold.human_scores.items():

                if criterion not in judge_scores:

                    criterion_agreement[criterion] = {
                        "human_score": human_score,
                        "judge_score": None,
                        "agreement": False,
                        "error": "Judge omitted criterion",
                    }

                    continue

                judge_score = judge_scores[criterion]

                criterion_agreement[criterion] = {
                    "human_score": human_score,
                    "judge_score": judge_score,
                    "agreement": human_score == judge_score,
                }

            result["criterion_agreement"] = criterion_agreement

        # ------------------------------------------------------------
        # Overall score agreement
        # ------------------------------------------------------------

        if gold.human_overall_score is not None:

            judge_overall = verdict.overall_score

            if judge_overall is None:

                result["overall_agreement"] = {
                    "human_score": gold.human_overall_score,
                    "judge_score": None,
                    "agreement": False,
                    "error": "Judge did not return overall score",
                }

            else:

                result["overall_agreement"] = {
                    "human_score": gold.human_overall_score,
                    "judge_score": judge_overall,
                    "agreement": (
                        abs(
                            gold.human_overall_score
                            - judge_overall
                        )
                        <= 0.01
                    ),
                }

    # ========================================================================
    # PAIRWISE VALIDATION
    # ========================================================================

    elif mode == "pairwise":

        # ------------------------------------------------------------
        # Winner agreement
        # ------------------------------------------------------------

        result["winner_agreement"] = {
            "human_winner": gold.human_winner,
            "judge_winner": verdict.winner,
            "agreement": gold.human_winner == verdict.winner,
        }

    return result


# ============================================================================
# VALIDATE ENTIRE SUITE
# ============================================================================

def validate_suite(
    gold_cases: list[GoldTestCase],
    mode: str,
    judge_model: str = "openai/gpt-oss-20b",
):
    """
    Validate every gold testcase and aggregate agreement statistics.
    """

    if mode not in {"pointwise", "pairwise"}:
        raise ValueError(
            f"Invalid validation mode: {mode}. "
            "Expected 'pointwise' or 'pairwise'."
        )

    results = []

    # ------------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------------

    criterion_stats = {}

    overall_stats = {
        "total": 0,
        "agreement": 0,
    }

    winner_stats = {
        "total": 0,
        "agreement": 0,
    }

    judge_failures = 0

    # ------------------------------------------------------------------------
    # Validate cases
    # ------------------------------------------------------------------------

    for gold in gold_cases:

        result = validate_case(
            gold=gold,
            mode=mode,
            judge_model=judge_model,
        )

        results.append(result)

        # ------------------------------------------------------------
        # Judge failure
        # ------------------------------------------------------------

        if result["status"] == "judge_failed":
            judge_failures += 1
            continue

        # ============================================================
        # Criterion statistics
        # ============================================================

        if "criterion_agreement" in result:

            for criterion, data in result["criterion_agreement"].items():

                if criterion not in criterion_stats:
                    criterion_stats[criterion] = {
                        "total": 0,
                        "agreement": 0,
                    }

                criterion_stats[criterion]["total"] += 1

                if data["agreement"]:
                    criterion_stats[criterion]["agreement"] += 1

        # ============================================================
        # Overall score statistics
        # ============================================================

        if "overall_agreement" in result:

            overall_stats["total"] += 1

            if result["overall_agreement"]["agreement"]:
                overall_stats["agreement"] += 1

        # ============================================================
        # Winner statistics
        # ============================================================

        if "winner_agreement" in result:

            winner_stats["total"] += 1

            if result["winner_agreement"]["agreement"]:
                winner_stats["agreement"] += 1

    # ------------------------------------------------------------------------
    # Calculate criterion percentages
    # ------------------------------------------------------------------------

    for criterion, stats in criterion_stats.items():

        if stats["total"] > 0:

            stats["percentage"] = (
                stats["agreement"]
                / stats["total"]
                * 100
            )

        else:
            stats["percentage"] = 0.0

    # ------------------------------------------------------------------------
    # Overall percentage
    # ------------------------------------------------------------------------

    if overall_stats["total"] > 0:

        overall_percentage = (
            overall_stats["agreement"]
            / overall_stats["total"]
            * 100
        )

    else:
        overall_percentage = 0.0

    # ------------------------------------------------------------------------
    # Winner percentage
    # ------------------------------------------------------------------------

    if winner_stats["total"] > 0:

        winner_percentage = (
            winner_stats["agreement"]
            / winner_stats["total"]
            * 100
        )

    else:
        winner_percentage = 0.0

    # ------------------------------------------------------------------------
    # Final report
    # ------------------------------------------------------------------------

    return {
        "mode": mode,

        "total_cases": len(gold_cases),

        "evaluated_cases": (
            len(gold_cases) - judge_failures
        ),

        "judge_failures": judge_failures,

        "criterion_stats": criterion_stats,

        "overall_stats": {
            "total": overall_stats["total"],
            "agreement": overall_stats["agreement"],
            "percentage": overall_percentage,
        },

        "winner_stats": {
            "total": winner_stats["total"],
            "agreement": winner_stats["agreement"],
            "percentage": winner_percentage,
        },

        "case_results": results,
    }


# ============================================================================
# PRINT REPORT
# ============================================================================

def print_report(report: dict):
    """
    Print a concise validation report.
    """

    print()
    print("Judge Validation Report")
    print("=" * 50)
    print()

    print(f"Mode: {report['mode']}")
    print(f"Cases evaluated: {report['evaluated_cases']}")
    print(f"Judge failures: {report['judge_failures']}")
    print()

    # ------------------------------------------------------------------------
    # Criterion agreement
    # ------------------------------------------------------------------------

    if report["criterion_stats"]:

        print("Criterion Agreement:")

        for criterion, stats in sorted(
            report["criterion_stats"].items()
        ):

            print(
                f"  {criterion:25}"
                f"{stats['agreement']}/{stats['total']} "
                f"({stats['percentage']:.1f}%)"
            )

        print()

    # ------------------------------------------------------------------------
    # Overall score agreement
    # ------------------------------------------------------------------------

    if report["overall_stats"]["total"] > 0:

        print("Overall Score Agreement:")

        print(
            f"  {report['overall_stats']['agreement']}"
            f"/{report['overall_stats']['total']} "
            f"({report['overall_stats']['percentage']:.1f}%)"
        )

        print()

    # ------------------------------------------------------------------------
    # Pairwise winner agreement
    # ------------------------------------------------------------------------

    if report["winner_stats"]["total"] > 0:

        print("Pairwise Winner Agreement:")

        print(
            f"  {report['winner_stats']['agreement']}"
            f"/{report['winner_stats']['total']} "
            f"({report['winner_stats']['percentage']:.1f}%)"
        )

        print()

    elif report["mode"] == "pairwise":

        print("Pairwise Winner Agreement:")
        print("  No winner comparisons available.")
        print()


# ============================================================================
# CLI
# ============================================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Validate the LLM judge against "
            "human-labelled gold test cases."
        )
    )

    # ------------------------------------------------------------------------
    # Gold suite
    # ------------------------------------------------------------------------

    parser.add_argument(
        "--suite",
        required=True,
        help="Path to the gold suite JSON file.",
    )

    # ------------------------------------------------------------------------
    # Explicit validation mode
    # ------------------------------------------------------------------------

    parser.add_argument(
        "--mode",
        required=True,
        choices=["pointwise", "pairwise"],
        help="Validation mode.",
    )

    # ------------------------------------------------------------------------
    # Judge model
    # ------------------------------------------------------------------------

    parser.add_argument(
        "--judge-model",
        default="openai/gpt-oss-20b",
        help="Model used as the LLM judge.",
    )

    # ------------------------------------------------------------------------
    # Optional output
    # ------------------------------------------------------------------------

    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to save the validation report.",
    )

    args = parser.parse_args()

    # ========================================================================
    # LOAD GOLD SUITE
    # ========================================================================

    with open(
        args.suite,
        "r",
        encoding="utf-8",
    ) as f:

        data = json.load(f)

    # ========================================================================
    # PARSE GOLD CASES
    # ========================================================================

    gold_cases = [
        GoldTestCase(**case)
        for case in data
    ]

    # ========================================================================
    # VALIDATE
    # ========================================================================

    report = validate_suite(
        gold_cases=gold_cases,
        mode=args.mode,
        judge_model=args.judge_model,
    )

    # ========================================================================
    # PRINT
    # ========================================================================

    print_report(report)

    # ========================================================================
    # OPTIONAL JSON OUTPUT
    # ========================================================================

    if args.output:

        with open(
            args.output,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                report,
                f,
                indent=2,
            )

        print(
            f"Results saved to {args.output}"
        )


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()