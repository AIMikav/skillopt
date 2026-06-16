# SkillOpt

SkillOpt optimizes or creates Claude Agent Skills using GEPA's `optimize_anything` API. It uses a hybrid evaluator (40% static best-practice rules + 60% LLM-as-judge assertion pass rate) to score each candidate, and GEPA's reflection-driven search evolves the skill toward the optimum.

## Subcommands

- `analyze` — score a skill against best practices, no changes made
- `optimize` — static-only GEPA optimization (no LLM judge or evals needed)
- `optimize-evals` — eval-based GEPA optimization; evals can be hand-written, auto-generated, or loaded from TAU-bench / SWE-bench / SearchQA; use `--from-scratch` to create a new skill instead of optimizing an existing one
- `convert` — convert any HuggingFace dataset to SkillOpt eval format via field mapping flags, output fed into `optimize-evals`

## Key flags

- `--model`, `--api-key`, `--api-base` — LLM provider config (OpenAI, Ollama, Gemini, or any OpenAI-compatible endpoint)
- `--benchmark` — load evals from `tau-bench`, `swe-bench`, or `searchqa`
- `--from-scratch` — skip existing SKILL.md, have GEPA generate the first candidate from benchmark context
- `--dry-run` — Phase 1 only: load/generate evals without optimizing
- `--max-evals` — number of GEPA iterations (default: 10)
- `-o` — override output directory (default: `output/<skill-name>-<timestamp>/`)

## Output

All artifacts go to `output/<skill-name>-<timestamp>/`: optimized `SKILL.md`, `benchmark.json` (scores + assertion verdicts), `evals_with_assertions.json`, and a `trajectory/` directory with per-iteration candidate files and a live `trajectory.jsonl` log.

## API key resolution

Checks `--api-key` flag first, then env vars `OPENAI_API_KEY` → `GEMINI_API_KEY` → `API_KEY` (loaded from `.env`).
