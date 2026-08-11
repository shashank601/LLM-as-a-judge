# Rubric module
"""
Rubric used by the LLM judge.

Defines:
- which criteria are evaluated
- what the 1-5 scale means
- few-shot anchors to reduce score clustering
"""

DEFAULT_CRITERIA = [
    "correctness",
    "completeness",
    "instruction_following",
]


SCORE_ANCHORS = {
    "correctness": {
        1: "Factually wrong or seriously misleading.",
        2: "Major factual problems.",
        3: "Partially correct with a noticeable error or omission.",
        4: "Essentially correct with a minor issue.",
        5: "Fully correct and precise.",
    },

    "completeness": {
        1: "Fails to address the request.",
        2: "Addresses only a small part of the request.",
        3: "Addresses the main request but misses important details.",
        4: "Answers well with a minor omission.",
        5: "Addresses all important parts of the request.",
    },

    "instruction_following": {
        1: "Ignores or violates the main instructions.",
        2: "Violates important instructions.",
        3: "Follows the main instructions but misses an important requirement.",
        4: "Follows instructions with a minor deviation.",
        5: "Follows all important instructions.",
    },
}

def build_rubric_text(criteria: list[str] | None = None) -> str:
    """Build rubric instructions for the judge prompt."""

    criteria = criteria or DEFAULT_CRITERIA

    lines = [
        "Score each criterion from 1 (poor) to 5 (excellent).",
        "",
    ]

    for criterion in criteria:
        lines.append(f"- {criterion}")

        anchors = SCORE_ANCHORS.get(criterion)

        if anchors:
            for level, description in anchors.items():
                lines.append(f"    {level}: {description}")

    return "\n".join(lines)