"""
Aggregation of Verdict objects into evaluation summaries.

This module calculates statistics from already-created Verdict objects.
It does not call LLMs, perform logging, or invoke the pipeline.
"""

from typing import Optional
from .schemas import Verdict


def aggregate(verdicts: list[Verdict]) -> dict:
    """
    Aggregate verdicts into an evaluation summary.

    Args:
        verdicts: List of Verdict objects to aggregate

    Returns:
        Dictionary containing aggregated statistics
    """
    if not verdicts:
        return {
            "total_cases": 0,
            "criteria_scores": {},
            "overall_score": None,
        }

    total_cases = len(verdicts)

    # Aggregate criterion scores
    criterion_sums = {}
    criterion_counts = {}

    for verdict in verdicts:
        for criterion in verdict.criteria:
            name = criterion.name
            
            # Handle both pointwise (score) and pairwise (a_score, b_score)
            if hasattr(criterion, 'score'):
                # Pointwise: single score
                score = criterion.score
                if name not in criterion_sums:
                    criterion_sums[name] = 0
                    criterion_counts[name] = 0
                criterion_sums[name] += score
                criterion_counts[name] += 1
            else:
                # Pairwise: a_score and b_score
                a_score = criterion.a_score
                b_score = criterion.b_score
                for score in [a_score, b_score]:
                    if name not in criterion_sums:
                        criterion_sums[name] = 0
                        criterion_counts[name] = 0
                    criterion_sums[name] += score
                    criterion_counts[name] += 1

    # Calculate average per criterion
    criteria_scores = {}
    for name in criterion_sums:
        avg = criterion_sums[name] / criterion_counts[name]
        criteria_scores[name] = round(avg, 2)

    # Aggregate overall scores
    overall_sum = 0
    overall_count = 0

    for verdict in verdicts:
        if verdict.overall_score is not None:
            overall_sum += verdict.overall_score
            overall_count += 1

    overall_avg = (
        round(overall_sum / overall_count, 2)
        if overall_count > 0
        else None
    )

    return {
        "total_cases": total_cases,
        "criteria_scores": criteria_scores,
        "overall_score": overall_avg,
    }
