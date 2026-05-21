# SkillOpt - Skill Optimizer

SkillOpt optimizes Claude Agent Skills using GEPA's `optimize_anything` API and best practices analysis.

## Quick Start

```bash
# With OpenAI
uv run python main.py optimize-evals <skill_directory> --generate-evals \
    --api-key $OPENAI_API_KEY --model openai/gpt-4o

# With local Ollama
uv run python main.py optimize-evals <skill_directory> --generate-evals \
    --model ollama/gemma3:4b --api-key ollama --api-base http://localhost:11434/v1

# Analyze a skill
uv run python main.py analyze <skill_directory>

# Static-only optimization
uv run python main.py optimize <skill_directory> -o <output_directory>

# Variance benchmark
uv run python main.py benchmark <skill_directory>
```

API key is resolved from `--api-key` flag, or env vars: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `API_KEY` (also loaded from `.env`).

## Library usage

```python
from skillopt import SkillParser, SkillAnalyzer

parser = SkillParser()
skill = parser.parse_directory("<skill_directory>")

analyzer = SkillAnalyzer()
report = analyzer.analyze(skill)
print(f"Score: {report.score}/100")
print(f"Issues: {len(report.issues)}")
```

## Best Practices Checks

| Category | Checks |
|----------|--------|
| **Structure** | SKILL.md < 500 lines, one-level references, TOC for long files |
| **Conciseness** | Remove filler phrases, simplify verbose explanations |
| **Frontmatter** | Valid name (lowercase, hyphens), description with "Use when..." |
| **Workflows** | Clear steps with checklists, validation feedback loops |
| **Terminology** | Consistent terms throughout skill |

## Optimization modes

- **Static-only** (`main.py optimize`) -- evaluator scores filler removal, conciseness, code-block preservation, structure
- **Eval-based** (`main.py optimize-evals`) -- 40% static + 60% LLM-as-judge assertion pass rate. Evals can be hand-written or auto-generated.

Both modes use `gepa.optimize_anything` with the skill content as the seed candidate. GEPA evolves the text via reflection-driven search, guided by evaluator feedback.

Run any subcommand with `--help` for full CLI options.
