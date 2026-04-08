# SkillOpt - Skill Optimizer

SkillOpt optimizes Claude Agent Skills using DSPy's GEPA optimizer and official best practices analysis.

## Quick Start

Open `gepa_skill_optimization.ipynb` and run the cells to:

1. Load a skill from `examples/`
2. Analyze against best practices
3. Run GEPA optimization with GPT-4o
4. Save optimized skill

## Usage

```python
from skillopt import SkillParser, SkillAnalyzer
import dspy

# Parse skill
parser = SkillParser()
skill = parser.parse_directory("examples/Bad_Kubernetes_Helper_Skill")

# Analyze against best practices
analyzer = SkillAnalyzer()
report = analyzer.analyze(skill)
print(f"Score: {report.score}/100")
print(f"Issues: {len(report.issues)}")

# Configure DSPy and run GEPA (see notebook for full example)
lm = dspy.LM("openai/gpt-4o", api_key="your-key")
dspy.configure(lm=lm)
```

## Best Practices Checks

| Category | Checks |
|----------|--------|
| **Structure** | SKILL.md < 500 lines, one-level references, TOC for long files |
| **Conciseness** | Remove filler phrases, simplify verbose explanations |
| **Frontmatter** | Valid name (lowercase, hyphens), description with "Use when..." |
| **Workflows** | Clear steps with checklists, validation feedback loops |
| **Terminology** | Consistent terms throughout skill |

## Training Examples

Best practices examples are in `examples/training_examples.json`:
- 30 bad/good example pairs from official documentation
- 13 filler phrases to remove
- 10 verbose patterns to simplify

## Files

| File | Purpose |
|------|---------|
| `gepa_skill_optimization.ipynb` | Main notebook for GEPA optimization |
| `examples/training_examples.json` | Best practices training data |
| `examples/Bad_Kubernetes_Helper_Skill/` | Example bad skill (input) |
| `examples/Bad_Kubernetes_Helper_Skill_GEPA_Optimized/` | Optimized output |
| `skillopt/` | Core library (parser, analyzer) |
