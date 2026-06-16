"""SWE-bench adapter for SkillOpt.

Converts SWE-bench instances (real GitHub issue resolution tasks) into SkillOpt
eval format. Uses the HuggingFace `datasets` library to auto-download.

Supported variants:
  swe-bench          princeton-nlp/SWE-bench          (~2.3k test instances)
  swe-bench-verified princeton-nlp/SWE-bench_Verified (500 human-validated)
  swe-bench-lite     princeton-nlp/SWE-bench_Lite     (300 instances)
"""

import re

DATASET_IDS = {
    "swe-bench": "princeton-nlp/SWE-bench",
    "swe-bench-verified": "princeton-nlp/SWE-bench_Verified",
    "swe-bench-lite": "princeton-nlp/SWE-bench_Lite",
}

DEFAULT_SPLIT = "test"


def _slug(instance_id: str) -> str:
    """Convert instance_id (e.g. django__django-12345) to a short eval name."""
    slug = re.sub(r"[^a-zA-Z0-9\-]", "-", instance_id)
    return slug[:48].strip("-")


def _instance_to_eval(instance: dict, idx: int) -> dict:
    """Convert one SWE-bench instance to SkillOpt eval format.

    Expectations are left empty — the LLM-as-judge will auto-generate them
    from the problem statement, since FAIL_TO_PASS test names are too
    implementation-specific for natural-language assertion checking.
    """
    instance_id = instance.get("instance_id", f"swe-{idx + 1}")
    repo = instance.get("repo", "unknown/repo")
    problem = instance.get("problem_statement", "").strip()

    # Summarise FAIL_TO_PASS tests as context for the expected output field
    fail_to_pass = instance.get("FAIL_TO_PASS", "[]")
    if isinstance(fail_to_pass, str):
        try:
            import json
            fail_to_pass = json.loads(fail_to_pass)
        except Exception:
            fail_to_pass = []
    test_summary = (
        f" Tests to fix: {', '.join(fail_to_pass[:3])}" if fail_to_pass else ""
    )

    return {
        "id": idx + 1,
        "name": _slug(instance_id),
        "prompt": problem or f"Resolve the issue in {repo} (instance: {instance_id})",
        "expected_output": (
            f"Agent identifies the root cause in {repo} and proposes a targeted code fix "
            f"that resolves the issue.{test_summary}"
        ),
        "expectations": [],  # auto-generated during Phase 1 of optimization
    }


def load_swe_bench(
    split: str = "test",
    variant: str = "swe-bench",
    n: int = 3,
) -> dict:
    """Load SWE-bench instances and return SkillOpt evals_data dict.

    Args:
        split: Dataset split — 'test' or 'dev'. 'swe-bench-verified' only has 'test'.
        variant: One of 'swe-bench', 'swe-bench-verified', 'swe-bench-lite'.
        n: Maximum number of instances to include as eval cases.

    Returns:
        evals_data dict matching the SkillOpt eval schema.

    Raises:
        ImportError: If the `datasets` package is not installed.
        ValueError: If variant or split is unrecognised.
    """
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise ImportError(
            "The `datasets` package is required to load SWE-bench.\n"
            "Install it with:  uv pip install datasets\n"
            "Or:               pip install datasets"
        ) from exc

    if variant not in DATASET_IDS:
        raise ValueError(
            f"Unknown SWE-bench variant '{variant}'. "
            f"Choose from: {sorted(DATASET_IDS)}"
        )

    dataset_id = DATASET_IDS[variant]
    dataset = load_dataset(dataset_id, split=split, trust_remote_code=False)

    instances = list(dataset.select(range(min(n, len(dataset)))))
    evals = [_instance_to_eval(inst, i) for i, inst in enumerate(instances)]

    return {
        "skill_name": f"{variant}-{split}",
        "benchmark": "swe-bench",
        "benchmark_variant": variant,
        "benchmark_split": split,
        "evals": evals,
    }
