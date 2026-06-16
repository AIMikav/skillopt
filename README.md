# SkillOpt

SkillOpt optimizes Claude Agent Skills using GEPA's `optimize_anything` API. It can optimize an existing skill or create one from scratch, grounded in standard benchmark task data.

## Installation

```bash
uv sync

# For SWE-bench and SearchQA support
uv pip install datasets
```

## API configuration

Copy `.env.example` to `.env` and set your credentials:

```bash
cp .env.example .env
```

| Provider | `.env` keys needed |
|---|---|
| OpenAI | `OPENAI_API_KEY` |
| Google Gemini | `GEMINI_API_KEY` + `OPENAI_API_BASE` |
| Ollama (local) | `API_KEY=ollama` + `OPENAI_API_BASE=http://localhost:11434/v1` |
| Any OpenAI-compatible | `API_KEY` + `OPENAI_API_BASE` |

Key resolution order: `OPENAI_API_KEY` → `GEMINI_API_KEY` → `API_KEY`. Flags `--api-key` and `--api-base` take precedence over `.env`.

## Commands

### Analyze
Score an existing skill against best practices without modifying it.
```bash
uv run python main.py analyze <skill_directory>
```

### Static optimization
Optimize using rule-based scoring only — no LLM judge or eval cases required.
```bash
uv run python main.py optimize <skill_directory> --model <model> --api-key <key>
```

### Eval-based optimization
Optimize with a hybrid evaluator: 40% static rules + 60% LLM-as-judge assertion pass rate.
```bash
# Hand-written evals
uv run python main.py optimize-evals <skill_directory> --evals <evals.json>

# Auto-generate evals from the skill content
uv run python main.py optimize-evals <skill_directory> --generate-evals

# Use a standard benchmark as the eval source
uv run python main.py optimize-evals <skill_directory> --benchmark tau-bench --benchmark-split airline
uv run python main.py optimize-evals <skill_directory> --benchmark swe-bench --benchmark-variant swe-bench-verified
uv run python main.py optimize-evals <skill_directory> --benchmark searchqa
```

### Create a skill from scratch
No existing SKILL.md required — GEPA generates the first candidate from the benchmark task context.
```bash
uv run python main.py optimize-evals <new_directory> --from-scratch --benchmark tau-bench --benchmark-split airline
uv run python main.py optimize-evals <new_directory> --from-scratch --benchmark searchqa
```

### Convert any HuggingFace dataset to eval format
Map any HuggingFace dataset fields to the SkillOpt eval schema. Output can be passed directly to `optimize-evals`.
```bash
uv run python main.py convert <dataset_id> \
    --prompt-field <field> \
    [--context-field <field>] \
    [--answer-field <field>] \
    [--split <split>] [--n <n>] [--config <config>] \
    -o evals.json
```

Dot notation is supported for nested fields: `--prompt-field answers.text`.

### Dry run
Load and generate evals without running optimization — useful for inspecting eval cases first.
```bash
uv run python main.py optimize-evals <skill_directory> --benchmark tau-bench --dry-run
```

## Common flags

| Flag | Description |
|---|---|
| `--model <provider/model>` | LLM in litellm format (default: `openai/gpt-4o`) |
| `--api-key <key>` | API key (fallback: env vars) |
| `--api-base <url>` | Base URL for OpenAI-compatible endpoints |
| `--max-evals <n>` | Max GEPA iterations (default: 10) |
| `--from-scratch` | Create a new skill instead of optimizing an existing one |
| `--dry-run` | Phase 1 only — load/generate evals, skip optimization |
| `-o <dir>` | Output directory (default: `output/<skill-name>-<timestamp>/`) |

## Benchmark sources

| `--benchmark` | `--benchmark-split` / `--benchmark-variant` | Source |
|---|---|---|
| `tau-bench` | `airline`, `retail` | GitHub (auto-fetched) |
| `swe-bench` | `swe-bench`, `swe-bench-verified`, `swe-bench-lite` | HuggingFace |
| `searchqa` | `train`, `validation` | HuggingFace |

## Output structure

Every run writes to `output/<skill-name>-<timestamp>/`:

```
output/<skill-name>-<timestamp>/
├── SKILL.md                    optimized or generated skill
├── benchmark.json              scores and assertion verdicts
├── evals_with_assertions.json  eval cases used
└── trajectory/
    ├── trajectory.jsonl        live per-iteration log
    ├── trajectory_summary.json post-run summary
    └── candidates/             every proposed variant
```

Watch a run live: `tail -f output/<run>/trajectory/trajectory.jsonl`

## Library usage

```python
from skillopt import SkillParser, SkillAnalyzer, load_benchmark

# Analyze
skill = SkillParser().parse_directory("<skill_directory>")
report = SkillAnalyzer().analyze(skill)
print(f"Score: {report.score}/100")

# Load benchmark evals
evals = load_benchmark("tau-bench", split="airline", n=3)
evals = load_benchmark("swe-bench", split="test", variant="swe-bench-verified", n=3)
evals = load_benchmark("searchqa", split="validation", n=3)
```

## Project structure

```
main.py                  # CLI (analyze, optimize, optimize-evals, convert)
skillopt/                # Core library
  skill_parser.py        # Parses SKILL.md + referenced files
  skill_analyzer.py      # Scores skills against best-practice rules
  trajectory.py          # Per-iteration candidate logging
  benchmarks/            # Benchmark adapters (tau_bench, swe_bench, searchqa)
scripts/                 # optimize_skill.py, optimize_skill_with_evals.py, convert_benchmark.py
output/                  # Generated run outputs (gitignored)
```

## License

Apache 2.0 — see [LICENSE](LICENSE).
