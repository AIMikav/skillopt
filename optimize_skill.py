#!/usr/bin/env python3
"""
GEPA Skill Optimization Script

Optimize Claude Agent Skills using DSPy's GEPA optimizer.

Usage:
    python optimize_skill.py <skill_path> [options]

Examples:
    python optimize_skill.py examples/Bad_Kubernetes_Helper_Skill
    python optimize_skill.py examples/Bad_Kubernetes_Helper_Skill -o optimized_skill
    python optimize_skill.py examples/Bad_Kubernetes_Helper_Skill --dry-run
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import dspy
from dspy import GEPA
from dotenv import load_dotenv

from skillopt import SkillParser, SkillAnalyzer


# Load environment variables
load_dotenv()


# ============================================================================
# DSPy Module Definition
# ============================================================================

class OptimizeSkillContent(dspy.Signature):
    """Optimize a Claude Agent Skill following best practices.

    PRESERVE:
    - All code blocks (```bash, ```python, etc.) - these are essential commands
    - Frontmatter (--- name/description ---)
    - Section headers (##)
    - Useful technical content

    REMOVE:
    - Filler phrases: "make sure to", "ensure that", "don't forget to", etc.
    - Verbose explanations of common concepts (YAML, JSON, API definitions)
    - Redundant command variations (consolidate same command for different namespaces)
    - Unrelated content (e.g., PDF/Git commands in a Kubernetes skill)
    - Time-sensitive information

    CONSOLIDATE:
    - Multiple similar commands into one with placeholder (e.g., -n <namespace>)
    """
    original_content: str = dspy.InputField(desc="Original skill content with issues")
    issues_found: str = dspy.InputField(desc="List of issues identified in the skill")
    optimized_content: str = dspy.OutputField(desc="Optimized skill preserving code blocks but removing filler")


class SkillOptimizerModule(dspy.Module):
    """DSPy module for skill optimization that preserves code blocks."""

    def __init__(self):
        super().__init__()
        self.optimizer = dspy.ChainOfThought(OptimizeSkillContent)

    def forward(self, original_content: str, issues_found: str) -> str:
        result = self.optimizer(
            original_content=original_content,
            issues_found=issues_found
        )
        return result.optimized_content


# ============================================================================
# Helper Functions
# ============================================================================

def count_code_blocks(content: str) -> int:
    """Count number of code blocks in content."""
    return len(re.findall(r'```', content)) // 2


def extract_code_blocks(content: str) -> list[str]:
    """Extract all code blocks from content."""
    pattern = r'```(?:\w+)?\s*\n(.*?)```'
    return re.findall(pattern, content, re.DOTALL)


def load_training_examples(json_path: Path, categories: list[str] = None):
    """Load training examples from JSON file."""
    if not json_path.exists():
        return {"examples": []}, []

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    examples = data.get("examples", [])

    if categories:
        examples = [ex for ex in examples if ex.get("category") in categories]

    return data, examples


def examples_to_dspy_trainset(examples: list[dict]) -> list:
    """Convert JSON examples to DSPy format."""
    trainset = []

    for ex in examples:
        if "bad" not in ex or "good" not in ex:
            continue

        bad = ex["bad"]
        good = ex["good"]

        if isinstance(bad, dict):
            bad_content = bad.get("content", "")
            bad_issues = bad.get("issues", [])
        else:
            bad_content = str(bad)
            bad_issues = []

        if isinstance(good, dict):
            good_content = good.get("content", "")
        else:
            good_content = str(good)

        issues_str = "\n".join([
            f"- [{ex.get('category', 'unknown')}] {issue}"
            for issue in bad_issues
        ])

        if not issues_str:
            issues_str = f"- [{ex.get('category', 'unknown')}] {ex.get('principle', 'Needs optimization')}"

        dspy_example = dspy.Example(
            original_content=bad_content,
            issues_found=issues_str,
            optimized_content=good_content,
        ).with_inputs("original_content", "issues_found")

        trainset.append(dspy_example)

    return trainset


# ============================================================================
# Metric Function
# ============================================================================

def skill_optimization_metric(gold, pred, trace=None, pred_name=None, pred_trace=None):
    """Evaluate skill optimization quality.

    Scoring:
    - 25% Filler phrase removal
    - 20% Conciseness (but not too aggressive)
    - 25% Code block preservation (CRITICAL)
    - 15% Structure preserved (frontmatter, sections)
    - 15% Verbose explanations removed

    Returns:
        float: Score between 0 and 1
    """
    optimized = pred.optimized_content if hasattr(pred, 'optimized_content') else str(pred)
    original_content = gold.original_content if hasattr(gold, 'original_content') else ""

    score = 0.0

    # 1. Filler phrase removal (25%)
    filler_phrases = ['make sure to', 'ensure that', "don't forget to", 'remember to',
                      'it is important to', 'please note that', 'keep in mind',
                      'you should', 'you need to', 'you must']
    filler_count = sum(1 for phrase in filler_phrases if phrase.lower() in optimized.lower())
    filler_score = max(0, 1 - (filler_count / 5))
    score += 0.25 * filler_score

    # 2. Conciseness - target 40-70% reduction, penalize over-reduction (20%)
    original_len = len(original_content) if original_content else 1
    optimized_len = len(optimized)
    if optimized_len < original_len:
        reduction_ratio = 1 - (optimized_len / original_len)
        if reduction_ratio < 0.4:
            concise_score = reduction_ratio / 0.4
        elif reduction_ratio <= 0.7:
            concise_score = 1.0
        else:
            concise_score = max(0, 1 - (reduction_ratio - 0.7) * 3)
    else:
        concise_score = 0.0
    score += 0.20 * concise_score

    # 3. Code block preservation - CRITICAL (25%)
    original_blocks = count_code_blocks(original_content)
    optimized_blocks = count_code_blocks(optimized)

    if original_blocks > 0:
        block_ratio = optimized_blocks / original_blocks
        if block_ratio >= 0.5:
            code_score = min(1.0, block_ratio)
        else:
            code_score = block_ratio * 0.5
    else:
        code_score = 1.0 if optimized_blocks == 0 else 0.8
    score += 0.25 * code_score

    # 4. Structure preserved - frontmatter and sections (15%)
    has_frontmatter = optimized.strip().startswith('---')
    has_sections = '## ' in optimized
    has_code = '```' in optimized
    structure_score = (
        (0.4 if has_frontmatter else 0) +
        (0.3 if has_sections else 0) +
        (0.3 if has_code else 0)
    )
    score += 0.15 * structure_score

    # 5. Verbose explanations removed (15%)
    verbose_patterns = [
        'Portable Document Format', 'JavaScript Object Notation',
        'Yet Another Markup Language', 'Application Programming Interface',
        'is an open-source', 'is a system for'
    ]
    verbose_count = sum(1 for p in verbose_patterns if p.lower() in optimized.lower())
    verbose_score = max(0, 1 - (verbose_count / 3))
    score += 0.15 * verbose_score

    return score


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
    verbose: bool = True
) -> dict:
    """
    Optimize a Claude Agent Skill using GEPA.

    Args:
        skill_path: Path to the skill directory
        output_path: Path to save optimized skill (optional)
        model: OpenAI model to use
        max_evals: Maximum GEPA evaluations
        content_limit: Character limit for training content
        dry_run: If True, only analyze without optimizing
        verbose: Print progress information

    Returns:
        dict with optimization results
    """
    # Initialize parser and analyzer
    parser = SkillParser()
    analyzer = SkillAnalyzer()

    # Parse the skill
    if not skill_path.exists():
        raise FileNotFoundError(f"Skill not found at: {skill_path}")

    skill = parser.parse_directory(skill_path)

    if verbose:
        print(f"Loaded skill: {skill.name}")
        print(f"  Lines: {skill.total_lines}")
        print(f"  References: {len(skill.references)}")

    # Analyze skill
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
                icon = {"error": "[ERR]", "warning": "[WRN]", "suggestion": "[SUG]"}.get(issue.severity, "[?]")
                print(f"  {icon} {issue.category}: {issue.message}")
        return {
            "skill": skill,
            "report": report,
            "optimized_content": None,
            "dry_run": True
        }

    # Configure DSPy
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    lm = dspy.LM(model, api_key=api_key)
    dspy.configure(lm=lm)

    if verbose:
        print(f"\nConfigured DSPy with: {lm.model}")

    # Prepare training data
    issues_str = "\n".join([
        f"- [{issue.severity}] {issue.category}: {issue.message}"
        for issue in report.issues[:20]
    ])

    skill_content = skill.main_file.raw_content[:content_limit]
    original_code_blocks = count_code_blocks(skill_content)

    if verbose:
        print(f"\nTraining content: {len(skill_content):,} chars")
        print(f"Code blocks found: {original_code_blocks}")

    # Create training example
    trainset = [
        dspy.Example(
            original_content=skill_content,
            issues_found=issues_str
        ).with_inputs("original_content", "issues_found")
    ]

    # Load additional training examples if available
    training_examples_path = Path(__file__).parent / "examples" / "training_examples.json"
    if training_examples_path.exists():
        _, all_examples = load_training_examples(training_examples_path)
        best_practices_trainset = examples_to_dspy_trainset(all_examples)
        if verbose:
            print(f"Loaded {len(best_practices_trainset)} best practices examples")

    # Initialize module
    skill_optimizer_module = SkillOptimizerModule()

    # Create reflection LM
    reflection_lm = dspy.LM(
        model,
        api_key=api_key,
        temperature=1.0,
        max_tokens=4096
    )

    # Initialize GEPA optimizer
    gepa_optimizer = GEPA(
        metric=skill_optimization_metric,
        reflection_lm=reflection_lm,
        max_full_evals=max_evals,
        num_threads=1,
        reflection_minibatch_size=3,
        skip_perfect_score=True,
    )

    if verbose:
        print(f"\nRunning GEPA optimization...")
        print("=" * 50)

    # Compile/optimize the module
    optimized_module = gepa_optimizer.compile(
        student=skill_optimizer_module,
        trainset=trainset,
    )

    if verbose:
        print("GEPA optimization complete")

    # Apply optimized module
    if verbose:
        print(f"\nApplying optimized module...")

    gepa_result = optimized_module(
        original_content=skill_content,
        issues_found=issues_str
    )

    optimized_content = gepa_result.optimized_content if hasattr(gepa_result, 'optimized_content') else str(gepa_result)

    # Calculate metrics
    original_len = len(skill_content)
    optimized_len = len(optimized_content)
    reduction = original_len - optimized_len
    reduction_pct = (reduction / original_len) * 100 if original_len > 0 else 0

    orig_blocks = count_code_blocks(skill_content)
    opt_blocks = count_code_blocks(optimized_content)

    if verbose:
        print(f"\nResults:")
        print(f"  Original: {original_len:,} chars, {orig_blocks} code blocks")
        print(f"  Optimized: {optimized_len:,} chars, {opt_blocks} code blocks")
        print(f"  Reduction: {reduction:,} chars ({reduction_pct:.1f}%)")
        print(f"  Code blocks preserved: {opt_blocks}/{orig_blocks}")

    # Calculate final metric score
    class PredictionWrapper:
        def __init__(self, content):
            self.optimized_content = content

    metric_score = skill_optimization_metric(
        gold=trainset[0],
        pred=PredictionWrapper(optimized_content)
    )

    if verbose:
        print(f"  Metric score: {metric_score:.2f}")

    # Save optimized skill
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
        "output_path": output_path
    }


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Optimize Claude Agent Skills using DSPy's GEPA optimizer",
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
        help="Path to the skill directory to optimize"
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output directory for optimized skill (default: <skill_path>_GEPA_Optimized)"
    )

    parser.add_argument(
        "--model",
        type=str,
        default="openai/gpt-4o",
        help="OpenAI model to use (default: openai/gpt-4o)"
    )

    parser.add_argument(
        "--max-evals",
        type=int,
        default=10,
        help="Maximum GEPA evaluations (default: 10)"
    )

    parser.add_argument(
        "--content-limit",
        type=int,
        default=8000,
        help="Character limit for training content (default: 8000)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze skill without optimizing"
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )

    args = parser.parse_args()

    # Set default output path
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
            verbose=not args.quiet
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
