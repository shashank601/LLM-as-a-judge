"""
Simple append-based logging for judge evaluations.

Logs exact prompts and raw LLM responses to JSONL format.
Each line is a JSON event - crash-safe because we append immediately.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


def init_logger(
    judge_model: str,
    logs_dir: str = "logs",
) -> tuple[str, Path]:
    """
    Initialize a logger for a run.

    Returns:
        (run_id, log_file_path)
    """
    logs_path = Path(logs_dir)
    logs_path.mkdir(parents=True, exist_ok=True)

    # Use timestamp + random suffix for uniqueness
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    suffix = uuid.uuid4().hex[:8]
    run_id = f"{timestamp}_{suffix}"
    log_file = logs_path / f"run_{run_id}.jsonl"

    # Write header with run metadata
    header = {
        "run_id": run_id,
        "started_at": datetime.utcnow().isoformat() + "Z",
        "judge_model": judge_model,
    }

    with open(log_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(header) + "\n")

    return run_id, log_file


def log_judge_call(
    log_file: Path,
    case_id: str,
    model: str,
    prompt: str,
    raw_response: str,
    usage: dict,
):
    """
    Log a single judge invocation.

    Appends immediately to the log file for crash safety.

    Args:
        log_file: Path to the JSONL log file
        case_id: ID of the test case
        model: Model used for this call
        prompt: Exact prompt sent to the judge
        raw_response: Exact raw response from the judge
        usage: Token usage dict with input_tokens and output_tokens
    """
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")

    # Calculate total_tokens only if both are available
    total_tokens = (
        input_tokens + output_tokens
        if input_tokens is not None and output_tokens is not None
        else None
    )

    event = {
        "case_id": case_id,
        "judge_model": model,
        "prompt": prompt,
        "raw_response": raw_response,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def log_failure(
    log_file: Path,
    case_id: str,
    model: str,
    error: str,
    prompt: Optional[str] = None,
):
    """
    Log a failed judge invocation.

    Args:
        log_file: Path to the JSONL log file
        case_id: ID of the test case
        model: Model used for this call
        error: Error message
        prompt: Prompt if available
    """
    event = {
        "case_id": case_id,
        "judge_model": model,
        "error": error,
        "prompt": prompt,
        "input_tokens": None,
        "output_tokens": None,
        "total_tokens": None,
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

