"""
Offline replay of saved judge responses.

Replay reads saved raw judge responses from JSONL and reconstructs Verdict objects
using the existing response parsing logic. No API calls are made.
"""

import json
from typing import Optional
from .schemas import Verdict
from .parser import parse_verdict


def replay_run(log_path: str) -> tuple[list[Verdict], list[dict]]:
    """
    Replay a saved run log to reconstruct Verdict objects.

    This function is completely offline - it does not make any API calls.

    Args:
        log_path: Path to the run log JSONL file

    Returns:
        Tuple of (verdicts, errors)
        - verdicts: List of successfully parsed Verdict objects
        - errors: List of parsing errors with case_id and error message
    """
    verdicts = []
    errors = []

    with open(log_path, "r", encoding="utf-8") as f:
        # Skip header line (run metadata)
        next(f)

        # Read each event line
        for line in f:
            if not line.strip():
                continue

            event = json.loads(line)
            case_id = event["case_id"]

            # Skip failed calls
            if "error" in event:
                errors.append({
                    "case_id": case_id,
                    "error": f"Original call failed: {event['error']}",
                })
                continue

            raw_response = event["raw_response"]

            # Parse using the existing parser
            verdict = parse_verdict(raw_response, case_id=case_id)

            if verdict is None:
                errors.append({
                    "case_id": case_id,
                    "error": "Failed to parse response",
                })
            else:
                verdicts.append(verdict)

    return verdicts, errors
