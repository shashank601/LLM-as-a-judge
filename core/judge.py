# Judge module

"""
The judge: builds prompts, calls Gemini, returns parsed Verdicts.

Supports:
- pointwise judging: evaluate one model output
- pairwise judging: compare two model outputs
- position-bias testing: swap A/B positions
"""

from google import genai

from core.schemas import TestCase, Verdict
from core.rubric import build_rubric_text
from core.parser import parse_verdict


# Reads GEMINI_API_KEY from the environment.
client = genai.Client()


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def build_pointwise_prompt(
    case: TestCase,
    model_output: str,
) -> str:
    """Build a prompt for evaluating one model output."""

    rubric = build_rubric_text(case.criteria)

    reference_section = (
        f"\nREFERENCE / EXPECTED ANSWER:\n{case.expected_output}\n"
        if case.expected_output
        else ""
    )

    return f"""
You are an impartial evaluator. Score the AI's response below.

SYSTEM PROMPT GIVEN TO THE AI:
{case.system_prompt}

USER INPUT:
{case.input}

AI RESPONSE TO EVALUATE:
{model_output}
{reference_section}

RUBRIC:
{rubric}

Evaluate the response according to every criterion.

For each criterion:
- Give a score from 1 to 5.
- Provide a concise rationale.

Calculate the overall score as the average of the criterion scores.

Respond with ONLY valid JSON.
Do not use markdown fences.
Do not include any text outside the JSON.

Use exactly this shape:

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
    model_output: str,
    model_output_b: str,
    swap: bool = False,
) -> str:
    """
    Build a prompt comparing two model outputs.

    swap=False:
        A = model_output
        B = model_output_b

    swap=True:
        A = model_output_b
        B = model_output

    Running both orders helps detect position bias.
    """

    a = model_output
    b = model_output_b

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
- Give a score from 1 to 5 representing the quality of the better response on that criterion.
- Explain the comparison in the rationale.

Then select the overall winner:
- "A" if Response A is better overall.
- "B" if Response B is better overall.
- "tie" if both are effectively equal.

Calculate the overall score from the criterion scores.

Respond with ONLY valid JSON.
Do not use markdown fences.
Do not include any text outside the JSON.

Use exactly this shape:

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
  "winner": "A"
}}
""".strip()


# ---------------------------------------------------------------------------
# Gemini API call
# ---------------------------------------------------------------------------

def call_judge(
    prompt: str,
    model: str = "gemini-2.5-flash",
) -> tuple[str, dict]:
    """
    Send the prompt to Gemini.

    Returns:
        (raw_response_text, usage_dict)
    """

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    raw_text = response.text or ""

    usage_metadata = getattr(response, "usage_metadata", None)

    usage = {
        "input_tokens": getattr(
            usage_metadata,
            "prompt_token_count",
            0,
        ),
        "output_tokens": getattr(
            usage_metadata,
            "candidates_token_count",
            0,
        ),
    }

    return raw_text, usage


# ---------------------------------------------------------------------------
# Main judge
# ---------------------------------------------------------------------------

def judge_case(
    case: TestCase,
    model_output: str,
    model_output_b: str | None = None,
    mode: str = "pointwise",
    swap: bool = False,
    model: str = "gemini-2.5-flash",
    max_retries: int = 1,
) -> Verdict | None:
    """
    Judge one test case.

    Pointwise:
        Evaluates model_output.

    Pairwise:
        Compares model_output against model_output_b.

    swap=True:
        Reverses A/B positions for position-bias testing.
    """

    if mode == "pointwise":

        prompt = build_pointwise_prompt(
            case=case,
            model_output=model_output,
        )

    elif mode == "pairwise":

        if model_output_b is None:
            raise ValueError(
                "model_output_b is required for pairwise evaluation."
            )

        prompt = build_pairwise_prompt(
            case=case,
            model_output=model_output,
            model_output_b=model_output_b,
            swap=swap,
        )

    else:
        raise ValueError(
            f"Unknown judging mode: {mode}. "
            "Expected 'pointwise' or 'pairwise'."
        )

    for attempt in range(max_retries + 1):

        raw_text, usage = call_judge(
            prompt=prompt,
            model=model,
        )

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

    return None