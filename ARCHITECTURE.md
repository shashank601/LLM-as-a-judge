# 🏗️ LLM-as-a-Judge — Architecture Diagram

> Visual reference for the **two-level evaluation system**. Level 1 is the automated LLM Judge; Level 2 is the Judge Validator that audits Level 1 against human-labeled ground truth.

---

## 🗺️ High-Level System Overview

```mermaid
graph TD
    subgraph SYSTEM["🎯 LLM-as-a-Judge System"]
        direction TB

        subgraph ENTRY["📥 Entry Points"]
            RUN["run.py\n(Pointwise Eval)"]
            VAL["validate.py\n(Judge Validation)"]
            CMP["compare.py\n(Pairwise Comparison)"]
        end

        subgraph CORE["⚙️ Core Logic"]
            JUDGE["judge.py\n(Prompt Builder + API Call)"]
            PARSER["parser.py\n(JSON Response Parser)"]
            PIPELINE["pipeline.py\n(Suite Loader)"]
            AGGREGATE["aggregate.py\n(Score Aggregator)"]
            LOGGER["logger.py\n(JSONL Writer)"]
        end

        subgraph DATA["💾 Data Layer"]
            SCHEMAS["schemas.py\n(Pydantic Models)"]
            RUBRIC["rubric.py\n(Scoring Rubric)"]
            SUITES["suites/\n(JSON Test Suites)"]
        end

        subgraph OUTPUT["📤 Output"]
            REPORTS["reports/\n(JSON Reports)"]
            LOGS["logs/\n(JSONL Logs)"]
        end
    end

    RUN --> PIPELINE
    VAL --> PIPELINE
    CMP --> PIPELINE

    PIPELINE --> JUDGE
    JUDGE --> RUBRIC
    JUDGE --> SCHEMAS
    JUDGE --> PARSER
    PARSER --> SCHEMAS
    JUDGE --> LOGGER
    LOGGER --> LOGS
    JUDGE --> AGGREGATE
    AGGREGATE --> REPORTS
    SUITES --> PIPELINE
```

---

## 🔵 Level 1 — The LLM Judge

> **Purpose**: Evaluate a single model output (or two, in pairwise mode) against a rubric and produce a structured `Verdict`.

```mermaid
flowchart LR
    A(["📄 TestCase\n(Input + Model Output\n+ Criteria)"])
    B["🔨 Prompt Builder\njudge.py"]
    C["☁️ Groq API\nLlama 3.1 8B Instant"]
    D["🔍 Response Parser\nparser.py"]
    E["✅ Schema Validator\nschemas.py"]
    F(["📊 Verdict\n(Scores + Rationale\n+ Token Counts)"])

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F

    subgraph RETRY["🔄 Retry Loop (on parse failure)"]
        B
        C
        D
    end
```

### Level 1 Key Components

| Module | Role |
|---|---|
| `judge.py` | Builds prompt, calls Groq API, orchestrates retry logic |
| `rubric.py` | Defines the 1–5 scoring rubric per criterion |
| `parser.py` | Extracts structured JSON from raw LLM text response |
| `schemas.py` | Validates parsed output via Pydantic (`Verdict`, `CriterionScore`) |
| `logger.py` | Appends each judge invocation to a `.jsonl` log file |

### Pointwise vs. Pairwise Mode

```mermaid
flowchart TD
    TC["TestCase"] --> MODE{{"Evaluation\nMode?"}}
    MODE -- "Pointwise" --> PW["Score model_output\nagainst criteria\n→ overall_score 1-5"]
    MODE -- "Pairwise" --> PP["Score model_output A\nand model_output B\n→ a_score, b_score\n→ winner: A / B / tie"]
    PW --> VRD["Verdict"]
    PP --> VRD
```

---

## 🟠 Level 2 — The Judge Validator

> **Purpose**: Audit Level 1's reliability by running it on cases where **human labels are already known**, then measuring agreement.

```mermaid
flowchart LR
    G(["📋 GoldTestCase\n(with human_scores\n/ human_winner)"])
    H["🔒 Label Masking\n(human labels hidden\nfrom judge)"]
    I["🔵 Level 1 Judge\n(runs normally)"]
    J["⚖️ Comparator\nvalidate.py"]
    K["📈 Validation Report\n(agreement %, failures)"]

    G --> H
    H --> I
    I --> J
    G --> J
    J --> K

    subgraph ADV["🛡️ Adversarial Mode (optional)"]
        L["Response B = Confidently\nIncorrect Answer"]
        L --> I
    end
```

### Level 2 Key Components

| Module / File | Role |
|---|---|
| `validate.py` | Entry point; loads gold suite, calls judge, computes agreement |
| `schemas.py` | `GoldTestCase` model with `human_scores`, `human_winner` fields |
| `pipeline.py` | Loads and parses `gold_pointwise.json` / `adversarial_suite.json` |
| `aggregate.py` | Accumulates per-criterion agreement statistics |

