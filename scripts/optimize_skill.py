#!/usr/bin/env python3
"""
GEPA Skill Optimization Script

Optimize Claude Agent Skills using GEPA's optimize_anything API.

Usage:
    python optimize_skill.py <skill_path> [options]

Examples:
    python optimize_skill.py examples/Bad_Kubernetes_Helper_Skill
    python optimize_skill.py examples/Bad_Kubernetes_Helper_Skill -o optimized_skill
    python optimize_skill.py examples/Bad_Kubernetes_Helper_Skill --dry-run
"""

import argparse
import os
import re
import sys
from pathlib import Path

import gepa.optimize_anything as oa
from gepa.optimize_anything import optimize_anything, GEPAConfig, EngineConfig, ReflectionConfig
from dotenv import load_dotenv

from skillopt import SkillParser, SkillAnalyzer


load_dotenv()


# ============================================================================
# Helper Functions
# ============================================================================

FILLER_PHRASES = [
    'make sure to', 'ensure that', "don't forget to", 'remember to',
    'it is important to', 'please note that', 'keep in mind',
    'you should', 'you need to', 'you must',
]

VERBOSE_PATTERNS = [
    'Portable Document Format', 'JavaScript Object Notation',
    'Yet Another Markup Language', 'Application Programming Interface',
    'is an open-source', 'is a system for',
]


def count_code_blocks(content: str) -> int:
    """Count number of code blocks in content."""
    return len(re.findall(r'```', content)) // 2


def extract_code_blocks(content: str) -> list[str]:
    """Extract all code blocks from content."""
    pattern = r'```(?:\w+)?\s*\n(.*?)```'
    return re.findall(pattern, content, re.DOTALL)


# ============================================================================
# Evaluator
# ============================================================================

def create_skill_evaluator(original_content: str):
    """Create an evaluator closure that scores optimized skill candidates.

    Scoring weights:
    - 25% Filler phrase removal
    - 20% Conciseness (target 40-70% reduction)
    - 25% Code block preservation
    - 15% Structure preserved (frontmatter, sections)
    - 15% Verbose explanations removed
    """
    original_len = len(original_content)
    original_blocks = count_code_blocks(original_content)

    def evaluate(candidate: str) -> tuple[float, dict]:
        score = 0.0
        feedback = {}

        # 1. Filler phrase removal (25%)
        found_fillers = [p for p in FILLER_PHRASES if p.lower() in candidate.lower()]
        filler_count = len(found_fillers)
        filler_score = max(0, 1 - (filler_count / 5))
        score += 0.25 * filler_score
        feedback["filler_phrases"] = (
            f"Found {filler_count}: {found_fillers}" if found_fillers else "None found"
        )

        # 2. Conciseness — target 40-70% reduction (20%)
        optimized_len = len(candidate)
        if optimized_len < original_len:
            reduction_ratio = 1 - (optimized_len / original_len)
            if reduction_ratio < 0.4:
                concise_score = reduction_ratio / 0.4
            elif reduction_ratio <= 0.7:
                concise_score = 1.0
            else:
                concise_score = max(0, 1 - (reduction_ratio - 0.7) * 3)
        else:
            reduction_ratio = 0.0
            concise_score = 0.0
        score += 0.20 * concise_score
        feedback["size_reduction"] = f"{reduction_ratio * 100:.1f}% (target: 40-70%)"

        # 3. Code block preservation (25%)
        opt_blocks = count_code_blocks(candidate)
        if original_blocks > 0:
            block_ratio = opt_blocks / original_blocks
            if block_ratio >= 0.5:
                code_score = min(1.0, block_ratio)
            else:
                code_score = block_ratio * 0.5
        else:
            code_score = 1.0 if opt_blocks == 0 else 0.8
        score += 0.25 * code_score
        feedback["code_blocks"] = f"preserved {opt_blocks}/{original_blocks}"

        # 4. Structure preserved (15%)
        has_frontmatter = candidate.strip().startswith('---')
        has_sections = '## ' in candidate
        has_code = '```' in candidate
        structure_score = (
            (0.4 if has_frontmatter else 0) +
            (0.3 if has_sections else 0) +
            (0.3 if has_code else 0)
        )
        score += 0.15 * structure_score
        feedback["structure"] = (
            f"frontmatter={'yes' if has_frontmatter else 'MISSING'}, "
            f"sections={'yes' if has_sections else 'MISSING'}, "
            f"code={'yes' if has_code else 'MISSING'}"
        )

        # 5. Verbose explanations removed (15%)
        found_verbose = [p for p in VERBOSE_PATTERNS if p.lower() in candidate.lower()]
        verbose_count = len(found_verbose)
        verbose_score = max(0, 1 - (verbose_count / 3))
        score += 0.15 * verbose_score
        feedback["verbose_explanations"] = (
            f"Found {verbose_count}: {found_verbose}" if found_verbose else "None found"
        )

        oa.log(f"Score: {score:.3f} | Size: {feedback['size_reduction']} | "
               f"Filler: {filler_count} | Code: {feedback['code_blocks']} | "
               f"Verbose: {verbose_count}")

        return score, feedback

    return evaluate


