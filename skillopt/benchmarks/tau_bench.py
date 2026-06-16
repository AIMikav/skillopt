"""TAU-bench adapter for SkillOpt.

Converts TAU-bench task definitions into SkillOpt eval format.

TAU-bench stores tasks as Python lists in:
  tau_bench/envs/{domain}/tasks.py  (field: tasks = [...])

Data source options:
  1. Local repo clone: point --benchmark-data at the repo root containing
     tau_bench/envs/{domain}/tasks.py
  2. Auto-fetch: downloads the raw .py file from GitHub and evaluates the
     tasks list in a restricted namespace (requires internet access)

Supported domains: airline, retail
"""

import importlib.util
import urllib.request
from pathlib import Path

SUPPORTED_DOMAINS = {"airline", "retail"}

TAU_BENCH_RAW_BASE = (
    "https://raw.githubusercontent.com/sierra-research/tau-bench/main"
    "/tau_bench/envs/{domain}/tasks.py"
)


def _exec_tasks_module(source: str) -> list[dict]:
    """Safely evaluate a tasks.py file and return the tasks list."""
    namespace: dict = {}
    exec(compile(source, "<tau-bench-tasks>", "exec"), {"__builtins__": {}}, namespace)  # noqa: S102
    tasks = namespace.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError(
            "Could not find a 'tasks' list in the tau-bench tasks.py file."
        )
    return tasks


def _fetch_remote(domain: str) -> list[dict]:
    """Download tasks.py from GitHub and extract the tasks list."""
    url = TAU_BENCH_RAW_BASE.format(domain=domain)
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            source = resp.read().decode("utf-8")
    except Exception as exc:
        raise RuntimeError(
            f"Failed to fetch TAU-bench tasks for domain '{domain}' from {url}: {exc}\n"
            "Provide --benchmark-data pointing to a local tau-bench repo clone."
        ) from exc
    return _exec_tasks_module(source)


def _load_local(domain: str, data_path: Path) -> list[dict]:
    """Load tasks from a local tau-bench repo clone using importlib."""
    candidates = [
        data_path / "tau_bench" / "envs" / domain / "tasks.py",
        data_path / "envs" / domain / "tasks.py",
        data_path / domain / "tasks.py",
        data_path / "tasks.py",
    ]
    tasks_file = None
    for path in candidates:
        if path.exists():
            tasks_file = path
            break

    if tasks_file is None:
        raise FileNotFoundError(
            f"Could not find tasks.py for domain '{domain}' under '{data_path}'.\n"
            f"Tried: {[str(p) for p in candidates]}"
        )

    # Use importlib for local files — avoids exec restrictions on complex modules
    spec = importlib.util.spec_from_file_location(f"tau_bench_{domain}_tasks", tasks_file)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:
        # Fall back to restricted exec if the module has import-time side effects
        source = tasks_file.read_text(encoding="utf-8")
        return _exec_tasks_module(source)

    tasks = getattr(mod, "tasks", None)
    if not isinstance(tasks, list):
        raise ValueError(
            f"No 'tasks' list found in {tasks_file}. "
            "Check that the file defines a top-level 'tasks = [...]' variable."
        )
    return tasks


def _task_to_eval(task: dict, domain: str, idx: int) -> dict:
    """Convert one TAU-bench task dict to SkillOpt eval format."""
    prompt = task.get("instruction", "").strip()
    if not prompt:
        prompt = f"Complete task {idx + 1} in the {domain} domain."

    # Build lightweight assertions from expected tool call names
    expectations = []
    for action in task.get("actions", []):
        name = action.get("name", "")
        if name:
            expectations.append(
                f"Agent calls the '{name}' tool or equivalent action to complete the task."
            )
    # De-duplicate while preserving order
    seen: set[str] = set()
    expectations = [e for e in expectations if not (e in seen or seen.add(e))]

    expected_outputs = task.get("outputs", [])
    expected_output_str = (
        f"Agent completes the {domain} task and reports: "
        + ", ".join(str(o) for o in expected_outputs[:3])
        if expected_outputs
        else f"Agent successfully completes the {domain} customer service task."
    )

    return {
        "id": idx + 1,
        "name": f"tau-{domain}-{idx + 1}",
        "prompt": prompt,
        "expected_output": expected_output_str,
        "expectations": expectations,
    }


def load_tau_bench(
    split: str = "airline",
    data_path: str | Path | None = None,
    n: int = 3,
) -> dict:
    """Load TAU-bench tasks and return SkillOpt evals_data dict.

    Args:
        split: Domain name — 'airline' or 'retail'.
        data_path: Path to a local tau-bench repo root. If None, tasks are
                   fetched from GitHub raw content.
        n: Maximum number of tasks to include as eval cases.

    Returns:
        evals_data dict matching the SkillOpt eval schema.
    """
    if split not in SUPPORTED_DOMAINS:
        raise ValueError(
            f"Unknown TAU-bench domain '{split}'. "
            f"Choose from: {sorted(SUPPORTED_DOMAINS)}"
        )

    if data_path is not None:
        tasks = _load_local(split, Path(data_path))
    else:
        tasks = _fetch_remote(split)

    tasks = tasks[:n]
    evals = [_task_to_eval(t, split, i) for i, t in enumerate(tasks)]

    return {
        "skill_name": f"tau-bench-{split}",
        "benchmark": "tau-bench",
        "benchmark_split": split,
        "evals": evals,
    }
