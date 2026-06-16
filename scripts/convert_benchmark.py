#!/usr/bin/env python3
"""
Convert any HuggingFace dataset into SkillOpt eval format.

Usage:
    python convert_benchmark.py <dataset_id> --prompt-field <field> [options]

Examples:
    # QA dataset with context
    python convert_benchmark.py lucadiliello/searchqa \\
        --split validation --n 5 \\
        --prompt-field question \\
        --context-field context \\
        --answer-field answers \\
        -o evals.json

    # Code dataset
    python convert_benchmark.py openai/openai_humaneval \\
        --split test --n 5 \\
        --prompt-field prompt \\
        --answer-field canonical_solution \\
        --name-field task_id \\
        -o evals.json

    # Dataset with a config
    python convert_benchmark.py allenai/ai2_arc \\
        --config ARC-Challenge --split test --n 5 \\
        --prompt-field question \\
        --answer-field answerKey \\
        -o evals.json
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ============================================================================
# Field extraction
# ============================================================================

def _get_field(row: dict, field: str):
    """Extract a value from a row using dot notation for nested fields.

    Supports:
      - Simple keys: "question"
      - Nested dicts: "answers.text"
      - List of dicts (takes first element): "answers.0.text" or "answers.text"
    """
    parts = field.split(".")
    value = row
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        elif isinstance(value, list):
            # Try integer index first, then apply key to first element
            try:
                value = value[int(part)]
            except (ValueError, IndexError):
                value = value[0].get(part) if value and isinstance(value[0], dict) else None
        else:
            return None
        if value is None:
            return None
    return value


def _to_str(value) -> str:
    """Coerce any field value to a readable string."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        # Join list of strings; for list of dicts take first element's values
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item.strip())
            elif isinstance(item, dict):
                parts.append(", ".join(str(v) for v in item.values()))
            else:
                parts.append(str(item))
        return ", ".join(parts)
    return str(value).strip()


def _make_slug(value: str, max_len: int = 40) -> str:
    """Convert a value to a safe eval name slug."""
    slug = re.sub(r"[^a-zA-Z0-9_-]", "-", str(value)).strip("-")
    return slug[:max_len].strip("-") or "eval"


# ============================================================================
# Conversion
# ============================================================================

def convert_dataset(
    dataset_id: str,
    prompt_field: str,
    split: str = "train",
    n: int = 3,
    config: str = None,
    context_field: str = None,
    answer_field: str = None,
    name_field: str = None,
    id_field: str = None,
    skill_name: str = None,
    verbose: bool = True,
) -> dict:
    """Load a HuggingFace dataset and convert it to SkillOpt eval format.

    Args:
        dataset_id: HuggingFace dataset ID (e.g. 'lucadiliello/searchqa')
        prompt_field: Field to use as the eval prompt (dot notation supported)
        split: Dataset split to load (default: 'train')
        n: Number of examples to convert
        config: HuggingFace dataset config name (optional)
        context_field: Field prepended to prompt as "Context:\\n{value}\\n\\n{prompt}"
        answer_field: Field for expected_output
        name_field: Field for the eval name slug (defaults to row index)
        id_field: Field for eval id (defaults to row index)
        skill_name: skill_name in the output (defaults to dataset slug)
        verbose: Print progress

    Returns:
        evals_data dict matching the SkillOpt eval schema
    """
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise ImportError(
            "The `datasets` package is required.\n"
            "Install it with:  uv pip install datasets"
        ) from exc

    if verbose:
        print(f"Loading dataset: {dataset_id} (split={split}, config={config or 'default'})")

    load_kwargs = {"split": split, "trust_remote_code": False}
    if config:
        load_kwargs["name"] = config

    dataset = load_dataset(dataset_id, **load_kwargs)
    total = len(dataset)
    n = min(n, total)

    if verbose:
        print(f"  Total rows in split: {total:,}")
        print(f"  Converting: {n}")

    evals = []
    for idx, row in enumerate(dataset.select(range(n))):
        # Prompt
        prompt_val = _to_str(_get_field(row, prompt_field))
        if not prompt_val:
            if verbose:
                print(f"  [warn] Row {idx}: prompt_field '{prompt_field}' is empty — skipping")
            continue

        # Optional context prepended to prompt
        if context_field:
            ctx = _to_str(_get_field(row, context_field))
            if ctx:
                prompt_val = f"Context:\n{ctx}\n\n{prompt_val}"

        # Expected output
        expected = ""
        if answer_field:
            expected = _to_str(_get_field(row, answer_field))

        # Eval name
        if name_field:
            name = _make_slug(_to_str(_get_field(row, name_field)))
        else:
            name = f"eval-{idx + 1}"

        # Eval id
        if id_field:
            eval_id = _get_field(row, id_field)
            try:
                eval_id = int(eval_id)
            except (TypeError, ValueError):
                eval_id = idx + 1
        else:
            eval_id = idx + 1

        evals.append({
            "id": eval_id,
            "name": name,
            "prompt": prompt_val,
            "expected_output": expected,
            "expectations": [],
        })

    derived_skill_name = skill_name or re.sub(r"[^a-zA-Z0-9_-]", "-", dataset_id.split("/")[-1])

    return {
        "skill_name": derived_skill_name,
        "source_dataset": dataset_id,
        "source_split": split,
        "evals": evals,
    }


