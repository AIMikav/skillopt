# SkillOpt - Skill Optimizer

SkillOpt optimizes Claude Agent Skills using DSPy's GEPA optimizer and best practices analysis.

## Quick Start

```bash
export OPENAI_API_KEY=your-api-key

# Analyze a skill
uv run python main.py analyze <skill_directory>

# Static-only optimization
uv run python main.py optimize <skill_directory> -o <output_directory>

# Eval-based optimization (recommended)
uv run python main.py optimize-evals <skill_directory> --evals <evals.json>
uv run python main.py optimize-evals <skill_directory> --generate-evals

# Variance benchmark
uv run python main.py benchmark <skill_directory>
```

The Jupyter notebook in `notebooks/` provides an interactive walkthrough.

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

- **Static-only** (`main.py optimize`) — composite metric: filler removal, conciseness, code-block preservation, structure
- **Eval-based** (`main.py optimize-evals`) — 40% static + 60% LLM-as-judge assertion pass rate. Evals can be hand-written or auto-generated.

Run any subcommand with `--help` for full CLI options.
