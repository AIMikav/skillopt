"""SkillOpt - Skill Optimizer using GEPA and best practices analysis."""

__version__ = "0.3.0"

from skillopt.prompt_parser import PromptFile, PromptParser, PromptSection
from skillopt.skill_parser import SkillFile, SkillParser, SkillReference
from skillopt.skill_analyzer import SkillAnalyzer, AnalysisReport, Issue, BashCommand
from skillopt.trajectory import TrajectoryLogger
from skillopt.benchmarks import load_benchmark, load_tau_bench, load_swe_bench, load_searchqa

__all__ = [
    "PromptFile",
    "PromptParser",
    "PromptSection",
    "SkillFile",
    "SkillParser",
    "SkillReference",
    "SkillAnalyzer",
    "AnalysisReport",
    "Issue",
    "BashCommand",
    "TrajectoryLogger",
    "load_benchmark",
    "load_tau_bench",
    "load_swe_bench",
    "load_searchqa",
]
