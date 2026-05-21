#!/usr/bin/env python3
"""
GEPA Skill Optimization with Eval-Based Metric

Optimizes Claude Agent Skills using GEPA's optimize_anything API with evaluation
test cases and assertions as the optimization target.

Three-phase pipeline:
  Phase 1: Load/generate evals and assertions
  Phase 2: GEPA optimization with hybrid metric (static + LLM-as-judge)
  Phase 3: Validate the optimized skill with final assertion pass rates

Usage:
    python optimize_skill_with_evals.py <skill_path> --evals <evals.json>
    python optimize_skill_with_evals.py <skill_path> --generate-evals
    python optimize_skill_with_evals.py <skill_path> --evals <evals.json> --dry-run

Examples:
    python optimize_skill_with_evals.py examples/example_1/Bad_Kubernetes_Helper_Skill \\
        --evals examples/example_1/kubernetes-skill-workspace/evals.json

    python optimize_skill_with_evals.py my-skill/ --generate-evals -o my-skill-optimized/
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import gepa.optimize_anything as oa
from gepa.optimize_anything import optimize_anything, GEPAConfig, EngineConfig, ReflectionConfig
from openai import OpenAI
from dotenv import load_dotenv

from skillopt import SkillParser, SkillAnalyzer

load_dotenv()


# ============================================================================
# Helpers
# ============================================================================

def strip_provider_prefix(model: str) -> str:
    """Strip provider prefix (e.g. 'openai/', 'ollama/') for direct OpenAI SDK usage."""
    if "/" in model:
        return model.split("/", 1)[1]
    return model


def _get_openai_client(api_key: str = None, api_base: str = None) -> OpenAI:
    key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("API_KEY")
    base = api_base or os.getenv("OPENAI_API_BASE") or os.getenv("API_BASE")
    if not key:
        raise ValueError(
            "No API key found. Provide --api-key or set one of: "
            "OPENAI_API_KEY, GEMINI_API_KEY, API_KEY"
        )
    kwargs = {"api_key": key}
    if base:
        kwargs["base_url"] = base
    return OpenAI(**kwargs)


def _chat(client: OpenAI, model: str, prompt: str, temperature: float = 0.7) -> str:
    """Single-turn chat completion, returns content string."""
    response = client.chat.completions.create(
        model=strip_provider_prefix(model),
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content


def _parse_json_or_lines(text: str) -> list:
    """Parse a JSON array from text, falling back to extracting lines."""
    # Try direct JSON parse
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict) and "assertions" in parsed:
            return parsed["assertions"]
        return []
    except json.JSONDecodeError:
        pass

    # Try extracting JSON array from markdown code block
    match = re.search(r'```(?:json)?\s*\n(\[.*?\])\s*\n```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding a bare JSON array
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Fallback: extract lines
    return [
        line.strip().lstrip("-*").strip()
        for line in text.strip().split("\n")
        if line.strip() and len(line.strip()) > 10
    ]


# ============================================================================
# Phase 1: Eval & Assertion Loading / Generation
# ============================================================================

def load_evals(evals_path: Path) -> dict:
    """Load evaluation test cases from evals.json."""
    with open(evals_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_assertions_for_evals(
    evals_data: dict, skill_content: str, model: str = "openai/gpt-4", verbose: bool = False,
    api_key: str = None, api_base: str = None,
) -> dict:
    """Generate assertions for eval cases that don't already have them."""
    client = _get_openai_client(api_key=api_key, api_base=api_base)

    for eval_case in evals_data.get("evals", []):
        if eval_case.get("expectations"):
            continue

        if verbose:
            print(f"    Generating assertions for eval {eval_case.get('id')}...")

        prompt = (
            "Generate verifiable assertions for a skill evaluation test case.\n\n"
            "Given a skill's content and an evaluation prompt, generate specific, "
            "objectively verifiable assertions that a correct response should satisfy.\n\n"
            "Good assertions:\n"
            '- "The response includes the kubectl logs command"\n'
            '- "The response mentions checking pod events with kubectl describe"\n'
            '- "The response explains at least two common causes of CrashLoopBackOff"\n\n'
            "Bad assertions (too subjective):\n"
            '- "The output is well-formatted"\n'
            '- "The response is helpful"\n\n'
            f"Skill content:\n{skill_content[:6000]}\n\n"
            f"User task prompt: {eval_case['prompt']}\n"
            f"Expected output: {eval_case.get('expected_output', '')}\n\n"
            "Return a JSON array of 4-6 verifiable assertion strings.\n"
            'Example: ["assertion 1", "assertion 2"]'
        )

        response_text = _chat(client, model, prompt)
        eval_case["expectations"] = _parse_json_or_lines(response_text)

    return evals_data


