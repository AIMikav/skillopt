"""Skill analyzer based on Claude Agent Skills best practices.

Analyzes skills against official guidelines:
- Conciseness (avoid verbose explanations)
- Progressive disclosure (SKILL.md < 500 lines)
- Degrees of freedom (match specificity to task)
- Structure (TOC for long files, one-level references)
- Patterns (workflows, templates, examples)
- Scripts (utility scripts, error handling)
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from skillopt.skill_parser import SkillFile


@dataclass
class Issue:
    """An issue found during skill analysis."""

    severity: str  # "error", "warning", "suggestion"
    category: str  # e.g., "conciseness", "structure", "workflow"
    message: str
    location: str  # file:line or file reference
    suggestion: str
    estimated_token_savings: int = 0


@dataclass
class BashCommand:
    """A bash command found in the skill."""

    command: str
    location: str
    can_be_scripted: bool
    similar_commands: list[str] = field(default_factory=list)


@dataclass
class AnalysisReport:
    """Report from analyzing a skill against best practices."""

    skill_name: str
    main_file_lines: int
    total_lines: int
    estimated_tokens: int
    issues: list[Issue]
    bash_commands: list[BashCommand]
    score: float  # 0-100, higher is better
    summary: str


class SkillAnalyzer:
    """
    Analyzes skills against Claude Agent Skills best practices.

    Checks for:
    1. Conciseness - Remove filler phrases, unnecessary explanations
    2. Structure - SKILL.md < 500 lines, one-level references, TOC
    3. Workflows - Clear steps with checklists for complex tasks
    4. Scripts - Extract repetitive bash commands to scripts/
    5. Terminology - Consistent terms throughout
    """

    # Filler phrases to flag (from best practices)
    FILLER_PHRASES = [
        r"make sure to",
        r"ensure that",
        r"don't forget to",
        r"remember to",
        r"it is important to",
        r"please note that",
        r"keep in mind",
        r"you should",
        r"you need to",
        r"you must",
        r"you can",
        r"you'll need to",
        r"first,? you'll",
    ]

    # Verbose explanation patterns
    VERBOSE_PATTERNS = [
        (r"PDF \(Portable Document Format\)", "Assumes Claude doesn't know what PDF is"),
        (r"(?:YAML|JSON|XML) is a (?:format|markup)", "Assumes Claude doesn't know formats"),
        (r"Kubernetes is (?:a|an)", "Assumes Claude doesn't know Kubernetes"),
        (r"(?:This|The) (?:library|tool|utility) (?:is|allows)", "Unnecessary library intro"),
    ]

    # Bash command patterns
    BASH_BLOCK = re.compile(r"```(?:bash|sh|shell)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
    INLINE_CMD = re.compile(r"`([^`]*(?:kubectl|oc|git|curl|helm|docker|python|pip)[^`]*)`")

    # Tokens per character estimate
    TOKENS_PER_CHAR = 0.25

    def __init__(self):
        self.filler_pattern = re.compile("|".join(self.FILLER_PHRASES), re.IGNORECASE)

    def analyze(self, skill: SkillFile) -> AnalysisReport:
        """Analyze a skill against best practices."""
        issues: list[Issue] = []
        bash_commands: list[BashCommand] = []

        main_content = skill.main_file.raw_content
        main_lines = len(main_content.split("\n"))
        total_lines = skill.total_lines
        estimated_tokens = int(len(skill.get_full_content()) * self.TOKENS_PER_CHAR)

        # Check SKILL.md line count (should be < 500)
        if main_lines > 500:
            issues.append(Issue(
                severity="error",
                category="structure",
                message=f"SKILL.md has {main_lines} lines, should be under 500",
                location="SKILL.md",
                suggestion="Move detailed content to separate reference files",
                estimated_token_savings=int((main_lines - 500) * 10 * self.TOKENS_PER_CHAR),
            ))
        elif main_lines > 300:
            issues.append(Issue(
                severity="warning",
                category="structure",
                message=f"SKILL.md has {main_lines} lines, approaching 500 limit",
                location="SKILL.md",
                suggestion="Consider splitting content to references proactively",
            ))

        # Check for filler phrases
        issues.extend(self._check_filler_phrases(skill))

        # Check for verbose explanations
        issues.extend(self._check_verbose_patterns(skill))

        # Check reference structure (one-level deep)
        issues.extend(self._check_reference_depth(skill))

        # Check for TOC in long files
        issues.extend(self._check_toc_needed(skill))

        # Check for workflow structure
        issues.extend(self._check_workflow_patterns(skill))

        # Extract and analyze bash commands
        bash_commands = self._extract_bash_commands(skill)
        issues.extend(self._check_bash_patterns(bash_commands))

        # Check frontmatter
        issues.extend(self._check_frontmatter(skill))

        # Check terminology consistency
        issues.extend(self._check_terminology(skill))

        # Calculate score
        score = self._calculate_score(issues, main_lines, bash_commands)

        # Generate summary
        summary = self._generate_summary(issues, bash_commands, score)

        return AnalysisReport(
            skill_name=skill.name,
            main_file_lines=main_lines,
            total_lines=total_lines,
            estimated_tokens=estimated_tokens,
            issues=issues,
            bash_commands=bash_commands,
            score=score,
            summary=summary,
        )

    def _check_filler_phrases(self, skill: SkillFile) -> list[Issue]:
        """Check for filler phrases that should be removed."""
        issues = []
        content = skill.get_full_content()

        matches = list(self.filler_pattern.finditer(content))
        if matches:
            # Group by phrase type
            phrase_counts: dict[str, int] = {}
            for match in matches:
                phrase = match.group().lower()
                phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1

            for phrase, count in phrase_counts.items():
                issues.append(Issue(
                    severity="warning",
                    category="conciseness",
                    message=f"Filler phrase '{phrase}' appears {count} time(s)",
                    location="multiple locations",
                    suggestion=f"Remove or rewrite without '{phrase}'",
                    estimated_token_savings=count * 3,
                ))

        return issues

    def _check_verbose_patterns(self, skill: SkillFile) -> list[Issue]:
        """Check for verbose explanations that assume Claude doesn't know basics."""
        issues = []
        content = skill.get_full_content()

        for pattern, reason in self.VERBOSE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(Issue(
                    severity="warning",
                    category="conciseness",
                    message=reason,
                    location="SKILL.md or references",
                    suggestion="Remove explanation - Claude already knows this",
                    estimated_token_savings=20,
                ))

        return issues

    def _check_reference_depth(self, skill: SkillFile) -> list[Issue]:
        """Check that references are one level deep from SKILL.md."""
        issues = []

        # Check for nested references in reference files
        nested_pattern = re.compile(r"\[.*?\]\((?!https?://|#)([^)]+\.md)\)", re.IGNORECASE)

        for ref in skill.references:
            matches = nested_pattern.findall(ref.content)
            if matches:
                issues.append(Issue(
                    severity="warning",
                    category="structure",
                    message=f"Reference {ref.filename} links to other files: {', '.join(matches)}",
                    location=ref.filename,
                    suggestion="Keep references one level deep from SKILL.md",
                ))

        return issues

    def _check_toc_needed(self, skill: SkillFile) -> list[Issue]:
        """Check if long files need a table of contents."""
        issues = []

        for ref in skill.references:
            if ref.line_count > 100:
                # Check if TOC exists
                has_toc = (
                    "## contents" in ref.content.lower()
                    or "## table of contents" in ref.content.lower()
                    or "- [" in ref.content[:500]  # Links at top
                )
                if not has_toc:
                    issues.append(Issue(
                        severity="suggestion",
                        category="structure",
                        message=f"{ref.filename} has {ref.line_count} lines but no TOC",
                        location=ref.filename,
                        suggestion="Add table of contents for files over 100 lines",
                    ))

        return issues

    def _check_workflow_patterns(self, skill: SkillFile) -> list[Issue]:
        """Check for workflow and checklist patterns."""
        issues = []
        content = skill.main_file.raw_content.lower()

        # Check if skill has multi-step instructions but no checklist
        has_steps = re.search(r"step \d|^\d+\.", content, re.MULTILINE)
        has_checklist = "- [ ]" in content or "- [x]" in content

        if has_steps and not has_checklist:
            issues.append(Issue(
                severity="suggestion",
                category="workflow",
                message="Multi-step workflow without checklist",
                location="SKILL.md",
                suggestion="Add checklist for complex workflows to track progress",
            ))

        # Check for validation/feedback loops
        has_validate = "validate" in content or "verify" in content
        has_loop = "if" in content and ("fail" in content or "error" in content)

        if has_steps and not (has_validate and has_loop):
            issues.append(Issue(
                severity="suggestion",
                category="workflow",
                message="Workflow may lack validation feedback loop",
                location="SKILL.md",
                suggestion="Add validation step and retry logic for critical operations",
            ))

        return issues

    def _extract_bash_commands(self, skill: SkillFile) -> list[BashCommand]:
        """Extract all bash commands from the skill."""
        commands: list[BashCommand] = []
        all_content = [(skill.main_file.raw_content, "SKILL.md")]

        for ref in skill.references:
            all_content.append((ref.content, ref.filename))

        for content, source in all_content:
            # Extract from code blocks
            for match in self.BASH_BLOCK.finditer(content):
                block = match.group(1).strip()
                for line in block.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        commands.append(BashCommand(
                            command=line,
                            location=f"{source}:block",
                            can_be_scripted=self._can_be_scripted(line),
                        ))

            # Extract inline commands
            for match in self.INLINE_CMD.finditer(content):
                cmd = match.group(1)
                commands.append(BashCommand(
                    command=cmd,
                    location=f"{source}:inline",
                    can_be_scripted=self._can_be_scripted(cmd),
                ))

        # Group similar commands
        self._group_similar_commands(commands)

        return commands

    def _can_be_scripted(self, command: str) -> bool:
        """Check if command can be extracted to a script."""
        scriptable = ["kubectl", "oc", "helm", "git", "curl", "docker", "podman"]
        return any(cmd in command for cmd in scriptable)

    def _group_similar_commands(self, commands: list[BashCommand]) -> None:
        """Find and group similar commands."""
        templates: dict[str, list[BashCommand]] = {}

        for cmd in commands:
            # Create template by generalizing variable parts
            template = re.sub(r'"[^"]*"', '"<VAR>"', cmd.command)
            template = re.sub(r"'[^']*'", "'<VAR>'", template)
            template = re.sub(r"-n\s+\S+", "-n <NS>", template)

            if template not in templates:
                templates[template] = []
            templates[template].append(cmd)

        # Mark similar commands
        for template, cmds in templates.items():
            if len(cmds) > 1:
                for cmd in cmds:
                    cmd.similar_commands = [c.command for c in cmds if c != cmd]

    def _check_bash_patterns(self, commands: list[BashCommand]) -> list[Issue]:
        """Check for bash patterns that should be extracted to scripts."""
        issues = []

        # Find commands that appear multiple times
        scriptable_groups: dict[str, list[BashCommand]] = {}
        for cmd in commands:
            if cmd.can_be_scripted and cmd.similar_commands:
                key = cmd.command.split()[0]  # Group by base command
                if key not in scriptable_groups:
                    scriptable_groups[key] = []
                scriptable_groups[key].append(cmd)

        for base_cmd, cmds in scriptable_groups.items():
            if len(cmds) >= 2:
                issues.append(Issue(
                    severity="suggestion",
                    category="scripts",
                    message=f"Found {len(cmds)} similar {base_cmd} commands",
                    location="multiple locations",
                    suggestion=f"Extract to scripts/{base_cmd}_helper.sh",
                    estimated_token_savings=len(cmds) * 10,
                ))

        return issues

    def _check_frontmatter(self, skill: SkillFile) -> list[Issue]:
        """Check YAML frontmatter requirements."""
        issues = []
        fm = skill.main_file.frontmatter

        # Check name
        name = fm.get("name", "")
        if not name:
            issues.append(Issue(
                severity="error",
                category="frontmatter",
                message="Missing required 'name' field",
                location="SKILL.md frontmatter",
                suggestion="Add name field (max 64 chars, lowercase, hyphens)",
            ))
        elif len(name) > 64:
            issues.append(Issue(
                severity="error",
                category="frontmatter",
                message=f"Name '{name}' exceeds 64 characters",
                location="SKILL.md frontmatter",
                suggestion="Shorten name to max 64 characters",
            ))
        elif not re.match(r"^[a-z0-9-]+$", name):
            issues.append(Issue(
                severity="error",
                category="frontmatter",
                message=f"Name '{name}' contains invalid characters",
                location="SKILL.md frontmatter",
                suggestion="Use only lowercase letters, numbers, and hyphens",
            ))

        # Check description
        desc = fm.get("description", "")
        if not desc:
            issues.append(Issue(
                severity="error",
                category="frontmatter",
                message="Missing required 'description' field",
                location="SKILL.md frontmatter",
                suggestion="Add description with what skill does AND when to use it",
            ))
        elif len(desc) > 1024:
            issues.append(Issue(
                severity="error",
                category="frontmatter",
                message=f"Description exceeds 1024 characters ({len(desc)})",
                location="SKILL.md frontmatter",
                suggestion="Shorten description to max 1024 characters",
            ))
        elif desc and not any(w in desc.lower() for w in ["use when", "use for", "when"]):
            issues.append(Issue(
                severity="warning",
                category="frontmatter",
                message="Description may not explain when to use the skill",
                location="SKILL.md frontmatter",
                suggestion="Add 'Use when...' to help Claude discover the skill",
            ))

        return issues

    def _check_terminology(self, skill: SkillFile) -> list[Issue]:
        """Check for inconsistent terminology."""
        issues = []
        content = skill.get_full_content().lower()

        # Common term variations to check
        term_groups = [
            (["api endpoint", "url", "api route", "path"], "API endpoint"),
            (["field", "box", "element", "control"], "field"),
            (["extract", "pull", "get", "retrieve"], "extract"),
        ]

        for variants, preferred in term_groups:
            found = [v for v in variants if v in content]
            if len(found) > 1:
                issues.append(Issue(
                    severity="suggestion",
                    category="terminology",
                    message=f"Inconsistent terms: {', '.join(found)}",
                    location="multiple locations",
                    suggestion=f"Use '{preferred}' consistently throughout",
                ))

        return issues

    def _calculate_score(
        self,
        issues: list[Issue],
        main_lines: int,
        bash_commands: list[BashCommand],
    ) -> float:
        """Calculate overall skill quality score (0-100)."""
        score = 100.0

        # Deduct for issues
        for issue in issues:
            if issue.severity == "error":
                score -= 15
            elif issue.severity == "warning":
                score -= 5
            elif issue.severity == "suggestion":
                score -= 2

        # Bonus for good structure
        if main_lines < 300:
            score += 5
        if main_lines < 200:
            score += 5

        # Penalty for no scripts when many bash commands
        scriptable = [c for c in bash_commands if c.can_be_scripted]
        if len(scriptable) > 5:
            score -= 10

        return max(0, min(100, score))

    def _generate_summary(
        self,
        issues: list[Issue],
        bash_commands: list[BashCommand],
        score: float,
    ) -> str:
        """Generate a summary of the analysis."""
        errors = len([i for i in issues if i.severity == "error"])
        warnings = len([i for i in issues if i.severity == "warning"])
        suggestions = len([i for i in issues if i.severity == "suggestion"])
        scriptable = len([c for c in bash_commands if c.can_be_scripted])

        parts = [f"Score: {score:.0f}/100"]

        if errors:
            parts.append(f"{errors} error(s)")
        if warnings:
            parts.append(f"{warnings} warning(s)")
        if suggestions:
            parts.append(f"{suggestions} suggestion(s)")
        if scriptable > 3:
            parts.append(f"{scriptable} commands could be scripted")

        return " | ".join(parts)
