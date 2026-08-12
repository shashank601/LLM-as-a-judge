# Judge module

"""
The judge: builds prompts, calls Groq, returns parsed Verdicts.

Supports:
- pointwise judging: evaluate one model output
- pairwise judging: compare two model outputs
- position-bias testing: swap A/B positions
"""

import os
from dotenv import load_dotenv

from groq import Groq

from .schemas import TestCase, Verdict
from .rubric import build_rubric_text
from .parser import parse_verdict

# Load environment variables from .env file
load_dotenv()

# Reads GROQ_API_KEY from the environment.
client = Groq(
    api_key=os.environ["GROQ_API_KEY"]
)


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------
def build_pointwise_prompt(
    case: TestCase,
) -> str:
    """Build a strict prompt for evaluating one model output."""

    rubric = build_rubric_text(case.criteria)

    reference_section = (
        f"""
REFERENCE / EXPECTED ANSWER:
{case.expected_output}

Use the reference as evidence for factual correctness when it is provided.
Do not require the response to use the exact wording of the reference.
Equivalent correct answers should receive full credit.
"""
        if case.expected_output
        else
        """
REFERENCE / EXPECTED ANSWER:
No reference answer was provided.

Do not invent a reference answer.
Evaluate correctness using the question, system instructions,
and generally established knowledge available to you.
"""
    )

    return f"""
You are a strict, impartial LLM evaluator.

Evaluate the AI RESPONSE against the task and rubric.
Do NOT assume the response is correct.
Check for factual errors, omissions, and instruction violations.

SYSTEM PROMPT GIVEN TO THE AI:
{case.system_prompt}

USER INPUT:
{case.input}

AI RESPONSE TO EVALUATE:
{case.model_output}

{reference_section}

RUBRIC:
{rubric}

EVALUATION RULES:

1. Evaluate each criterion independently.
2. Check for factual errors and important omissions.
3. Check system/user instructions literally.
4. Use expected_output as reference evidence when provided.
5. Accept equivalent correct answers; do not require exact wording.
6. overall_score MUST be the arithmetic mean of the three criterion scores.

RATIONALE REQUIREMENTS:

- For each criterion: keep the rationale under 12 words.
- For overall_rationale: keep it under 20 words.

OUTPUT REQUIREMENTS:

Return ONLY valid JSON.
Do not use markdown fences.
Do not include any text outside the JSON.

Use exactly this schema:

{{
  "criteria": [
    {{
      "name": "...",
      "score": 1,
      "rationale": "..."
    }}
  ],
  "overall_score": 0.0,
  "overall_rationale": "...",
  "winner": null
}}
""".strip()

def build_pairwise_prompt(
    case: TestCase,
    swap: bool = False,
) -> str:
    """
    Build a prompt comparing two model outputs.

    swap=False:
        A = case.model_output
        B = case.model_output_b

    swap=True:
        A = case.model_output_b
        B = case.model_output

    Running both orders helps detect position bias.
    """

    a = case.model_output
    b = case.model_output_b

    if swap:
        a, b = b, a

    rubric = build_rubric_text(case.criteria)

    reference_section = (
        f"\nREFERENCE / EXPECTED ANSWER:\n{case.expected_output}\n"
        if case.expected_output
        else ""
    )

    return f"""
You are an impartial evaluator comparing two AI responses.

SYSTEM PROMPT GIVEN TO THE AI:
{case.system_prompt}

USER INPUT:
{case.input}

RESPONSE A:
{a}

RESPONSE B:
{b}
{reference_section}

RUBRIC:
{rubric}

Compare Response A and Response B according to the rubric.

For each criterion:
- Give Response A a score from 1 to 5.
- Give Response B a score from 1 to 5.
- Explain the comparison in the rationale.

Choose the winner based on the overall scores:
- "A" if overall_score > overall_score_b.
- "B" if overall_score_b > overall_score.
- "tie" if the scores are equal or effectively equivalent.

overall_score = average of Response A's criterion scores.
overall_score_b = average of Response B's criterion scores.

Respond with ONLY valid JSON.
Do not use markdown fences.
Do not include any text outside the JSON.



Use exactly this shape:

{{
    "criteria": [
        {{
            "name": "...",
            "a_score": 1,
            "b_score": 1,
            "rationale": "..."
        }}
    ],
    "overall_score": 0.0,
    "overall_score_b": 0.0,
    "overall_rationale": "...",
    "winner": "A"
}}
""".strip()


# ---------------------------------------------------------------------------
# Groq API call
# ---------------------------------------------------------------------------

def call_judge(
    prompt: str,
    model: str = "llama-3.1-8b-instant",
) -> tuple[str, dict]:
    """
    Send the prompt to Groq.

    Returns:
        (raw_response_text, usage_dict)
    """

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    raw_text = response.choices[0].message.content or ""

    usage = {
        "input_tokens": response.usage.prompt_tokens if response.usage else 0,
        "output_tokens": response.usage.completion_tokens if response.usage else 0,
    }

    return raw_text, usage


# ---------------------------------------------------------------------------
# Main judge
# ---------------------------------------------------------------------------

def judge_case(
    case: TestCase,
    mode: str = "pointwise",
    swap: bool = False,
    model: str = "llama-3.1-8b-instant",
    max_retries: int = 1,
    log_file=None,
) -> Verdict | None:
    """
    Judge one test case.

    Pointwise:
        Evaluates case.model_output.

    Pairwise:
        Compares case.model_output against case.model_output_b.

    swap=True:
        Reverses A/B positions for position-bias testing.

    log_file:
        Optional path to JSONL log file for recording judge invocations.
    """

    if mode == "pointwise":

        prompt = build_pointwise_prompt(
            case=case,
        )

    elif mode == "pairwise":

        if case.model_output_b is None:
            raise ValueError(
                "model_output_b is required for pairwise evaluation."
            )

        prompt = build_pairwise_prompt(
            case=case,
            swap=swap,
        )

    else:
        raise ValueError(
            f"Unknown judging mode: {mode}. "
            "Expected 'pointwise' or 'pairwise'."
        )

    for attempt in range(max_retries + 1):

        try:
            raw_text, usage = call_judge(
                prompt=prompt,
                model=model,
            )

            # Record the judge call immediately after receiving response
            if log_file is not None:
                from .logger import log_judge_call
                log_judge_call(
                    log_file=log_file,
                    case_id=case.id,
                    model=model,
                    prompt=prompt,
                    raw_response=raw_text,
                    usage=usage,
                )

        except Exception as e:
            # Record failure if logger is available
            if log_file is not None:
                from .logger import log_failure
                log_failure(
                    log_file=log_file,
                    case_id=case.id,
                    model=model,
                    error=str(e),
                    prompt=prompt,
                )
            raise

        verdict = parse_verdict(
            raw_text,
            case_id=case.id,
        )

        if verdict is not None:

            # Attach audit information.
            verdict.judge_model = model
            verdict.raw_response = raw_text
            verdict.prompt_used = prompt
            verdict.input_tokens = usage["input_tokens"]
            verdict.output_tokens = usage["output_tokens"]

            return verdict

        # Retry with an explicit correction instruction.
        prompt += """

Your previous response was invalid.

Return ONLY valid JSON matching the required schema.
Do not use markdown.
Do not add explanations outside the JSON.
"""

    # All retries failed
    if log_file is not None:
        from .logger import log_failure
        log_failure(
            log_file=log_file,
            case_id=case.id,
            model=model,
            error="All retries failed - could not parse response",
            prompt=prompt,
        )

    return None