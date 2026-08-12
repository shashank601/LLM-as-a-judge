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
    judge_model: str = "openai/gpt-oss-20b",
) -> Verdict | None:
    """
    Evaluate a test case.

    Pointwise:
        TestCase (with model_output)
            -> Judge
            -> Verdict

    Pairwise:
        Not yet implemented.
    """

    if mode == "pointwise":
        return judge_case(
            case=case,
            mode="pointwise",
            model=judge_model,
        )

    elif mode == "pairwise":
        raise ValueError(
            "Pairwise evaluation is not yet implemented."
        )

    else:
        raise ValueError(
            f"Unknown mode: {mode}. "
            "Expected 'pointwise'."
        )