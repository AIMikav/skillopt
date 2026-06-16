"""Trajectory logging for GEPA optimization runs.

Intercepts each evaluator call to save candidates and scores incrementally,
then writes a summary after optimization completes.
"""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


class TrajectoryLogger:
    """Wraps a GEPA evaluator to capture every candidate and score per iteration.

    Usage:
        logger = TrajectoryLogger(output_dir / "trajectory")
        evaluator = logger.wrap(evaluator)
        result = optimize_anything(seed_candidate=..., evaluator=evaluator, ...)
        logger.save_summary(result, metadata={"skill_name": ..., "model": ...})
    """

    def __init__(self, trajectory_dir: Path) -> None:
        self.trajectory_dir = Path(trajectory_dir)
        self.candidates_dir = self.trajectory_dir / "candidates"
        self.trajectory_dir.mkdir(parents=True, exist_ok=True)
        self.candidates_dir.mkdir(exist_ok=True)

        self.jsonl_path = self.trajectory_dir / "trajectory.jsonl"
        # Truncate any existing file from a previous run
        self.jsonl_path.write_text("")

        self._lock = threading.Lock()
        self._call_index = 0
        self._best_score = float("-inf")

    def wrap(self, evaluator: Callable) -> Callable:
        """Return a new evaluator that logs each call before returning."""

        def wrapped(candidate: str) -> tuple[float, dict]:
            score, feedback = evaluator(candidate)

            with self._lock:
                idx = self._call_index
                self._call_index += 1
                is_best = score > self._best_score
                if is_best:
                    self._best_score = score

            # Save candidate file
            candidate_file = f"candidates/candidate_{idx:03d}.md"
            (self.candidates_dir / f"candidate_{idx:03d}.md").write_text(
                candidate, encoding="utf-8"
            )

            # Append JSONL record
            record = {
                "call_index": idx,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "score": round(score, 6),
                "feedback": feedback,
                "candidate_file": candidate_file,
                "is_best_so_far": is_best,
            }
            with self._lock:
                with self.jsonl_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(record) + "\n")

            return score, feedback

        return wrapped

    def save_summary(self, result: Any, metadata: dict | None = None) -> Path:
        """Write trajectory_summary.json from the GEPAResult after optimization.

        Args:
            result: GEPAResult returned by optimize_anything
            metadata: Optional dict with run metadata (skill_name, model, etc.)

        Returns:
            Path to the written summary file
        """
        scores = list(result.val_aggregate_scores) if result.val_aggregate_scores else []
        parents = list(result.parents) if result.parents else []
        discovery_counts = (
            list(result.discovery_eval_counts) if result.discovery_eval_counts else []
        )

        best_idx = result.best_idx if scores else 0
        best_score = scores[best_idx] if scores else self._best_score

        trajectory = []
        for i, score in enumerate(scores):
            parent = parents[i][0] if i < len(parents) and parents[i] else None
            discovered_at = discovery_counts[i] if i < len(discovery_counts) else i
            trajectory.append(
                {
                    "candidate_index": i,
                    "discovered_at_call": discovered_at,
                    "score": round(score, 6),
                    "parent": parent,
                    "candidate_file": f"candidates/candidate_{discovered_at:03d}.md",
                    "is_best": i == best_idx,
                }
            )

        # Sort trajectory by discovery order for readability
        trajectory.sort(key=lambda r: r["discovered_at_call"])

        summary = {
            "metadata": {
                **(metadata or {}),
                "total_metric_calls": result.total_metric_calls,
                "num_candidates_explored": result.num_candidates,
            },
            "best": {
                "candidate_index": best_idx,
                "score": round(best_score, 6),
                "candidate_file": f"candidates/candidate_{discovery_counts[best_idx] if best_idx < len(discovery_counts) else best_idx:03d}.md",
            },
            "trajectory": trajectory,
        }

        summary_path = self.trajectory_dir / "trajectory_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary_path