# ============================================================================
# Main Optimization Function
# ============================================================================

def optimize_skill(
    skill_path: Path,
    output_path: Path = None,
    model: str = "openai/gpt-4o",
    max_evals: int = 10,
    content_limit: int = 8000,
    dry_run: bool = False,
    verbose: bool = True,
    api_key: str = None,
    api_base: str = None,
) -> dict:
    """
    Optimize a Claude Agent Skill using GEPA's optimize_anything.

    Args:
        skill_path: Path to the skill directory
        output_path: Path to save optimized skill (optional)
        model: LLM model to use (litellm format, e.g. openai/gpt-4o)
        max_evals: Maximum GEPA metric calls
        content_limit: Character limit for skill content
        dry_run: If True, only analyze without optimizing
        verbose: Print progress information

    Returns:
        dict with optimization results
    """
    parser = SkillParser()
    analyzer = SkillAnalyzer()

    if not skill_path.exists():
        raise FileNotFoundError(f"Skill not found at: {skill_path}")

    skill = parser.parse_directory(skill_path)

    if verbose:
        print(f"Loaded skill: {skill.name}")
        print(f"  Lines: {skill.total_lines}")
        print(f"  References: {len(skill.references)}")

    report = analyzer.analyze(skill)

    if verbose:
        print(f"\nAnalysis Report")
        print("=" * 50)
        print(f"Score: {report.score}/100")
        print(f"Issues: {len(report.issues)}")

        errors = [i for i in report.issues if i.severity == 'error']
        warnings = [i for i in report.issues if i.severity == 'warning']
        suggestions = [i for i in report.issues if i.severity == 'suggestion']
        print(f"  Errors: {len(errors)}")
        print(f"  Warnings: {len(warnings)}")
        print(f"  Suggestions: {len(suggestions)}")

    if dry_run:
        if verbose:
            print("\nDry run - showing issues only:")
            for issue in report.issues[:15]:
                icon = {"error": "[ERR]", "warning": "[WRN]", "suggestion": "[SUG]"}.get(
                    issue.severity, "[?]"
                )
                print(f"  {icon} {issue.category}: {issue.message}")
        return {
            "skill": skill,
            "report": report,
            "optimized_content": None,
            "dry_run": True,
        }

    issues_str = "\n".join([
        f"- [{issue.severity}] {issue.category}: {issue.message}"
        for issue in report.issues[:20]
    ])

    skill_content = skill.main_file.raw_content[:content_limit]
    original_code_blocks = count_code_blocks(skill_content)

    if verbose:
        print(f"\nSkill content: {len(skill_content):,} chars")
        print(f"Code blocks found: {original_code_blocks}")

    # Build objective and background for GEPA reflection
    objective = (
        "Optimize this Claude Agent Skill (SKILL.md) to reduce token usage while "
        "preserving full functionality. Remove filler phrases, verbose explanations, "
        "and redundant content. Preserve all code blocks, YAML frontmatter, and "
        "section headers. Consolidate similar commands using placeholders. "
        "The output must be a complete, valid SKILL.md file."
    )

    background = (
        f"Issues found by the skill analyzer:\n{issues_str}\n\n"
        "Best practices for Claude Agent Skills:\n"
        "- Remove filler phrases: 'make sure to', 'ensure that', 'don't forget to', "
        "'remember to', 'it is important to', 'please note that', 'keep in mind'\n"
        "- Don't explain concepts Claude already knows (YAML, JSON, APIs, Kubernetes, etc.)\n"
        "- Keep YAML frontmatter (--- name/description ---), section headers (##), "
        "and all code blocks (```)\n"
        "- Consolidate similar commands using placeholders (e.g., -n <namespace>)\n"
        "- Target 40-70% size reduction — not more, not less\n"
        "- Preserve core functionality and workflow logic"
    )

    evaluator = create_skill_evaluator(skill_content)

    if verbose:
        print(f"\nRunning GEPA optimize_anything (max_metric_calls={max_evals})...")
        print("=" * 50)

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
        print("GEPA optimization complete")

    # Calculate metrics
    original_len = len(skill_content)
    optimized_len = len(optimized_content)
    reduction = original_len - optimized_len
    reduction_pct = (reduction / original_len) * 100 if original_len > 0 else 0

    orig_blocks = count_code_blocks(skill_content)
    opt_blocks = count_code_blocks(optimized_content)

    metric_score, _ = evaluator(optimized_content)

    if verbose:
        print(f"\nResults:")
        print(f"  Original: {original_len:,} chars, {orig_blocks} code blocks")
        print(f"  Optimized: {optimized_len:,} chars, {opt_blocks} code blocks")
        print(f"  Reduction: {reduction:,} chars ({reduction_pct:.1f}%)")
        print(f"  Code blocks preserved: {opt_blocks}/{orig_blocks}")
        print(f"  Metric score: {metric_score:.2f}")

    if output_path:
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        output_file = output_path / "SKILL.md"
        output_file.write_text(optimized_content)

        if verbose:
            print(f"\nSaved optimized skill to: {output_file}")

    return {
        "skill": skill,
        "report": report,
        "optimized_content": optimized_content,
        "original_length": original_len,
        "optimized_length": optimized_len,
        "reduction_percent": reduction_pct,
        "original_code_blocks": orig_blocks,
        "optimized_code_blocks": opt_blocks,
        "metric_score": metric_score,
        "output_path": output_path,
    }


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Optimize Claude Agent Skills using GEPA optimizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python optimize_skill.py examples/Bad_Kubernetes_Helper_Skill
  python optimize_skill.py examples/Bad_Kubernetes_Helper_Skill -o optimized_skill
  python optimize_skill.py examples/Bad_Kubernetes_Helper_Skill --dry-run
  python optimize_skill.py examples/Bad_Kubernetes_Helper_Skill --model openai/gpt-4o-mini
        """
    )

    parser.add_argument(
        "skill_path",
        type=Path,
        help="Path to the skill directory to optimize",
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output directory for optimized skill (default: <skill_path>_GEPA_Optimized)",
    )

    parser.add_argument(
        "--model",
        type=str,
        default="openai/gpt-4o",
        help="LLM model to use in litellm format (default: openai/gpt-4o)",
    )

    parser.add_argument(
        "--max-evals",
        type=int,
        default=10,
        help="Maximum GEPA metric calls (default: 10)",
    )

    parser.add_argument(
        "--content-limit",
        type=int,
        default=8000,
        help="Character limit for skill content (default: 8000)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze skill without optimizing",
    )

    parser.add_argument(
        "--api-key",
        default=None,
        help="API key (default: OPENAI_API_KEY or API_KEY env var)",
    )

    parser.add_argument(
        "--api-base",
        default=None,
        help="API base URL for OpenAI-compatible endpoints (e.g. http://localhost:11434/v1 for Ollama)",
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress verbose output",
    )

    args = parser.parse_args()

    if args.output is None and not args.dry_run:
        args.output = Path(f"{args.skill_path}_GEPA_Optimized")

    try:
        result = optimize_skill(
            skill_path=args.skill_path,
            output_path=args.output,
            model=args.model,
            max_evals=args.max_evals,
            content_limit=args.content_limit,
            dry_run=args.dry_run,
            verbose=not args.quiet,
            api_key=args.api_key,
            api_base=args.api_base,
        )

        if not args.quiet:
            print("\n" + "=" * 50)
            if args.dry_run:
                print("Dry run complete. No changes made.")
            else:
                print("Optimization complete!")
                print(f"  Reduction: {result['reduction_percent']:.1f}%")
                print(f"  Code blocks: {result['optimized_code_blocks']}/{result['original_code_blocks']}")
                print(f"  Metric score: {result['metric_score']:.2f}")
                if result['output_path']:
                    print(f"  Output: {result['output_path']}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if not args.quiet:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
