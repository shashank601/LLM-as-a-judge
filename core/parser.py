# Parser module

"""
Parses raw judge-LLM responses into validated Verdict objects.

The parser handles common LLM formatting problems:
- Markdown code fences
- Extra text before/after JSON
- Invalid JSON
- Missing required fields
- Invalid field types
- Invalid score ranges
- Invalid winner values
"""

import json
import re

from pydantic import ValidationError

from .schemas import Verdict


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------

def _extract_json(raw_text: str) -> str:
    """
    Extract the most likely JSON object from an LLM response.

    Handles responses such as:

        {"criteria": [...]}

    and:

        ```json
        {"criteria": [...]}
        ```

    and:

        Here is the result:
        {"criteria": [...]}
    """

    text = raw_text.strip()

    # Remove markdown code fences if present.
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    text = text.strip()

    # If the entire response is already JSON, use it.
    if text.startswith("{") and text.endswith("}"):
        return text

    # Otherwise try to find a JSON object inside surrounding text.
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in judge response.")

    return text[start:end + 1]


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse_verdict(
    raw_text: str,
    case_id: str,
) -> Verdict | None:
    """
    Parse raw LLM output into a validated Verdict.

    Returns:
        Verdict if the response is valid.
        None if the response cannot be parsed or validated.
    """

    if not raw_text or not raw_text.strip():
        return None

    try:
        json_text = _extract_json(raw_text)

        data = json.loads(json_text)

        if not isinstance(data, dict):
            return None

        verdict = Verdict(
            case_id=case_id,
            **data,
        )

        return verdict

    except (
        json.JSONDecodeError,
        ValueError,
        TypeError,
        ValidationError,
    ):
        return None