def auto_generate_evals(
    skill_content: str, skill_name: str, model: str = "openai/gpt-4o", verbose: bool = False,
    api_key: str = None, api_base: str = None,
) -> dict:
    """Auto-generate eval cases from skill content using LLM."""
    if verbose:
        print("  Generating eval test cases from skill content...")

    client = _get_openai_client(api_key=api_key, api_base=api_base)

    prompt = (
        "Generate evaluation test cases for a Claude Agent Skill.\n\n"
        "Create 3 realistic test prompts a user would actually say. "
        "Cover different aspects of the skill. Make prompts specific and detailed "
        "with context (file paths, names, scenarios), not generic requests.\n\n"
        f"Skill name: {skill_name}\n"
        f"Skill content:\n{skill_content[:6000]}\n\n"
        "Return JSON in this format:\n"
        '{"evals": [{"id": 1, "name": "short-name", '
        '"prompt": "realistic user prompt", '
        '"expected_output": "description of success"}]}'
    )

    response_text = _chat(client, model, prompt)

    try:
        data = json.loads(response_text)
        if "evals" not in data:
            data = {"evals": data if isinstance(data, list) else []}
        data["skill_name"] = skill_name
        return data
    except json.JSONDecodeError:
        return {
            "skill_name": skill_name,
            "evals": [{
                "id": 1,
                "name": "basic-usage",
                "prompt": f"Help me with a typical {skill_name} task",
                "expected_output": "Should provide relevant guidance",
                "expectations": [],
            }],
        }


# ============================================================================
# LLM-as-Judge for Assertion Evaluation
# ============================================================================

def judge_skill_against_assertions(
    optimized_skill: str,
    eval_cases: list[dict],
    model: str = "openai/gpt-4o",
    api_key: str = None,
    api_base: str = None,
) -> tuple[float, list[dict]]:
    """Use LLM-as-judge to evaluate if the skill enables satisfying assertions.

    Returns:
        (score, detailed_results) where score is 0.0-1.0
    """
    client = _get_openai_client(api_key=api_key, api_base=api_base)

    total_assertions = 0
    total_passed = 0
    all_results = []

    for eval_case in eval_cases:
        assertions = eval_case.get("expectations", [])
        if not assertions:
            continue

        prompt = (
            "Judge whether an optimized skill would guide an agent to satisfy assertions.\n\n"
            "Evaluate whether the skill document contains sufficient information, commands, "
            "and guidance for an AI agent to successfully complete the given task and "
            "satisfy all assertions.\n\n"
            "For each assertion:\n"
            "- PASS: The skill clearly provides the knowledge, commands, or workflow "
            "needed to produce output satisfying this assertion.\n"
            "- FAIL: The skill lacks the necessary information, commands, or guidance.\n\n"
            "Be strict: the skill must contain actionable content (specific commands, "
            "steps, examples) that directly enables satisfying the assertion.\n\n"
            f"Optimized skill:\n{optimized_skill}\n\n"
            f"User task prompt: {eval_case['prompt']}\n\n"
            f"Assertions to evaluate:\n{json.dumps(assertions)}\n\n"
            'Return a JSON array of objects: '
            '[{"assertion": "...", "passed": true/false, "reason": "brief evidence"}]'
        )

        response_text = _chat(client, model, prompt, temperature=0.0)

        try:
            verdicts = _parse_json_or_lines(response_text)
            if isinstance(verdicts, list) and verdicts and isinstance(verdicts[0], dict):
                passed = sum(1 for v in verdicts if v.get("passed", False))
                total = len(verdicts)
            else:
                passed = 0
                total = len(assertions)
                verdicts = []
        except (TypeError, IndexError):
            text = response_text.upper()
            passed = max(0, text.count("PASS") - text.count("NOT PASS"))
            total = len(assertions)
            verdicts = []

        total_assertions += total
        total_passed += max(0, passed)
        all_results.append({
            "eval_id": eval_case.get("id", 0),
            "eval_name": eval_case.get("name", ""),
            "passed": max(0, passed),
            "total": total,
            "pass_rate": max(0, passed) / total if total > 0 else 0,
            "verdicts": verdicts,
        })

    overall_score = total_passed / total_assertions if total_assertions > 0 else 0
    return overall_score, all_results


