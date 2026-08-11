# Schemas module
"""
Data models for the LLM judge pipeline.

Everything else imports these models.
"""

from typing import Literal, Optional


from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

class TestCase(BaseModel):
    """
    One test case given to the judge.
    
    A TestCase represents one evaluation problem.
    """

    id: str

    # The task/question given to the model.
    input: str

    # System instructions given to the model being evaluated.
    system_prompt: str

    # Optional reference/answer key.
    # The judge can use this when it exists.
    expected_output: Optional[str] = None

    # Optional criteria for this particular case.
    # If None, judge.py uses the default rubric.
    criteria: Optional[list[str]] = None


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

class CriterionScore(BaseModel):
    """Judge's score for one rubric criterion."""

    name: str

    # 1 = very poor, 5 = excellent.
    score: int = Field(ge=1, le=5)

    # Required explanation for the score.
    rationale: str


class Verdict(BaseModel):
    """Judge's final result for one test case."""

    case_id: str

    # One score for every criterion evaluated.
    criteria: list[CriterionScore]

    # Calculated by our code from the criterion scores.
    overall_score: float | None = None

    # Explanation of the overall judgment.
    overall_rationale: str | None = None

    # Only populated during pairwise evaluation.
    winner: Optional[Literal["A", "B", "tie"]] = None

    # -----------------------------------------------------------------------
    # Audit metadata
    # -----------------------------------------------------------------------

    # Which model acted as the judge?
    judge_model: Optional[str] = None

    # Exact raw response from the judge LLM.
    raw_response: Optional[str] = None

    # Exact prompt sent to the judge LLM.
    prompt_used: Optional[str] = None

    # Token usage, if provided by the API.
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None