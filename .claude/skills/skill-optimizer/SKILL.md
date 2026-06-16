---
name: skill-optimizer
description: Use when the user wants to analyze, optimize, or create a Claude Agent Skill using GEPA. Handles best practices analysis, static or eval-based optimization, benchmark-driven optimization (TAU-bench, SWE-bench, SearchQA), creating skills from scratch, converting custom HuggingFace datasets to eval format, and before/after comparison.
argument-hint: <skill-directory> [--benchmark <name>] [--from-scratch] [--generate-evals] [--evals <evals.json>] [--mode analyze|optimize|optimize-evals|convert]
allowed-tools: Bash Read Grep Glob
---

# Skill Optimizer

Optimize or create the Claude Agent Skill using GEPA's optimize_anything API.

## Step 1: Parse arguments

Parse `$ARGUMENTS` for:
- **skill directory** (required for analyze/optimize) — path to directory containing a SKILL.md
- **--mode** (optional) — one of `analyze`, `optimize`, `optimize-evals`, `convert` (default: ask)
- **--evals <path>** (optional) — path to a hand-written evals.json
- **--generate-evals** (optional) — auto-generate evals from skill content
- **--benchmark <name>** (optional) — `tau-bench`, `swe-bench`, or `searchqa`
- **--benchmark-split <split>** (optional) — e.g. `airline`, `retail`, `validation`
- **--benchmark-variant <variant>** (optional) — e.g. `swe-bench-verified`
- **--from-scratch** (optional) — create a new skill instead of optimizing an existing one
- **-o <path>** (optional) — output directory

If mode is not specified, ask the user:
1. **Analyze** — score against best practices, no changes
2. **Optimize (static)** — rule-based scoring only, no evals needed
3. **Optimize with evals** (recommended) — 40% static + 60% LLM-as-judge assertions
4. **Create from scratch** — generate a brand new skill grounded in benchmark tasks
5. **Convert dataset** — convert a HuggingFace dataset to eval format

## Step 2: Verify prerequisites

- [ ] API key available via `--api-key` or env vars (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `API_KEY`)
- [ ] For `--benchmark swe-bench` or `searchqa`: `datasets` package installed (`uv pip install datasets`)
- [ ] For optimize/analyze: skill directory exists with a SKILL.md (not required for `--from-scratch`)
- [ ] For `--evals`: file exists at the provided path

## Step 3: Run the command

**Analyze:**
```bash
python main.py analyze <skill_directory>
```

**Static optimization:**
```bash
python main.py optimize <skill_directory> --model <provider/model> --api-key <key>
```

**Eval-based optimization:**
```bash
# Hand-written evals
python main.py optimize-evals <skill_directory> --evals <evals.json>

# Auto-generated evals
python main.py optimize-evals <skill_directory> --generate-evals

# Benchmark-driven
python main.py optimize-evals <skill_directory> --benchmark tau-bench --benchmark-split airline
python main.py optimize-evals <skill_directory> --benchmark swe-bench --benchmark-variant swe-bench-verified
python main.py optimize-evals <skill_directory> --benchmark searchqa
```

**Create from scratch:**
```bash
python main.py optimize-evals <new_directory> --from-scratch --benchmark tau-bench --benchmark-split airline
python main.py optimize-evals <new_directory> --from-scratch --benchmark searchqa
```

**Convert a HuggingFace dataset to eval format:**
```bash
python main.py convert <dataset_id> \
    --prompt-field <field> \
    [--context-field <field>] \
    [--answer-field <field>] \
    [--split <split>] [--n <n>] [--config <config>] \
    -o evals.json
```
Then feed the output into `optimize-evals --evals evals.json`.

All commands accept: `--model <provider/model>`, `--api-key <key>`, `--api-base <url>`, `--max-evals <n>`

## Step 4: Review results

Output is written to `output/<skill-name>-<timestamp>/`:

- [ ] Read `SKILL.md` — the optimized or generated skill
- [ ] Read `benchmark.json` — static score, assertion pass rate, combined score
- [ ] Read `trajectory/trajectory.jsonl` — per-iteration candidate scores
- [ ] Present a before/after summary: size change, code blocks preserved, scores

## Step 5: Iterate if needed

- Increase `--max-evals` for more GEPA iterations
- Provide hand-written evals for tighter control over what the skill must handle
- Try a different `--model` or `--benchmark-split` for more diverse task coverage

## Evals format

```json
{
  "skill_name": "<name>",
  "evals": [
    {
      "id": 1,
      "name": "short-name",
      "prompt": "A realistic user prompt exercising the skill",
      "expected_output": "What a good response looks like",
      "expectations": [
        "Specific, verifiable assertion — e.g. 'includes the kubectl logs command'"
      ]
    }
  ]
}
```

`expectations` is optional — omit to auto-generate 4–6 assertions per case.