# ============================================================================
# Metric Functions
# ============================================================================

def count_code_blocks(content: str) -> int:
    """Count number of code blocks in content."""
    return len(re.findall(r'```', content)) // 2


def static_analysis_score(optimized: str, original: str) -> float:
    """Compute static analysis score (0.0-1.0).

    Components:
    - 30% Filler phrase removal
    - 25% Conciseness (target 30-70% reduction)
    - 25% Code block preservation
    - 20% Structure preservation (frontmatter, sections, code)
    """
    score = 0.0

    # 1. Filler phrase removal (30%)
    filler_phrases = [
        'make sure to', 'ensure that', "don't forget to", 'remember to',
        'it is important to', 'please note that', 'keep in mind',
        'you should', 'you need to', 'you must',
    ]
    filler_count = sum(1 for p in filler_phrases if p.lower() in optimized.lower())
    score += 0.30 * max(0, 1 - (filler_count / 5))

    # 2. Conciseness (25%)
    orig_len = len(original) if original else 1
    opt_len = len(optimized)
    if opt_len < orig_len:
        ratio = 1 - (opt_len / orig_len)
        if ratio < 0.3:
            score += 0.25 * (ratio / 0.3)
        elif ratio <= 0.7:
            score += 0.25
        else:
            score += 0.25 * max(0, 1 - (ratio - 0.7) * 3)

    # 3. Code block preservation (25%)
    orig_blocks = count_code_blocks(original)
    opt_blocks = count_code_blocks(optimized)
    if orig_blocks > 0:
        block_ratio = opt_blocks / orig_blocks
        if block_ratio >= 0.5:
            score += 0.25 * min(1.0, block_ratio)
        else:
            score += 0.25 * block_ratio * 0.5
    else:
        score += 0.25

    # 4. Structure (20%)
    has_frontmatter = optimized.strip().startswith('---')
    has_sections = '## ' in optimized
    has_code = '```' in optimized
    structure = (0.4 if has_frontmatter else 0) + (0.3 if has_sections else 0) + (0.3 if has_code else 0)
    score += 0.20 * structure

    return score


# ============================================================================
# Evaluator for optimize_anything
# ============================================================================