# ============================================================================
# CLI
# ============================================================================

def main():
    p = argparse.ArgumentParser(
        description="Convert a HuggingFace dataset to SkillOpt eval format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Field mapping:
  Use dot notation to access nested fields: e.g. --prompt-field answers.text
  For lists of dicts, the first element is used: answers.text → answers[0]["text"]

Examples:
  python convert_benchmark.py lucadiliello/searchqa \\
      --split validation --n 5 \\
      --prompt-field question --context-field context --answer-field answers \\
      -o evals.json

  python convert_benchmark.py openai/openai_humaneval \\
      --split test --n 5 \\
      --prompt-field prompt --answer-field canonical_solution --name-field task_id \\
      -o evals.json

  python convert_benchmark.py allenai/ai2_arc --config ARC-Challenge \\
      --split test --n 5 \\
      --prompt-field question --answer-field answerKey \\
      -o evals.json
        """,
    )

    p.add_argument("dataset_id", help="HuggingFace dataset ID (e.g. lucadiliello/searchqa)")

    # Field mapping
    p.add_argument("--prompt-field", required=True,
                   help="Dataset field to use as the eval prompt (dot notation supported)")
    p.add_argument("--context-field", default=None,
                   help="Field prepended to prompt as 'Context:\\n{value}\\n\\n{prompt}'")
    p.add_argument("--answer-field", default=None,
                   help="Field for expected_output (optional)")
    p.add_argument("--name-field", default=None,
                   help="Field for the eval name slug (default: row index)")
    p.add_argument("--id-field", default=None,
                   help="Field for eval id (default: row index)")

    # Dataset control
    p.add_argument("--split", default="train",
                   help="Dataset split to load (default: train)")
    p.add_argument("--n", type=int, default=3,
                   help="Number of examples to convert (default: 3)")
    p.add_argument("--config", default=None,
                   help="HuggingFace dataset config name (e.g. ARC-Challenge)")

    # Output
    p.add_argument("-o", "--output", type=Path, default=Path("evals.json"),
                   help="Output path for evals.json (default: evals.json)")
    p.add_argument("--skill-name", default=None,
                   help="skill_name in the output (default: derived from dataset ID)")
    p.add_argument("-q", "--quiet", action="store_true", help="Suppress verbose output")

    args = p.parse_args()

    try:
        data = convert_dataset(
            dataset_id=args.dataset_id,
            prompt_field=args.prompt_field,
            split=args.split,
            n=args.n,
            config=args.config,
            context_field=args.context_field,
            answer_field=args.answer_field,
            name_field=args.name_field,
            id_field=args.id_field,
            skill_name=args.skill_name,
            verbose=not args.quiet,
        )
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2), encoding="utf-8")

    if not args.quiet:
        print(f"\nConverted {len(data['evals'])} eval(s) → {args.output}")
        print(f"\nNext step:")
        print(f"  uv run python main.py optimize-evals <skill_dir> --evals {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
