# SkillOpt

SkillOpt optimizes Claude Agent Skills using DSPy's GEPA (Greedy Evolutionary Prompt Adaptation) algorithm. It analyzes skills against best practices, removes filler and verbose explanations, and consolidates redundant content while preserving code blocks and structure. Training data with bad/good example pairs teaches the optimizer what to fix.

## Installation

```bash
uv sync
```

## Usage

Set your OpenAI API key before running:

```bash
export OPENAI_API_KEY=your-api-key

# Optional: Set your API base to use with other providers (e.g. vLLM, Ollama, llama.cpp)
# Specify the model name with --model openai/<model-name> when running
# export OPENAI_API_BASE=http://localhost:11434/v1
```

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

### Interactive notebooks

Two Jupyter notebooks in `notebooks/` provide step-by-step walkthroughs:

- **Static-only optimization** — uses the composite static metric (filler, conciseness, code blocks, structure)
- **Eval-based optimization** — adds LLM-as-judge assertion scoring on top of static analysis

Each subcommand documents its own flags:

```bash
uv run python main.py optimize --help
uv run python main.py optimize-evals --help
```

## How It Works

1. **Parse** — Load skill directory (SKILL.md + references) and extract content
2. **Analyze** — Score against Claude Agent Skills best practices
3. **Optimize** — GEPA evolves prompt instructions over multiple iterations, scored by the chosen metric
4. **Validate** — (eval-based only) LLM-as-judge checks the optimized skill against all assertions
5. **Save** — Output optimized SKILL.md and benchmark results

### Eval-based metric

When using eval-based optimization, GEPA scores each candidate with:

- **40% static analysis** — filler removal, conciseness, code-block preservation, structure
- **60% assertion satisfaction** — an LLM judge evaluates whether the optimized skill enables handling every test case

Assertions can be provided in the evals file or auto-generated (3-6 per test case, filtered for objectivity).

### Variance benchmark

The `benchmark` subcommand tests analyzer determinism by running multiple analysis passes and reporting score stability.

## Project Structure

```
main.py                  # CLI entry point (analyze, optimize, optimize-evals, benchmark)
skillopt/                # Core library (parser, analyzer)
scripts/                 # Optimization and benchmark scripts
notebooks/               # Interactive Jupyter walkthroughs
examples/                # Example skills, evals, and training data
```

## License

MIT
