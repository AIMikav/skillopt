#!/usr/bin/env python3
"""
SkillOpt — Optimize Claude Agent Skills using GEPA's optimize_anything API.

Subcommands:
    analyze         Analyze a skill against best practices (no optimization)
    optimize        Static-only GEPA optimization
    optimize-evals  Eval-based GEPA optimization (static + LLM-as-judge assertions)
    convert         Convert any HuggingFace dataset to SkillOpt eval format

Usage:
    python main.py analyze <skill_path>
    python main.py optimize <skill_path> [-o <output>]
    python main.py optimize-evals <skill_path> --evals <evals.json>
    python main.py optimize-evals <skill_path> --generate-evals
    python main.py convert <dataset_id> --prompt-field <field> [-o evals.json]
"""

import sys
from pathlib import Path

# Ensure the repo root is on sys.path so scripts/ can import skillopt
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def cmd_analyze(argv):
    """Run skill analysis without optimization."""
    from scripts.optimize_skill import main as optimize_main
    sys.argv = ["optimize_skill", *argv, "--dry-run"]
    raise SystemExit(optimize_main())


def cmd_optimize(argv):
    """Run static-only GEPA optimization."""
    from scripts.optimize_skill import main as optimize_main
    sys.argv = ["optimize_skill", *argv]
    raise SystemExit(optimize_main())


def cmd_optimize_evals(argv):
    """Run eval-based GEPA optimization."""
    from scripts.optimize_skill_with_evals import main as optimize_evals_main
    sys.argv = ["optimize_skill_with_evals", *argv]
    raise SystemExit(optimize_evals_main())


def cmd_convert(argv):
    """Convert a HuggingFace dataset to SkillOpt eval format."""
    from scripts.convert_benchmark import main as convert_main
    sys.argv = ["convert_benchmark", *argv]
    raise SystemExit(convert_main())


COMMANDS = {
    "analyze": cmd_analyze,
    "optimize": cmd_optimize,
    "optimize-evals": cmd_optimize_evals,
    "convert": cmd_convert,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        print("\nSubcommands:")
        for name, fn in COMMANDS.items():
            print(f"  {name:<20} {fn.__doc__}")
        return 0

    cmd_name = sys.argv[1]
    if cmd_name not in COMMANDS:
        print(f"Unknown command: {cmd_name}")
        print(f"Available: {', '.join(COMMANDS)}")
        return 1

    COMMANDS[cmd_name](sys.argv[2:])


if __name__ == "__main__":
    sys.exit(main())
