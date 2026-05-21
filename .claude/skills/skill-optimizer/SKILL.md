---
name: skill-optimizer
description: Use when the user wants to analyze, optimize, or benchmark a Claude Agent Skill using GEPA. Handles best practices analysis, static or eval-based optimization, eval/assertion generation, and before/after comparison.
argument-hint: <skill-directory> [--evals <evals.json>] [--generate-evals] [--mode analyze|optimize|optimize-evals]
allowed-tools: Bash Read Grep Glob
---

# Skill Optimizer

Optimize the Claude Agent Skill at `$ARGUMENTS` using GEPA's optimize_anything API.

## Step 1: Parse arguments

Parse `$ARGUMENTS` for:
- **skill directory** (required) -- path to directory containing a SKILL.md
- **--evals <path>** (optional) -- path to an evals.json file
- **--generate-evals** (optional) -- auto-generate evals from skill content
- **--mode** (optional) -- one of `analyze`, `optimize`, `optimize-evals` (default: ask)
- **-o <path>** (optional) -- output directory

If only a skill directory is provided, ask the user which mode to run:
1. **Analyze** -- score against best practices, no optimization
2. **Optimize (static)** -- evaluator scores filler/conciseness/structure/code-blocks
3. **Optimize with evals** (recommended) -- 40% static + 60% LLM-as-judge assertions

## Step 2: Verify prerequisites

- [ ] Confirm the skill directory exists and contains a SKILL.md
- [ ] Confirm an API key is available (via `--api-key`, or env vars: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `API_KEY`)
- [ ] If evals path was provided, confirm the file exists
- [ ] Ask the user which LLM provider/model to use if not specified

```bash
test -f "$SKILL_DIR/SKILL.md" && echo "SKILL.md found" || echo "ERROR: No SKILL.md"
```

## Step 3: Analyze

Always run analysis first regardless of mode:

```bash
python main.py analyze <skill_directory>
```

Report to the user:
- Score out of 100
- Number of errors, warnings, suggestions
- Top issues found

If mode is `analyze`, stop here.

## Step 4: Optimize

Run the appropriate optimization:

All commands accept `--model <provider/model>`, `--api-key <key>`, and `--api-base <url>`.

**Static-only:**
```bash
python main.py optimize <skill_directory> -o <output_directory> --model ollama/gemma3:4b --api-key ollama --api-base http://localhost:11434/v1
```

**Eval-based with provided evals:**
```bash
python main.py optimize-evals <skill_directory> --evals <evals_json_path> -o <output_directory> --model <provider/model> --api-key <key>
```

**Eval-based with auto-generated evals:**
```bash
python main.py optimize-evals <skill_directory> --generate-evals -o <output_directory> --model <provider/model> --api-key <key>
```

If no output directory was specified, the CLI defaults to `<skill_directory>_GEPA_Optimized` or `<skill_directory>_GEPA_Eval_Optimized`.

## Step 5: Review results

After optimization:

- [ ] Read the optimized SKILL.md from the output directory
- [ ] Read benchmark.json for scores and assertion verdicts (eval-based only)
- [ ] Present a before/after comparison:
  - Character count and reduction percentage
  - Code blocks preserved
  - Filler phrases removed
  - Static score, assertion pass rate, combined score (eval-based)
  - Per-eval assertion results with PASS/FAIL (eval-based)

## Step 6: Iterate if needed

If the user wants to improve further:

- Increase `--max-evals` for more GEPA iterations
- Provide hand-written evals for tighter control
- Try a different `--model` (e.g. `ollama/gemma3:4b` for local, `openai/gpt-4o-mini` for fast cloud)

## Evals format

If the user wants to write custom evals, help them create a JSON file:

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
        "Specific, verifiable assertion about the response"
      ]
    }
  ]
}
```

The `expectations` array is optional -- if omitted, assertions are auto-generated (3-6 per case). Assertions must be objective ("includes the kubectl logs command"), not subjective ("is well-formatted").
