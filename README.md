# SkillOpt

SkillOpt optimizes Claude Agent Skills using GEPA's `optimize_anything` API. It analyzes skills against best practices, removes filler and verbose explanations, and consolidates redundant content while preserving code blocks and structure. An evaluator function scores each candidate, and GEPA's reflection-driven search evolves the skill toward the optimum.

## Installation

```bash
uv sync
```

## Usage

### API configuration

The scripts work with any OpenAI-compatible API. Pass credentials via CLI flags or environment variables:

```bash
# Option 1: OpenAI
uv run python main.py optimize-evals <skill> --generate-evals \
    --api-key $OPENAI_API_KEY --model openai/gpt-4o

# Option 2: Local Ollama
uv run python main.py optimize-evals <skill> --generate-evals \
    --model ollama/gemma3:4b --api-key ollama --api-base http://localhost:11434/v1

# Option 3: Google Gemini
uv run python main.py optimize-evals <skill> --generate-evals \
    --model gemini/gemini-2.0-flash --api-key $GEMINI_API_KEY \
    --api-base https://generativelanguage.googleapis.com/v1beta/openai/

# Option 4: Environment variables (also loaded from .env)
export OPENAI_API_KEY=your-key        # or GEMINI_API_KEY or API_KEY
export OPENAI_API_BASE=http://...     # optional, for non-OpenAI endpoints
```

### Commands

All commands go through `main.py`:

```bash
# Analyze a skill without optimizing
uv run python main.py analyze <skill_directory>

# Static-only optimization
uv run python main.py optimize <skill_directory> -o <output_directory>

# Eval-based optimization (recommended)
uv run python main.py optimize-evals <skill_directory> --evals <evals.json>
uv run python main.py optimize-evals <skill_directory> --generate-evals

# Variance benchmark
uv run python main.py benchmark <skill_directory> [--num-runs 10]
```

### Common flags

| Flag | Description |
|------|-------------|
| `--model <provider/model>` | LLM model in litellm format (default: `openai/gpt-4o`) |
| `--api-key <key>` | API key (fallback: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `API_KEY` env vars) |
| `--api-base <url>` | Base URL for OpenAI-compatible endpoints |
| `--max-evals <n>` | Maximum GEPA iterations (default: 10) |
| `-o <dir>` | Output directory |
| `-q` | Quiet mode |

Each subcommand documents its own flags:

```bash
uv run python main.py optimize --help
uv run python main.py optimize-evals --help
```

## How It Works

1. **Parse** -- Load skill directory (SKILL.md + references) and extract content
2. **Analyze** -- Score against Claude Agent Skills best practices
3. **Optimize** -- `optimize_anything` evolves the skill content over multiple iterations, scored by the evaluator
4. **Validate** -- (eval-based only) LLM-as-judge checks the optimized skill against all assertions
5. **Save** -- Output optimized SKILL.md and benchmark results

The skill content itself is the seed candidate. GEPA proposes mutations, the evaluator scores them and returns structured feedback, and GEPA's reflection LM uses that feedback to guide the next proposal.

### Optimization modes

**Static** (`optimize`) -- Evaluator scores on filler phrase removal (25%), conciseness (20%), code-block preservation (25%), structure (15%), and verbose explanation removal (15%).

**Eval-based** (`optimize-evals`) -- Combines 40% static analysis with 60% LLM-as-judge assertion pass rate. The judge evaluates whether the optimized skill contains enough information for an agent to satisfy each assertion. Assertions can be provided in the evals file or auto-generated (3-6 per test case).

### Variance benchmark

The `benchmark` subcommand tests analyzer determinism by running multiple analysis passes and reporting score stability.

## Project Structure

```
main.py                  # CLI entry point (analyze, optimize, optimize-evals, benchmark)
skillopt/                # Core library (parser, analyzer)
scripts/                 # Optimization and benchmark scripts
examples/                # Example skills and evals
```

## License

MIT