def create_eval_evaluator(original_content: str, eval_cases: list[dict], model: str,
                          api_key: str = None, api_base: str = None):
    """Create an evaluator closure for optimize_anything.

    Scoring weights:
    - 40% Static analysis (filler, conciseness, structure, code blocks)
    - 60% Assertion satisfaction (LLM-as-judge)
    """
    def evaluate(candidate: str) -> tuple[float, dict]:
        feedback = {}

        # Part A: Static analysis (40%)
        static = static_analysis_score(candidate, original_content)
        feedback["static_score"] = f"{static:.3f}"

        # Part B: LLM-as-judge assertion evaluation (60%)
        assertion_score, detailed = judge_skill_against_assertions(
            candidate, eval_cases, model=model,
            api_key=api_key, api_base=api_base,
        )
        feedback["assertion_pass_rate"] = f"{assertion_score:.3f}"

        combined = 0.40 * static + 0.60 * assertion_score
        feedback["combined_score"] = f"{combined:.3f}"

        # Per-eval feedback for GEPA reflection
        for r in detailed:
            status = (
                "PASS" if r["pass_rate"] == 1.0
                else f"PARTIAL ({r['passed']}/{r['total']})"
            )
            feedback[f"eval_{r['eval_id']}_{r['eval_name']}"] = status
            if r.get("verdicts"):
                failures = [v for v in r["verdicts"] if isinstance(v, dict) and not v.get("passed")]
                if failures:
                    feedback[f"eval_{r['eval_id']}_failures"] = json.dumps(failures[:3])

        oa.log(f"Static: {static:.3f} | Assertions: {assertion_score:.3f} | Combined: {combined:.3f}")
        for r in detailed:
            oa.log(f"  Eval [{r['eval_id']}] {r['eval_name']}: {r['passed']}/{r['total']}")

        return combined, feedback

    return evaluate


# ============================================================================
# Formatting Helpers
# ============================================================================

def format_eval_cases(eval_cases: list[dict]) -> str:
    """Format eval cases as readable text for GEPA background context."""
    lines = []
    for ec in eval_cases:
        lines.append(f"## Test Case {ec.get('id', '?')}: {ec.get('name', 'unnamed')}")
        lines.append(f"Prompt: {ec['prompt']}")
        lines.append(f"Expected: {ec.get('expected_output', 'N/A')}")
        assertions = ec.get("expectations", [])
        if assertions:
            lines.append("Assertions (the optimized skill MUST enable satisfying ALL of these):")
            for a in assertions:
                lines.append(f"  - {a}")
        lines.append("")
    return "\n".join(lines)


# ============================================================================
# Main Optimization Pipeline
# ============================================================================

