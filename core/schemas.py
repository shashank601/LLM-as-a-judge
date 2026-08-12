from typing import Literal, Optional
from pydantic import BaseModel, Field


class TestCase(BaseModel):
    id: str
    input: str
    system_prompt: str
    model_output: str
    model_output_b: Optional[str] = None
    expected_output: Optional[str] = None
    criteria: Optional[list[str]] = None



class GoldTestCase(BaseModel):
    id: str

    input: str
    system_prompt: str

    model_output: str
    model_output_b: Optional[str] = None

    criteria: list[str]

    human_scores: Optional[dict[str, int]] = None
    human_overall_score: Optional[float] = None

    human_winner: Optional[Literal["A", "B", "tie"]] = None


# ---------------------------------------------------------------------------
# Pointwise
# ---------------------------------------------------------------------------

class CriterionScore(BaseModel):
    """Score for one criterion in pointwise evaluation."""

    name: str
    score: int = Field(ge=1, le=5)
    rationale: str


# ---------------------------------------------------------------------------
# Pairwise
# ---------------------------------------------------------------------------

class PairwiseCriterionScore(BaseModel):
    """Comparison of two responses for one criterion."""

    name: str

    a_score: int = Field(ge=1, le=5)
    b_score: int = Field(ge=1, le=5)

    rationale: str


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------

class Verdict(BaseModel):
    """Judge's final result for one test case."""

    case_id: str

    # Pointwise: CriterionScore
    # Pairwise: PairwiseCriterionScore
    criteria: list[CriterionScore | PairwiseCriterionScore]

    # Pointwise uses overall_score.
    # Pairwise uses both overall_score and overall_score_b.
    overall_score: Optional[float] = None
    overall_score_b: Optional[float] = None

    overall_rationale: Optional[str] = None

    # Only populated during pairwise evaluation.
    winner: Optional[Literal["A", "B", "tie"]] = None

    # -----------------------------------------------------------------------
    # Audit metadata
    # -----------------------------------------------------------------------

    judge_model: Optional[str] = None
    raw_response: Optional[str] = None
    prompt_used: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None