"""SearchQA adapter for SkillOpt.

Converts SearchQA instances into SkillOpt eval format. Each instance contains
a Jeopardy!-style question and web search snippets as context; the agent must
find the correct answer within the provided passages.

Dataset: lucadiliello/searchqa (HuggingFace, derived from MRQA 2019)
Splits:  train (117k), validation (17k)

Requires: pip install datasets
"""

DATASET_ID = "lucadiliello/searchqa"
CONTEXT_LIMIT = 2000  # chars — keeps prompts manageable for the LLM judge


def _clean_context(context: str) -> str:
    """Strip MRQA structural tags and trim to CONTEXT_LIMIT chars."""
    for tag in ("[DOC]", "[TLE]", "[PAR]"):
        context = context.replace(tag, "\n")
    context = "\n".join(line.strip() for line in context.splitlines() if line.strip())
    return context[:CONTEXT_LIMIT] + ("..." if len(context) > CONTEXT_LIMIT else "")


def _instance_to_eval(instance: dict, idx: int) -> dict:
    """Convert one SearchQA instance to SkillOpt eval format."""
    question = instance.get("question", "").strip()
    context = _clean_context(instance.get("context", ""))
    answers = instance.get("answers", [])
    key = instance.get("key", f"searchqa-{idx}")[:8]

    prompt = f"Question: {question}\n\nSearch results:\n{context}"
    expected = (
        f"The correct answer is: {', '.join(answers[:3])}"
        if answers
        else "Find and state the answer from the search results."
    )

    expectations = []
    if answers:
        expectations.append(
            f"The response identifies the correct answer: {answers[0]}"
        )
        expectations.append(
            "The response cites or references the relevant passage from the search results."
        )

    return {
        "id": idx + 1,
        "name": f"searchqa-{key}",
        "prompt": prompt,
        "expected_output": expected,
        "expectations": expectations,
    }


def load_searchqa(
    split: str = "validation",
    n: int = 3,
) -> dict:
    """Load SearchQA instances and return SkillOpt evals_data dict.

    Args:
        split: Dataset split — 'train' or 'validation'.
        n: Maximum number of instances to include as eval cases.

    Returns:
        evals_data dict matching the SkillOpt eval schema.

    Raises:
        ImportError: If the `datasets` package is not installed.
    """
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise ImportError(
            "The `datasets` package is required to load SearchQA.\n"
            "Install it with:  uv pip install datasets"
        ) from exc

    dataset = load_dataset(DATASET_ID, split=split, trust_remote_code=False)
    instances = list(dataset.select(range(min(n, len(dataset)))))
    evals = [_instance_to_eval(inst, i) for i, inst in enumerate(instances)]

    return {
        "skill_name": f"searchqa-{split}",
        "benchmark": "searchqa",
        "benchmark_split": split,
        "evals": evals,
    }