def optimize_skill_with_evals(
    skill_path: Path,
    evals_path: Path = None,
    output_path: Path = None,
    model: str = "openai/gpt-4o",
    max_evals: int = 10,
    dry_run: bool = False,
    generate_evals: bool = False,
    verbose: bool = True,
    api_key: str = None,
    api_base: str = None,
) -> dict:
    """
    Three-phase skill optimization pipeline.

    Phase 1: Load/generate evals and assertions
    Phase 2: GEPA optimization with hybrid metric (static + LLM-as-judge)
    Phase 3: Validate and output results with assertion pass rates

    Args:
        skill_path: Path to the skill directory containing SKILL.md
        evals_path: Path to evals.json with test cases
        output_path: Directory to save optimized skill and benchmark
        model: LLM model in litellm format (default: openai/gpt-4o)
        max_evals: Maximum GEPA metric calls
        dry_run: If True, only run Phase 1 (load/generate evals)
        generate_evals: If True, auto-generate eval cases when none provided
        verbose: Print progress information

    Returns:
        dict with optimization results including assertion pass rates
    """
    # ---- Setup ----
    parser = SkillParser()
    analyzer = SkillAnalyzer()

    if not skill_path.exists():
        raise FileNotFoundError(f"Skill not found: {skill_path}")

    skill = parser.parse_directory(skill_path)
    skill_content = skill.main_file.raw_content

    if verbose:
        print(f"Loaded skill: {skill.name}")
        print(f"  Lines: {skill.total_lines}")
        print(f"  References: {len(skill.references)}")

    # Analyze
    report = analyzer.analyze(skill)
    if verbose:
        errors = sum(1 for i in report.issues if i.severity == 'error')
        warnings = sum(1 for i in report.issues if i.severity == 'warning')
        suggestions = sum(1 for i in report.issues if i.severity == 'suggestion')
        print(f"\nAnalysis: {report.score}/100 ({errors} errors, {warnings} warnings, {suggestions} suggestions)")

    # ==================================================================
    # Phase 1: Load / Generate Evals & Assertions
    # ==================================================================
    if verbose:
        print("\n" + "=" * 60)
        print("PHASE 1: Load evals and generate assertions")
        print("=" * 60)

    if evals_path and evals_path.exists():
        evals_data = load_evals(evals_path)
        if verbose:
            print(f"Loaded evals from: {evals_path}")
            print(f"  Skill: {evals_data.get('skill_name', 'unknown')}")
            print(f"  Eval cases: {len(evals_data.get('evals', []))}")
    elif generate_evals:
        evals_data = auto_generate_evals(skill_content, skill.name, model=model, verbose=verbose,
                                          api_key=api_key, api_base=api_base)
        if verbose:
            print(f"  Generated {len(evals_data.get('evals', []))} eval case(s)")
    else:
        raise FileNotFoundError(
            "No evals.json found. Provide --evals <path> or use --generate-evals"
        )

    eval_cases = evals_data.get("evals", [])

    # Generate assertions for cases that don't have them
    cases_without = [e for e in eval_cases if not e.get("expectations")]
    if cases_without:
        if verbose:
            print(f"\nGenerating assertions for {len(cases_without)} eval case(s)...")
        evals_data = generate_assertions_for_evals(
            evals_data, skill_content, model=model, verbose=verbose,
            api_key=api_key, api_base=api_base,
        )
        eval_cases = evals_data.get("evals", [])

    if verbose:
        print(f"\nEval cases with assertions:")
        for ec in eval_cases:
            assertions = ec.get("expectations", [])
            print(f"  [{ec.get('id')}] {ec.get('name', 'unnamed')}: {len(assertions)} assertion(s)")
            for a in assertions[:3]:
                print(f"      - {a}")
            if len(assertions) > 3:
                print(f"      ... and {len(assertions) - 3} more")

    # Save evals with assertions
    if evals_path:
        evals_out = evals_path.parent / "evals_with_assertions.json"
    else:
        evals_out = skill_path / "evals_with_assertions.json"
    with open(evals_out, "w") as f:
        json.dump(evals_data, f, indent=2)
    if verbose:
        print(f"\nSaved evals with assertions: {evals_out}")

    if dry_run:
        if verbose:
            print("\nDry run complete. Evals loaded/generated, no optimization performed.")
        return {
            "skill": skill,
            "report": report,
            "evals": evals_data,
            "dry_run": True,
        }

    # ==================================================================
    # Phase 2: GEPA Optimization
    # ==================================================================
    if verbose:
        print("\n" + "=" * 60)
        print("PHASE 2: GEPA optimization with eval-based metric")
        print("=" * 60)

    issues_str = "\n".join([
        f"- [{issue.severity}] {issue.category}: {issue.message}"
        for issue in report.issues[:20]
    ])

    eval_cases_str = format_eval_cases(eval_cases)

    objective = (
        "Optimize this Claude Agent Skill (SKILL.md) to be effective, concise, and "
        "satisfy all evaluation criteria. The skill must contain the knowledge, commands, "
        "and workflows needed for an agent to handle all test cases and pass all assertions. "
        "The output must be a complete, valid SKILL.md file starting with --- frontmatter."
    )

    background = (
        f"Issues found by the skill analyzer:\n{issues_str}\n\n"
        f"Evaluation test cases the optimized skill must support:\n{eval_cases_str}\n\n"
        "Optimization guidelines:\n"
        "- Remove filler phrases: 'make sure to', 'ensure that', 'don't forget to'\n"
        "- Don't explain concepts Claude already knows (YAML, JSON, APIs, etc.)\n"
        "- Preserve frontmatter (--- name/description ---), section headers (##), "
        "and essential code blocks\n"
        "- Consolidate similar commands using placeholders (e.g., -n <namespace>)\n"
        "- Target 30-70% size reduction"
    )

    evaluator = create_eval_evaluator(skill_content, eval_cases, model=model,
                                      api_key=api_key, api_base=api_base)

    total_assertions = sum(len(e.get("expectations", [])) for e in eval_cases)
    if verbose:
        print(f"Running GEPA optimize_anything with {model}...")
        print(f"  Max metric calls: {max_evals}")
        print(f"  Eval cases: {len(eval_cases)}")
        print(f"  Total assertions: {total_assertions}")
        print(f"  Metric: 40% static + 60% assertion (LLM-as-judge)")
        print()

    if api_key:
        os.environ.setdefault("OPENAI_API_KEY", api_key)
    if api_base:
        os.environ.setdefault("OPENAI_API_BASE", api_base)

    result = optimize_anything(
        seed_candidate=skill_content,
        evaluator=evaluator,
        objective=objective,
        background=background,
        config=GEPAConfig(
            engine=EngineConfig(
                max_metric_calls=max_evals,
                display_progress_bar=verbose,
            ),
            reflection=ReflectionConfig(
                reflection_lm=model,
                skip_perfect_score=True,
                perfect_score=1.0,
            ),
        ),
    )

    optimized_content = result.best_candidate
    if isinstance(optimized_content, dict):
        optimized_content = list(optimized_content.values())[0]

    if verbose:
        print("\nGEPA optimization complete")

    # ==================================================================
    # Phase 3: Validate & Output
    # ==================================================================
    if verbose:
        print("\n" + "=" * 60)
        print("PHASE 3: Validation and results")
        print("=" * 60)

    # Final assertion evaluation
    final_assertion_score, detailed_results = judge_skill_against_assertions(
        optimized_content, eval_cases, model=model,
        api_key=api_key, api_base=api_base,
    )

    # Static analysis
    static = static_analysis_score(optimized_content, skill_content)
    combined = 0.40 * static + 0.60 * final_assertion_score

    # Metrics
    original_len = len(skill_content)
    optimized_len = len(optimized_content)
    reduction_pct = ((original_len - optimized_len) / original_len * 100) if original_len > 0 else 0
    orig_blocks = count_code_blocks(skill_content)
    opt_blocks = count_code_blocks(optimized_content)

    if verbose:
        print(f"\nOptimization Results:")
        print(f"  Original:  {original_len:,} chars, {orig_blocks} code blocks")
        print(f"  Optimized: {optimized_len:,} chars, {opt_blocks} code blocks")
        print(f"  Reduction: {original_len - optimized_len:,} chars ({reduction_pct:.1f}%)")
        print(f"  Code blocks: {opt_blocks}/{orig_blocks}")
        print(f"\nScores:")
        print(f"  Static analysis:     {static:.3f}")
        print(f"  Assertion pass rate: {final_assertion_score:.3f}")
        print(f"  Combined (40/60):    {combined:.3f}")
        print(f"\nAssertion Results by Eval:")
        for r in detailed_results:
            status = "PASS" if r['pass_rate'] == 1.0 else "PARTIAL" if r['pass_rate'] > 0 else "FAIL"
            print(f"  [{r['eval_id']}] {r['eval_name']}: {r['passed']}/{r['total']} ({r['pass_rate']:.0%}) {status}")

    # Save output
    if output_path:
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        (output_path / "SKILL.md").write_text(optimized_content)

        benchmark = {
            "metadata": {
                "skill_name": skill.name,
                "model": model,
                "optimizer": "GEPA optimize_anything",
                "max_metric_calls": max_evals,
                "metric_weights": {"static": 0.40, "assertions": 0.60},
            },
            "scores": {
                "static_analysis": round(static, 4),
                "assertion_pass_rate": round(final_assertion_score, 4),
                "combined": round(combined, 4),
            },
            "metrics": {
                "original_chars": original_len,
                "optimized_chars": optimized_len,
                "reduction_percent": round(reduction_pct, 1),
                "original_code_blocks": orig_blocks,
                "optimized_code_blocks": opt_blocks,
            },
            "assertion_results": detailed_results,
            "evals": eval_cases,
        }

        with open(output_path / "benchmark.json", "w") as f:
            json.dump(benchmark, f, indent=2)

        if verbose:
            print(f"\nSaved to: {output_path}")
            print(f"  SKILL.md       - optimized skill")
            print(f"  benchmark.json - evaluation results")

    return {
        "skill": skill,
        "report": report,
        "evals": evals_data,
        "optimized_content": optimized_content,
        "original_length": original_len,
        "optimized_length": optimized_len,
        "reduction_percent": reduction_pct,
        "original_code_blocks": orig_blocks,
        "optimized_code_blocks": opt_blocks,
        "static_score": static,
        "assertion_score": final_assertion_score,
        "combined_score": combined,
        "assertion_results": detailed_results,
        "output_path": output_path,
    }


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    p = argparse.ArgumentParser(
        description="Optimize Claude Agent Skills using GEPA with eval-based metric",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python optimize_skill_with_evals.py examples/example_1/Bad_Kubernetes_Helper_Skill \\
      --evals examples/example_1/kubernetes-skill-workspace/evals.json

  python optimize_skill_with_evals.py my-skill/ --generate-evals

  python optimize_skill_with_evals.py my-skill/ --evals evals.json --dry-run
        """,
    )

    p.add_argument("skill_path", type=Path, help="Path to the skill directory")
    p.add_argument("-o", "--output", type=Path, help="Output directory for optimized skill")
    p.add_argument("--evals", type=Path, help="Path to evals.json with test cases")
    p.add_argument("--model", default="openai/gpt-4o", help="LLM model in litellm format (default: openai/gpt-4o)")
    p.add_argument("--max-evals", type=int, default=10, help="Max GEPA metric calls (default: 10)")
    p.add_argument("--generate-evals", action="store_true", help="Auto-generate eval cases if none provided")
    p.add_argument("--dry-run", action="store_true", help="Phase 1 only: load/generate evals, skip optimization")
    p.add_argument("--api-key", default=None, help="API key (default: OPENAI_API_KEY or API_KEY env var)")
    p.add_argument("--api-base", default=None, help="API base URL for OpenAI-compatible endpoints (e.g. http://localhost:11434/v1 for Ollama)")
    p.add_argument("-q", "--quiet", action="store_true", help="Suppress verbose output")

    args = p.parse_args()

    # Default output path
    if args.output is None and not args.dry_run:
        args.output = Path(f"{args.skill_path}_GEPA_Eval_Optimized")

    # Auto-discover evals.json if not provided
    if args.evals is None and not args.generate_evals:
        candidates = [
            args.skill_path / "evals" / "evals.json",
            args.skill_path.parent / f"{args.skill_path.name}-workspace" / "evals.json",
            args.skill_path / "evals.json",
        ]
        for c in candidates:
            if c.exists():
                args.evals = c
                if not args.quiet:
                    print(f"Auto-discovered evals: {c}")
                break

    if args.evals is None and not args.generate_evals:
        print("Error: No evals.json found. Provide --evals <path> or use --generate-evals", file=sys.stderr)
        return 1

    try:
        result = optimize_skill_with_evals(
            skill_path=args.skill_path,
            evals_path=args.evals,
            output_path=args.output,
            model=args.model,
            max_evals=args.max_evals,
            dry_run=args.dry_run,
            generate_evals=args.generate_evals,
            verbose=not args.quiet,
            api_key=args.api_key,
            api_base=args.api_base,
        )

        if not args.quiet:
            print("\n" + "=" * 60)
            if args.dry_run:
                print("Dry run complete. Evals loaded/generated.")
            else:
                print("Optimization complete!")
                print(f"  Reduction:  {result['reduction_percent']:.1f}%")
                print(f"  Static:     {result['static_score']:.3f}")
                print(f"  Assertions: {result['assertion_score']:.3f}")
                print(f"  Combined:   {result['combined_score']:.3f}")
                if result['output_path']:
                    print(f"  Output:     {result['output_path']}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