### Validation Metrics

```mermaid
flowchart TD
    VP["Verdict from Judge"]
    HV["Human Labels\n(GoldTestCase)"]
    CMP2["compare\ncriterion by criterion"]
    VP --> CMP2
    HV --> CMP2
    CMP2 --> EXACT["Exact Match\nscore == human_score"]
    CMP2 --> TOL["Tolerance Match\nabsolute diff <= 0.5"]
    CMP2 --> WIN["Winner Agreement\nA / B / tie"]
    EXACT --> REPORT2["📊 Validation Report\n• % agreement per criterion\n• Overall agreement\n• Adversarial failure rate"]
    TOL --> REPORT2
    WIN --> REPORT2
```

---

## 🔄 End-to-End Data Flow

```mermaid
sequenceDiagram
    autonumber
    participant U as User / CLI
    participant PL as pipeline.py
    participant JD as judge.py
    participant API as Groq API
    participant PR as parser.py
    participant SC as schemas.py
    participant LG as logger.py
    participant AG as aggregate.py

    U->>PL: Load suite JSON
    PL->>JD: Pass TestCase list
    loop For each TestCase
        JD->>JD: Build prompt (rubric.py)
        JD->>API: POST /chat/completions
        API-->>JD: Raw text response
        JD->>PR: Parse JSON from response
        PR-->>JD: Dict or ParseError
        alt Parse success
            JD->>SC: Validate → Verdict
            SC-->>JD: Validated Verdict
        else Parse failure (retry up to 3x)
            JD->>API: Retry with correction hint
        end
        JD->>LG: Append to .jsonl log
        JD->>AG: Accumulate scores
    end
    AG-->>U: Final Report (reports/*.json)
    LG-->>U: Run Log (logs/*.jsonl)
```

---

## 📦 Module Dependency Map

```mermaid
graph LR
    run.py --> pipeline.py
    validate.py --> pipeline.py
    compare.py --> pipeline.py

    pipeline.py --> schemas.py
    pipeline.py --> judge.py

    judge.py --> rubric.py
    judge.py --> parser.py
    judge.py --> logger.py
    judge.py --> aggregate.py
    judge.py --> schemas.py

    parser.py --> schemas.py
```

---

## 🗂️ Directory Structure

```
nexpro/
├── run.py              ← Level 1 entry: pointwise evaluation
├── validate.py         ← Level 2 entry: judge validation
├── compare.py          ← Level 1 entry: pairwise comparison
│
├── core/
│   ├── judge.py        ← [L1] Prompt builder + Groq API caller
│   ├── parser.py       ← [L1] LLM response → structured dict
│   ├── pipeline.py     ← [L1/L2] Suite loader
│   ├── rubric.py       ← [L1] Scoring rubric definitions
│   ├── schemas.py      ← [L1/L2] Pydantic models
│   ├── logger.py       ← [L1] JSONL interaction logger
│   ├── aggregate.py    ← [L1/L2] Score aggregation
│   └── replay.py       ← Replay logged runs
│
├── suites/
│   ├── judge_suite.json          ← Standard pointwise test cases
│   ├── gold_pointwise.json       ← Human-labeled pointwise cases
│   ├── gold_pairwise.json        ← Human-labeled pairwise cases
│   └── adversarial_suite.json    ← Adversarial (confidently wrong) cases
│
├── reports/            ← JSON evaluation reports (auto-generated)
├── logs/               ← JSONL judge invocation logs (auto-generated)
└── .env                ← GROQ_API_KEY
```

---

## 🧩 Schema Relationships

```mermaid
classDiagram
    class TestCase {
        +str id
        +str input
        +str system_prompt
        +str model_output
        +str model_output_b
        +str expected_output
        +list criteria
    }

    class GoldTestCase {
        +str id
        +str input
        +str system_prompt
        +str model_output
        +str model_output_b
        +list criteria
        +dict human_scores
        +float human_overall_score
        +str human_winner
    }

    class Verdict {
        +str case_id
        +list criteria
        +float overall_score
        +float overall_score_b
        +str overall_rationale
        +str winner
        +str judge_model
        +int input_tokens
        +int output_tokens
    }

    class CriterionScore {
        +str name
        +int score
        +str rationale
    }

    class PairwiseCriterionScore {
        +str name
        +int a_score
        +int b_score
        +str rationale
    }

    TestCase --> Verdict : evaluated by judge
    GoldTestCase --> TestCase : extends (labels hidden)
    Verdict --> CriterionScore : contains (pointwise)
    Verdict --> PairwiseCriterionScore : contains (pairwise)
    GoldTestCase --> Verdict : compared for validation
```

---

> **Legend**:
> - 🔵 **Level 1** — Judge: automated LLM scoring of model outputs
> - 🟠 **Level 2** — Validator: human-agreement audit of the judge itself
> - 🛡️ **Adversarial** — Special Level 2 mode testing judge robustness
