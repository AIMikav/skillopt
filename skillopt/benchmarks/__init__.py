"""Benchmark adapters for SkillOpt.

Converts standard benchmark task formats into the SkillOpt eval schema so they
can drive GEPA optimization without any changes to the core pipeline.

Supported benchmarks:
  tau-bench    Tool-Augmented User tasks (airline, retail, telecom, banking)
  swe-bench    Software Engineering tasks from real GitHub issues
"""

from pathlib import Path

from skillopt.benchmarks.tau_bench import load_tau_bench
from skillopt.benchmarks.swe_bench import load_swe_bench
from skillopt.benchmarks.searchqa import load_searchqa

SUPPORTED_BENCHMARKS = {"tau-bench", "swe-bench", "searchqa"}


def load_benchmark(
    name: str,
    split: str | None = None,
    data_path: str | Path | None = None,
    n: int = 3,
    **kwargs,
) -> dict:
    """Load eval cases from a standard benchmark.

    Args:
        name: Benchmark name — 'tau-bench' or 'swe-bench'.
        split: Domain (tau-bench) or dataset split (swe-bench).
               Defaults: 'airline' for tau-bench, 'test' for swe-bench.
        data_path: Local path to tau-bench repo (tau-bench only). If None,
                   tasks are fetched from GitHub.
        n: Number of tasks/instances to use as eval cases (default: 3).
        **kwargs: Passed to the underlying loader (e.g. variant= for swe-bench).

    Returns:
        evals_data dict matching the SkillOpt eval schema.
    """
    if name not in SUPPORTED_BENCHMARKS:
        raise ValueError(
            f"Unknown benchmark '{name}'. Choose from: {sorted(SUPPORTED_BENCHMARKS)}"
        )

    if name == "tau-bench":
        return load_tau_bench(
            split=split or "airline",
            data_path=data_path,
            n=n,
        )


    if name == "swe-bench":
        return load_swe_bench(
            split=split or "test",
            variant=kwargs.get("variant", "swe-bench"),
            n=n,
        )

    if name == "searchqa":
        return load_searchqa(
            split=split or "validation",
            n=n,
        )


__all__ = [
    "load_benchmark",
    "load_tau_bench",
    "load_swe_bench",
    "load_searchqa",
    "SUPPORTED_BENCHMARKS",
]
