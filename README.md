# 🎯 LLM-as-a-Judge Evaluation Framework

> A robust two-level evaluation system for assessing LLM outputs using automated LLM judges with validation against human-labeled ground truth.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Production%20Ready-success)

## 📋 Table of Contents

- [🌟 Introduction](#-introduction)
- [🏗️ Architecture](#️-architecture)
- [🔧 Tech Stack](#-tech-stack)
- [🚀 Entry Points](#-entry-points)
- [📊 Data Schemas](#-data-schemas)
- [⚙️ Setup & Installation](#️-setup--installation)
- [🔑 Environment Configuration](#-environment-configuration)
- [📈 Usage Examples](#-usage-examples)
- [🎯 Evaluation Modes](#-evaluation-modes)
- [🛡️ Adversarial Testing](#️-adversarial-testing)
- [🔍 Validation Results](#-validation-results)
- [🤖 AI Usage Disclosure](#-ai-usage-disclosure)
- [📸 Screenshots](#-screenshots)
- [🎓 Assumptions & Design Decisions](#-assumptions--design-decisions)
- [🚧 Future Enhancements](#-future-enhancements)

---

## 🌟 Introduction

This project implements a **two-level LLM evaluation framework** designed to systematically assess model outputs using automated LLM judges. The system provides:

- **🎯 Pointwise Evaluation**: Evaluate individual model outputs against specific criteria
- **⚖️ Pairwise Comparison**: Compare two model outputs to determine relative performance
- **✅ Judge Validation**: Validate automated judge performance against human-labeled ground truth
- **🛡️ Adversarial Testing**: Test judge robustness against confidently-stated incorrect responses
- **📊 Comprehensive Metrics**: Track correctness, completeness, and instruction following
- **🔄 Position Bias Detection**: Test for ordering bias in pairwise comparisons

The framework is designed for research teams, ML engineers, and data scientists who need reliable, scalable evaluation of LLM systems.

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM-as-a-Judge System                     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Entry Points │   │   Core Logic  │   │   Data Layer  │
└───────────────┘   └───────────────┘   └───────────────┘
        │                     │                     │
        │                     │                     │
        ├─ run.py             ├─ judge.py          ├─ schemas.py
        ├─ validate.py        ├─ parser.py         ├─ rubric.py
        └─ compare.py         ├─ pipeline.py       └─ suites/
                              ├─ aggregate.py
                              └─ logger.py
```

### Two-Level Architecture

#### Level 1: The Judge
```
TestCase → Prompt Builder → Groq API → Response Parser → Verdict
```

The judge level evaluates model outputs using:
- **Strict Rubric-Based Evaluation**: 1-5 scale across multiple criteria
- **Reference-Based Grounding**: Optional expected output for factual correctness
- **Comprehensive Logging**: JSONL logs of all judge interactions
- **Retry Logic**: Automatic retries with correction instructions

#### Level 2: Judge Validator
```
GoldTestCase → TestCase → Judge → Verdict → Comparison → Validation Report
```

The validator level assesses judge reliability by:
- **Human-AI Agreement**: Comparing judge scores against human labels
- **Criterion-Level Analysis**: Per-criteria agreement statistics
- **Tolerance Levels**: Configurable tolerance for score variations
- **Failure Detection**: Identifying when judge produces invalid outputs
- **Adversarial Robustness**: Testing judge resistance to confidently-stated falsehoods

### Component Interactions

```
┌──────────────────────────────────────────────────────────────────┐
│                        Evaluation Pipeline                        │
└──────────────────────────────────────────────────────────────────┘

Input Suite JSON
       │
       ▼
┌──────────────┐
│ Load Suite   │ (core/pipeline.py)
└──────────────┘
       │
       ▼
┌──────────────┐
│ Build Prompt │ (core/judge.py)
└──────────────┘
       │
       ▼
┌──────────────┐
│ Call Groq    │ (core/judge.py)
└──────────────┘
       │
       ▼
┌──────────────┐
│ Parse JSON   │ (core/parser.py)
└──────────────┘
       │
       ▼
┌──────────────┐
│ Validate     │ (core/schemas.py)
└──────────────┘
       │
       ▼
┌──────────────┐
│ Log Results  │ (core/logger.py)
└──────────────┘
       │
       ▼
┌──────────────┐
│ Aggregate    │ (core/aggregate.py)
└──────────────┘
       │
       ▼
Final Report
```

---

## 🔧 Tech Stack

### Core Technologies

| Component | Technology | Purpose |
|----------|-----------|---------|
| **Language** | Python 3.8+ | Primary implementation language |
| **API Client** | Groq Python SDK | LLM API integration |
| **Data Validation** | Pydantic v2 | Schema validation and type safety |
| **Environment** | python-dotenv | Environment variable management |
| **Logging** | JSON (custom) | Structured logging format |

### Model Support

- **Primary Judge Model**: Llama 3.1 8B Instant (via Groq)
- **Configurable**: Any Groq-hosted model can be specified via CLI

### Dependencies

```txt
pydantic>=2.0.0
groq>=0.5.0
python-dotenv>=1.0.0
```

---

## 🚀 Entry Points

### 1. **run.py** - Pointwise Evaluation

Evaluate model outputs against predefined criteria.

```bash
python run.py --suite suites/judge_suite.json --judge-model llama-3.1-8b-instant
```

**What it does:**
- Loads test cases from JSON suite
- Evaluates each case using the LLM judge
- Aggregates results across all cases
- Generates comprehensive report with criteria scores

**Output:**
- JSON report in `reports/` directory
- JSONL log in `logs/` directory
- Console summary with scores

### 2. **validate.py** - Judge Validation

Validate judge performance against human-labeled ground truth.

```bash
# Pointwise validation
python validate.py --suite suites/gold_pointwise.json --mode pointwise

# Pairwise validation
python validate.py --suite suites/gold_pairwise.json --mode pairwise

# Adversarial validation (new!)
python validate.py --suite suites/adversarial_suite.json --mode pairwise --adversarial
```

**What it does:**
- Loads gold standard test cases with human labels
- Runs judge on each case (human labels hidden)
- Compares judge verdicts against human scores
- Calculates agreement statistics per criterion
- Generates validation report

**Output:**
- Agreement percentages per criterion
- Overall score agreement
- Detailed case-by-case breakdown
- Adversarial-specific metrics (when `--adversarial` flag is used)

### 3. **compare.py** - Pairwise Comparison

Compare two model outputs with position bias detection.

```bash
python compare.py --suite suites/judge_suite.json
```

**What it does:**
- Evaluates Response A vs Response B
- Swaps positions and evaluates again
- Detects position bias (preference flips)
- Declares overall winner based on consistent results

**Output:**
- Win rates for each response
- Position bias detection
- Overall winner declaration

---

## 📊 Data Schemas

### TestCase Schema

```python
class TestCase(BaseModel):
    id: str                              # Unique case identifier
    input: str                           # User input/prompt
    system_prompt: str                   # System instructions
    model_output: str                    # Model response to evaluate
    model_output_b: Optional[str]        # Second response (pairwise)
    expected_output: Optional[str]       # Reference answer (optional)
    criteria: Optional[list[str]]        # Evaluation criteria
```

### GoldTestCase Schema

```python
class GoldTestCase(BaseModel):
    id: str                              # Unique case identifier
    input: str                           # User input/prompt
    system_prompt: str                   # System instructions
    model_output: str                    # Model response to evaluate
    model_output_b: Optional[str]        # Second response (pairwise)
    criteria: list[str]                  # Evaluation criteria
    human_scores: Optional[dict[str, int]]      # Human-labeled scores
    human_overall_score: Optional[float]        # Human overall score
    human_winner: Optional[Literal["A", "B", "tie"]]  # Human winner (pairwise)
```

### Verdict Schema

```python
class Verdict(BaseModel):
    case_id: str                         # Associated test case
    criteria: list[CriterionScore | PairwiseCriterionScore]  # Per-criterion scores
    overall_score: Optional[float]       # Overall score (pointwise)
    overall_score_b: Optional[float]     # Overall score for B (pairwise)
    overall_rationale: Optional[str]     # Overall justification
    winner: Optional[Literal["A", "B", "tie"]]  # Winner (pairwise)
    judge_model: Optional[str]           # Model used for judgment
    raw_response: Optional[str]         # Raw LLM response
    prompt_used: Optional[str]           # Prompt sent to judge
    input_tokens: Optional[int]          # Input token count
    output_tokens: Optional[int]         # Output token count
```

### CriterionScore Schema (Pointwise)

```python
class CriterionScore(BaseModel):
    name: str                            # Criterion name
    score: int (1-5)                     # Score value
    rationale: str                       # Justification
```

### PairwiseCriterionScore Schema

```python
class PairwiseCriterionScore(BaseModel):
    name: str                            # Criterion name
    a_score: int (1-5)                   # Score for Response A
    b_score: int (1-5)                   # Score for Response B
    rationale: str                       # Comparison justification
```

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.8 or higher
- Groq API key
- Git (for cloning)

### Installation Steps

1. **Clone the repository**
```bash
git clone https://github.com/shashank601/LLM-as-a-judge.git
cd LLM-as-a-judge
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your Groq API key
```

5. **Verify installation**
```bash
python run.py --suite suites/judge_suite.json --judge-model llama-3.1-8b-instant
```

---

## 🔑 Environment Configuration

### Required Environment Variables

Create a `.env` file in the project root:

```env
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here

# Optional: Custom judge model (overrides default)
# JUDGE_MODEL=llama-3.1-8b-instant
```

### Getting Your Groq API Key

1. Visit [console.groq.com](https://console.groq.com)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and add it to your `.env` file

---

## 📈 Usage Examples

### Basic Pointwise Evaluation

```bash
python run.py --suite suites/judge_suite.json --judge-model llama-3.1-8b-instant
```

**Expected Output:**
```
Evaluation Results
==================================================
Total cases: 11
Evaluated: 10
Failed: 1

Criteria Scores:
  correctness: 3.70
  completeness: 4.70
  instruction_following: 4.00

Overall Score: 4.00

Report saved to reports\report_20260812_063002_0c34cd03.json
Run log saved to logs\run_20260812_063002_0c34cd03.jsonl
```

### Judge Validation

```bash
python validate.py --suite suites/gold_pointwise.json --mode pointwise
```

**Expected Output:**
```
Judge Validation Report
==================================================

Mode: pointwise
Cases evaluated: 12
Judge failures: 0

Criterion Agreement:
  completeness             7/12 (58.3%)
  correctness              9/12 (75.0%)
  instruction_following    5/12 (41.7%)

Overall Score Agreement:
  7/12 (58.3%)
```

### Adversarial Testing

```bash
python validate.py --suite suites/adversarial_suite.json --mode pairwise --adversarial
```

**Expected Output:**
```
Judge Validation Report
==================================================

Mode: pairwise
Cases evaluated: 8
Judge failures: 0

Pairwise Winner Agreement:
  7/8 (87.5%)

Adversarial Test Results
--------------------------------------------------
Adversarial probes: 8
Expected winners: 8
Judge winners correct: 6
Fooled: 2
Adversarial failure rate: 25.0%

WARNING: Judge was fooled by adversarial cases!
   The judge preferred incorrect but confidently-stated responses.
```

### Custom Judge Model

```bash
python run.py --suite suites/judge_suite.json --judge-model llama-3.1-70b-versatile
```

---

## 🎯 Evaluation Modes

### Pointwise Evaluation

**Purpose**: Evaluate a single model output against specific criteria

**Process**:
1. Judge receives test case with model output
2. Evaluates against predefined rubric (correctness, completeness, instruction_following)
3. Returns scores (1-5) for each criterion
4. Calculates overall score as arithmetic mean
5. Provides rationale for each score

**Use Cases**:
- Quality assessment of individual responses
- Benchmarking model performance
- A/B testing prompt variations
- Regression testing

### Pairwise Evaluation

**Purpose**: Compare two model outputs to determine relative performance

**Process**:
1. Judge receives test case with two model outputs (A and B)
2. Evaluates both against same rubric
3. Returns scores for both responses
4. Determines winner based on overall scores
5. Can detect position bias by swapping A/B

**Use Cases**:
- Model comparison
- Prompt engineering
- Configuration testing
- Position bias detection

---

## 🛡️ Adversarial Testing

### Overview

Adversarial testing evaluates the judge's robustness against **confidently-stated incorrect responses**. This is critical because LLM judges can be fooled by responses that sound authoritative but contain factual errors.

### How It Works

The adversarial testing uses your **existing validation infrastructure** - no new judging logic required:

1. **Adversarial Test Suite**: Contains cases where Response A is correct and Response B is confidently incorrect
2. **Human Winner**: Each case specifies the expected winner (always "A" in adversarial cases)
3. **Validation**: Run the suite through the existing pairwise validation
4. **Interpretation**: Winner disagreement = adversarial failure

### Creating Adversarial Cases

Adversarial cases follow the standard `GoldTestCase` schema:

```json
{
  "id": "adv_001",
  "input": "What is the capital of France?",
  "system_prompt": "Answer accurately.",
  "model_output": "Paris.",
  "model_output_b": "The capital of France is London. This is an obvious and well-established fact...",
  "criteria": ["correctness", "completeness", "instruction_following"],
  "human_winner": "A"
}
```

**Key characteristics:**
- Response A: Correct, concise answer
- Response B: Incorrect but confidently stated with elaboration
- Human winner: Always "A" (the correct response)

### Running Adversarial Tests

```bash
python validate.py --suite suites/adversarial_suite.json --mode pairwise --adversarial
```

The `--adversarial` flag enables explicit adversarial reporting:
- Interprets winner disagreement as adversarial failure
- Shows adversarial-specific metrics
- Provides clear warnings when judge is fooled

### Adversarial Metrics

```
Adversarial Test Results
--------------------------------------------------
Adversarial probes: 8
Expected winners: 8
Judge winners correct: 6
Fooled: 2
Adversarial failure rate: 25.0%
```

**Interpretation:**
- **Adversarial probes**: Total number of adversarial test cases
- **Expected winners**: Cases where Response A should win
- **Judge winners correct**: Cases where judge correctly chose A
- **Fooled**: Cases where judge incorrectly chose B
- **Failure rate**: Percentage of adversarial cases that fooled the judge

### Current Adversarial Suite

The project includes `suites/adversarial_suite.json` with 8 adversarial probes covering:
- Basic factual errors (geography, math, science)
- Historical inaccuracies
- Scientific misconceptions
- Confidence tricks (long, authoritative-sounding incorrect responses)

### Why This Matters

Adversarial testing is crucial because:
- **Real-world deployment**: Users may attempt to fool evaluation systems
- **Confidence bias**: LLMs prefer confident responses over correct ones
- **Safety**: Ensures judge doesn't validate harmful misinformation
- **Trust**: Builds confidence in evaluation system reliability

---

## 🔍 Validation Results

### Current Validation Statistics

Based on validation against 12 human-labeled gold standard cases:

| Criterion | Agreement Rate | Human-Judge Alignment |
|-----------|---------------|----------------------|
| **Correctness** | 75.0% (9/12) | High alignment on factual accuracy |
| **Completeness** | 58.3% (7/12) | Moderate alignment on response coverage |
| **Instruction Following** | 41.7% (5/12) | Lower alignment on constraint adherence |
| **Overall Score** | 58.3% (7/12) | Moderate overall agreement |

### Key Findings

✅ **Strengths**:
- High accuracy in detecting factual errors (75% agreement)
- Consistent scoring for clear-cut cases
- Reliable identification of completely incorrect responses

⚠️ **Areas for Improvement**:
- Instruction following detection needs refinement
- Completeness scoring shows higher variance
- Tolerance levels adjusted for weaker LLMs

### Adversarial Test Results

Latest adversarial validation results:

| Metric | Value | Status |
|--------|-------|--------|
| **Adversarial Probes** | 8 | ✅ |
| **Judge Winners Correct** | 6 | ⚠️ |
| **Fooled** | 2 | ⚠️ |
| **Failure Rate** | 25.0% | ⚠️ |

**Analysis**: The judge shows moderate resistance to adversarial attacks. It correctly identified 6 out of 8 confidently-stated incorrect responses, but was fooled by 2 cases, indicating room for improvement in detecting confidently-stated falsehoods.

### Validation Methodology

The validation system uses a **tolerance-based approach**:
- **Exact Match**: Judge score equals human score
- **Tolerance Match**: Judge score within ±0.5 of human score (for overall scores)
- **Criterion-Level**: Per-criteria exact matching
- **Overall-Level**: Overall score with tolerance
- **Adversarial-Level**: Winner agreement in pairwise mode

---

## 🤖 AI Usage Disclosure

### Code Generation

This project was developed with assistance from **Devin AI** (https://devin.ai), an AI-powered software development assistant. Devin contributed to:

- ✅ Core architecture implementation
- ✅ Data schema design and validation
- ✅ Parser and logger modules
- ✅ Test case structure and examples
- ✅ Error handling and retry logic
- ✅ Adversarial testing integration

### Architecture Design

The system architecture and design decisions were developed through extensive discussions with:

- **Gemini (Google AI)**: For architecture patterns, evaluation strategies, and validation methodologies
- **ChatGPT (OpenAI)**: For rubric design, scoring schema refinement, and best practices in LLM evaluation

### Transparency Commitment

We believe in transparency in AI-assisted development. All code has been:
- Reviewed and validated by human developers
- Tested against real-world scenarios
- Documented with clear explanations
- Open-sourced for community scrutiny

---

## 📸 Screenshots

### Evaluation Run Output

<!-- TODO: Add screenshot of run.py execution -->
![Evaluation Run](docs/screenshots/evaluation_run.png)
*Figure: Pointwise evaluation execution showing criteria scores and overall results*

### Validation Report

<!-- TODO: Add screenshot of validate.py execution -->
![Validation Report](docs/screenshots/validation_report.png)
*Figure: Judge validation report showing agreement statistics across criteria*

### Adversarial Test Results

<!-- TODO: Add screenshot of adversarial validation -->
![Adversarial Results](docs/screenshots/adversarial_results.png)
*Figure: Adversarial test results showing judge robustness against confidently-stated falsehoods*

### JSON Report Structure

<!-- TODO: Add screenshot of report JSON structure -->
![JSON Report](docs/screenshots/json_report.png)
*Figure: Generated JSON report showing detailed verdict structure*

### Log File Example

<!-- TODO: Add screenshot of JSONL log file -->
![Log File](docs/screenshots/log_file.png)
*Figure: JSONL log file showing judge invocation details*

---

## 🎓 Assumptions & Design Decisions

### Core Assumptions

1. **Groq API Reliability**: System assumes Groq API is available and responsive
2. **Model Consistency**: Judge model behavior is assumed consistent across evaluations
3. **Rubric Universality**: The 3-criteria rubric is assumed applicable to most text generation tasks
4. **Human Label Quality**: Gold standard cases assume accurate human labeling
5. **Score Linearity**: Assumes 1-5 scale provides meaningful granularity

### Design Decisions

#### Why Groq?
- **Speed**: Fast inference for rapid evaluation
- **Cost**: Cost-effective for large-scale evaluation
- **Model Quality**: Llama 3.1 provides strong performance
- **API Stability**: Reliable production-ready API

#### Why 1-5 Scale?
- **Standard Practice**: Widely used in LLM evaluation research
- **Sufficient Granularity**: 5 points provide meaningful differentiation
- **Interpretability**: Clear semantic meaning for each level
- **Compatibility**: Works well with human evaluators

#### Why Separate Validation?
- **Trust Building**: Independent validation builds confidence in judge
- **Bias Detection**: Identifies systematic judge biases
- **Continuous Improvement**: Enables judge refinement over time
- **Research Value**: Provides metrics for judge reliability

#### Why JSONL Logging?
- **Crash Safety**: Append-only writes prevent data loss
- **Stream Processing**: Easy to process line-by-line
- **Debugging**: Complete record of all interactions
- **Audit Trail**: Full reproducibility of evaluations

#### Why Adversarial Testing?
- **Real-World Robustness**: Tests against actual attack patterns
- **No New Infrastructure**: Uses existing validation pipeline
- **Clear Metrics**: Direct measurement of judge vulnerability
- **Safety Critical**: Prevents validation of harmful misinformation

### Known Limitations

1. **Position Bias**: Pairwise mode may still exhibit position bias despite swap testing
2. **Criteria Coverage**: Current 3-criteria rubric may not cover all use cases
3. **Model Dependency**: Judge quality depends on underlying LLM capabilities
4. **Context Window**: Long inputs may exceed model context limits
5. **Language Support**: Primarily optimized for English text
6. **Adversarial Coverage**: Current adversarial suite may not cover all attack vectors

---

## 🚧 Future Enhancements

### Planned Features

- [ ] **Custom Criteria Support**: Allow user-defined evaluation criteria
- [ ] **Multi-Model Comparison**: Compare outputs from multiple models simultaneously
- [ ] **Statistical Significance Testing**: Add confidence intervals and p-values
- [ ] **Web Dashboard**: Interactive UI for viewing results
- [ ] **Batch Processing**: Parallel evaluation for large suites
- [ ] **Export Formats**: CSV, HTML, and PDF report generation
- [ ] **Custom Rubrics**: Per-suite rubric configuration
- [ ] **Trend Analysis**: Track judge performance over time
- [ ] **API Integration**: REST API for programmatic access
- [ ] **Language Support**: Multi-language evaluation capabilities
- [ ] **Expanded Adversarial Suite**: More diverse adversarial attack patterns
- [ ] **Adversarial Generation**: Automated generation of adversarial test cases

### Research Directions

- **Adaptive Tolerance**: Dynamic tolerance based on criterion difficulty
- **Ensemble Judging**: Multiple judge models with voting
- **Few-Shot Learning**: Improve judge with examples
- **Calibration**: Score calibration across different domains
- **Explainability**: Enhanced rationale generation
- **Adversarial Defense**: Techniques to improve judge robustness

---

## 📚 Additional Resources

### Documentation

- **Groq API Docs**: [console.groq.com/docs](https://console.groq.com/docs)
- **Pydantic Docs**: [docs.pydantic.dev](https://docs.pydantic.dev)
- **LLM Evaluation Research**: See academic papers on automated evaluation

### Related Projects

- **OpenAI Evals**: Framework for evaluating LLMs
- **Promptfoo**: Tool for testing LLM prompts
- **RAGAS**: Framework for evaluating RAG applications

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests (when available)
python -m pytest tests/

# Format code
black .
```

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👨‍💻 Author

**Shashank** - [GitHub](https://github.com/shashank601)

---

## 🙏 Acknowledgments

- **Groq** for providing fast, reliable LLM inference
- **Devin AI** for assistance in code generation
- **Gemini & ChatGPT** for architecture design discussions
- The LLM evaluation research community for foundational work

---

<div align="center">

**Built with ❤️ for reliable LLM evaluation**

[⬆ Back to Top](#-llm-as-a-judge-evaluation-framework)

</div>
