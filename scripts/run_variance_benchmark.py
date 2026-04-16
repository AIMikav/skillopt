#!/usr/bin/env python3
"""
Benchmark SkillOpt analyzer variance across 10 runs.
"""

import json
from pathlib import Path
from statistics import mean, stdev
from skillopt import SkillParser, SkillAnalyzer

def benchmark_skill_variance(skill_path: Path, num_runs: int = 10):
    """Run analysis multiple times and calculate variance."""
    parser = SkillParser()
    analyzer = SkillAnalyzer()

    print(f"Benchmarking: {skill_path.name}")
    print(f"Running {num_runs} iterations...")
    print("=" * 70)

    results = []

    for i in range(num_runs):
        print(f"Run {i+1}/{num_runs}... ", end="", flush=True)

        # Parse and analyze
        skill = parser.parse_directory(skill_path)
        report = analyzer.analyze(skill)

        # Collect metrics
        run_data = {
            'run': i + 1,
            'score': report.score,
            'total_issues': len(report.issues),
            'errors': sum(1 for iss in report.issues if iss.severity == 'error'),
            'warnings': sum(1 for iss in report.issues if iss.severity == 'warning'),
            'suggestions': sum(1 for iss in report.issues if iss.severity == 'suggestion'),
            'lines': skill.total_lines,
        }

        results.append(run_data)
        print(f"Score: {report.score}/100")

    return results

def calculate_stats(values: list):
    """Calculate mean, std dev, and coefficient of variation."""
    if not values:
        return 0, 0, 0

    avg = mean(values)
    std = stdev(values) if len(values) > 1 else 0.0
    cv = (std / avg * 100) if avg != 0 else 0.0

    return avg, std, cv

def print_variance_report(results: list, skill_name: str):
    """Print comprehensive variance analysis."""
    print("\n" + "=" * 70)
    print(f"VARIANCE ANALYSIS: {skill_name}")
    print("=" * 70)
    print()

    # Calculate statistics for each metric
    metrics = {
        'Score': [r['score'] for r in results],
        'Total Issues': [r['total_issues'] for r in results],
        'Errors': [r['errors'] for r in results],
        'Warnings': [r['warnings'] for r in results],
        'Suggestions': [r['suggestions'] for r in results],
    }

    # Summary table
    print("METRIC STABILITY")
    print("-" * 70)
    print(f"{'Metric':<20} {'Mean':<12} {'Std Dev':<12} {'CV%':<10}")
    print("-" * 70)

    for metric_name, values in metrics.items():
        avg, std, cv = calculate_stats(values)
        print(f"{metric_name:<20} {avg:>11.2f} {std:>11.4f} {cv:>9.2f}%")

    # Run-by-run details
    print("\nRUN-BY-RUN RESULTS")
    print("-" * 70)
    print(f"{'Run':<6} {'Score':<10} {'Issues':<10} {'Errors':<10} {'Warnings':<10} {'Suggestions'}")
    print("-" * 70)

    for r in results:
        print(f"{r['run']:<6} {r['score']:<10} {r['total_issues']:<10} "
              f"{r['errors']:<10} {r['warnings']:<10} {r['suggestions']}")

    # Variance interpretation
    print("\nINTERPRETATION")
    print("-" * 70)

    score_avg, score_std, score_cv = calculate_stats(metrics['Score'])

    print(f"Score Stability: ", end="")
    if score_std == 0:
        print("PERFECT (zero variance - deterministic)")
    elif score_cv < 1:
        print(f"EXCELLENT (CV = {score_cv:.2f}%)")
    elif score_cv < 5:
        print(f"GOOD (CV = {score_cv:.2f}%)")
    else:
        print(f"MODERATE (CV = {score_cv:.2f}%)")

    issue_avg, issue_std, issue_cv = calculate_stats(metrics['Total Issues'])

    print(f"Issue Detection Stability: ", end="")
    if issue_std == 0:
        print("PERFECT (zero variance - deterministic)")
    elif issue_cv < 1:
        print(f"EXCELLENT (CV = {issue_cv:.2f}%)")
    elif issue_cv < 5:
        print(f"GOOD (CV = {issue_cv:.2f}%)")
    else:
        print(f"MODERATE (CV = {issue_cv:.2f}%)")

    print(f"\nConclusion: The analyzer is {'DETERMINISTIC' if score_std == 0 else 'STABLE with minimal variance'}")
    print("=" * 70)

def compare_skills_variance(skills: dict, num_runs: int = 10):
    """Compare variance across multiple skills."""
    all_results = {}

    for skill_name, skill_path in skills.items():
        print(f"\n{'='*70}")
        print(f"Testing: {skill_name}")
        print(f"{'='*70}")

        results = benchmark_skill_variance(skill_path, num_runs)
        all_results[skill_name] = results

        print_variance_report(results, skill_name)

    # Comparison summary
    print("\n" + "=" * 70)
    print("CROSS-SKILL COMPARISON")
    print("=" * 70)
    print()
    print(f"{'Skill':<30} {'Avg Score':<12} {'Score StdDev':<12} {'CV%'}")
    print("-" * 70)

    for skill_name, results in all_results.items():
        scores = [r['score'] for r in results]
        avg, std, cv = calculate_stats(scores)
        print(f"{skill_name:<30} {avg:>11.2f} {std:>11.4f} {cv:>9.2f}%")

    print("=" * 70)

if __name__ == "__main__":
    # Define skills to benchmark
    skills_to_test = {
        "Original (Bad)": Path("examples/example_1/Bad_Kubernetes_Helper_Skill"),
        "GEPA Optimized": Path("examples/example_1/Bad_Kubernetes_Helper_Skill_Fresh_Optimized"),
        "Skill-Creator Optimized": Path("examples/example_1/Bad_Kubernetes_Helper_Skill_SkillCreator_Optimized"),
    }

    # Run variance benchmark
    compare_skills_variance(skills_to_test, num_runs=10)
