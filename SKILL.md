---
name: skill-optimizer
description: Use when the user wants to analyze, optimize, or benchmark a Claude Agent Skill using GEPA. Handles analyzing skills against best practices, running static or eval-based optimization, generating evals and assertions, and comparing before/after results.
---

# Skill Optimizer

Optimize Claude Agent Skills using DSPy's GEPA (Greedy Evolutionary Prompt Adaptation) algorithm. This skill wraps the SkillOpt CLI to analyze, optimize, and benchmark skills.

## Prerequisites

- `OPENAI_API_KEY` must be set in the environment or `.env`
- Dependencies installed via `uv sync`
- The skill to optimize must be a directory containing a `SKILL.md`

## Workflow

When the user asks to optimize a skill, follow these steps:

### Step 1: Identify the target skill

- [ ] Confirm the path to the skill directory (must contain a `SKILL.md`)
- [ ] Check if an `evals.json` file exists alongside or within the skill directory
- [ ] Ask the user which optimization mode they want if not clear:
  - **Analyze only** — score against best practices, no changes
  - **Static optimization** — optimize using filler/conciseness/structure metric
  - **Eval-based optimization** (recommended) — optimize using evals + LLM-as-judge assertions

### Step 2: Analyze the skill

Run analysis to understand current quality:

```bash
python main.py analyze <skill_directory>
```

Report the score, issue counts, and top issues to the user before proceeding.

### Step 3: Optimize

Choose the appropriate command based on the user's preference:

**Static-only:**

```bash
python main.py optimize <skill_directory> -o <output_directory>
```

**Eval-based with existing evals:**

```bash
python main.py optimize-evals <skill_directory> --evals <evals_json_path>
```

**Eval-based with auto-generated evals:**

```bash
python main.py optimize-evals <skill_directory> --generate-evals
```

**Dry run (generate evals/assertions without optimizing):**

```bash
python main.py optimize-evals <skill_directory> --evals <evals_json_path> --dry-run
```

### Step 4: Review results

After optimization completes:

- [ ] Read the optimized `SKILL.md` from the output directory
- [ ] Read `benchmark.json` for scores and assertion verdicts (eval-based only)
- [ ] Compare original vs optimized: character count, code blocks, filler phrases
- [ ] Present a summary to the user with before/after metrics

### Step 5: Iterate (optional)

If the user is not satisfied:

- [ ] Adjust `--max-evals` to allow more GEPA iterations
- [ ] Provide hand-written evals for tighter control over what the skill must handle
- [ ] Try a different `--model`

## Evals format

If the user wants to provide custom evals, they should create a JSON file:

```json
{
  "skill_name": "<name>",
  "evals": [
    {
      "id": 1,
      "name": "short-descriptive-name",
      "prompt": "A realistic user prompt that exercises this skill",
      "expected_output": "Description of what a good response looks like",
      "expectations": [
        "Specific, verifiable assertion about the response",
        "Another verifiable assertion"
      ]
    }
  ]
}
```

The `expectations` field is optional. If omitted, assertions are auto-generated (3-6 per case).

Good assertions are objective and verifiable:
- "The response includes the kubectl logs command"
- "The response explains at least two common causes"

Bad assertions are subjective:
- "The response is helpful"
- "The output is well-formatted"

## CLI reference

```bash
python main.py analyze <skill_directory>
python main.py optimize <skill_directory> [-o <output>] [--model <model>] [--max-evals <n>]
python main.py optimize-evals <skill_directory> [--evals <path>] [--generate-evals] [--dry-run] [--model <model>] [--max-evals <n>]
python main.py benchmark <skill_directory> [--num-runs <n>]
```

Run any subcommand with `--help` for full details.

## Scoring

### Static metric

Scores candidates on: filler phrase removal, conciseness (target 30-70% reduction), code-block preservation, and structural integrity (frontmatter, sections).

### Eval-based metric

Combines 40% static analysis with 60% LLM-as-judge assertion pass rate. The judge evaluates whether the optimized skill contains enough information for an agent to satisfy each assertion.
