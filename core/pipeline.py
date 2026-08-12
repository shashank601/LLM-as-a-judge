# Pipeline module
"""
Evaluation pipeline.

Responsible for:
1. Loading test cases.
2. Sending test cases to the judge.
3. Returning Verdicts.
"""

import json

from .schemas import TestCase, Verdict
from .judge import judge_case


def load_suite(path: str) -> list[TestCase]:
    """Load test cases from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [TestCase(**case) for case in data]


def evaluate_case(
    case: TestCase,
    mode: str = "pointwise",
    judge_model: str = "llama-3.1-8b-instant",
    log_file=None,
) -> Verdict | None:
    """
    Evaluate a test case.

    Pointwise:
        TestCase (with model_output)
            -> Judge
            -> Verdict

    Pairwise:
        Not yet implemented.

    log_file:
        Optional path to JSONL log file for recording judge invocations.
    """

    if mode == "pointwise":
        return judge_case(
            case=case,
            mode="pointwise",
            model=judge_model,
            log_file=log_file,
        )

    elif mode == "pairwise":
        return judge_case(
            case=case,
            mode="pairwise",
            model=judge_model,
            log_file=log_file,
        )

    else:
        raise ValueError(
            f"Unknown mode: {mode}. "
            "Expected 'pointwise'."
        )