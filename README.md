# SkillOpt

SkillOpt optimizes Claude Agent Skills using DSPy's GEPA (Greedy Evolutionary Prompt Adaptation) algorithm. It analyzes skill files against best practices, removes filler phrases and verbose explanations, and consolidates redundant commands while preserving essential code blocks. The optimizer is trained on 30 curated bad/good example pairs covering conciseness, structure, and formatting patterns from official documentation. This achieves 50-70% token reduction without loss of functionality.

## Installation

```bash
uv sync
```

## Usage

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=your-api-key

# Analyze skill (dry run)
uv run python optimize_skill.py <skill_directory> --dry-run

# Optimize skill
uv run python optimize_skill.py <skill_directory> -o <output_directory>
```

### Example

```bash
uv run python optimize_skill.py examples/example_1/Bad_Kubernetes_Helper_Skill -o examples/example_1/Optimized_Skill
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `skill_path` | required | Path to skill directory |
| `-o, --output` | `<skill>_GEPA_Optimized` | Output directory |
| `--model` | `openai/gpt-4o` | OpenAI model to use |
| `--max-evals` | `10` | Maximum GEPA evaluations |
| `--content-limit` | `8000` | Character limit for training |
| `--dry-run` | `false` | Analyze without optimizing |
| `-q, --quiet` | `false` | Suppress output |

## How It Works

1. **Parse** - Load skill directory and extract content
2. **Analyze** - Check against Claude Agent Skills best practices
3. **Optimize** - Use GEPA to evolve better prompts
4. **Save** - Output optimized skill

### Training Set

- 30 curated bad/good example pairs from Claude Agent Skills best practices
- Covers 10 categories: conciseness, frontmatter, naming, structure, content, scripts, terminology, workflows, templates, paths
- Includes 13 filler phrases to remove and 10 verbose patterns to simplify

### Optimization Metric

| Component | Weight | Description |
|-----------|--------|-------------|
| Filler removal | 25% | Remove "make sure to", "ensure that", etc. |
| Code preservation | 25% | Keep code blocks intact |
| Conciseness | 20% | Target 40-70% reduction |
| Structure | 15% | Preserve frontmatter and sections |
| Verbose removal | 15% | Remove acronym expansions |

## Project Structure

```
optimize_skill.py           # CLI script
skillopt/
├── skill_parser.py         # Parse skill directories
├── skill_analyzer.py       # Analyze against best practices
└── prompt_parser.py        # Parse prompt files
examples/
├── example_1/              # Example skill
└── training_examples.json  # Training data
```

## License

MIT
