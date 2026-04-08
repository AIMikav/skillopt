"""Skill parser for reading and writing skill directories with references."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from skillopt.prompt_parser import PromptFile, PromptParser


@dataclass
class SkillReference:
    """A reference file within a skill's references directory."""

    name: str  # Filename without extension
    path: Path
    content: str
    line_count: int

    @property
    def filename(self) -> str:
        """Get the filename with extension."""
        return self.path.name


@dataclass
class SkillFile:
    """A complete skill with main file and references."""

    name: str
    path: Path  # Path to skill directory
    main_file: PromptFile  # SKILL.md parsed content
    references: list[SkillReference] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_lines(self) -> int:
        """Get total line count across all files."""
        main_lines = len(self.main_file.raw_content.split("\n"))
        ref_lines = sum(r.line_count for r in self.references)
        return main_lines + ref_lines

    @property
    def reference_names(self) -> list[str]:
        """Get list of reference file names."""
        return [r.name for r in self.references]

    def get_reference(self, name: str) -> Optional[SkillReference]:
        """Get a reference by name (case-insensitive)."""
        name_lower = name.lower().replace(".md", "")
        for ref in self.references:
            if ref.name.lower() == name_lower:
                return ref
        return None

    def get_full_content(self) -> str:
        """Get concatenated content of main file and all references."""
        parts = [self.main_file.raw_content]
        for ref in self.references:
            parts.append(f"\n\n# Reference: {ref.filename}\n\n{ref.content}")
        return "\n".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert skill to dictionary representation."""
        return {
            "name": self.name,
            "path": str(self.path),
            "total_lines": self.total_lines,
            "main_file": {
                "title": self.main_file.title,
                "sections": [s.title for s in self.main_file.sections],
            },
            "references": [
                {"name": r.name, "lines": r.line_count} for r in self.references
            ],
            "metadata": self.metadata,
        }


class SkillParser:
    """Parser for skill directories containing SKILL.md and references/."""

    SKILL_FILENAME = "SKILL.md"
    REFERENCES_DIR = "references"

    def __init__(self):
        self.prompt_parser = PromptParser()

    def parse_directory(self, skill_dir: Path) -> SkillFile:
        """
        Parse a skill directory.

        Expected structure:
            skill-name/
            ├── SKILL.md
            └── references/
                ├── TEMPLATES.md
                ├── MAPPINGS.md
                └── EXAMPLES.md

        Args:
            skill_dir: Path to the skill directory

        Returns:
            SkillFile object with parsed content
        """
        skill_dir = Path(skill_dir)
        if not skill_dir.is_dir():
            raise ValueError(f"Not a directory: {skill_dir}")

        # Parse main SKILL.md
        main_path = skill_dir / self.SKILL_FILENAME
        if not main_path.exists():
            raise ValueError(f"Missing {self.SKILL_FILENAME} in {skill_dir}")

        main_file = self.prompt_parser.parse_file(main_path)

        # Parse references
        references = []
        refs_dir = skill_dir / self.REFERENCES_DIR
        if refs_dir.exists() and refs_dir.is_dir():
            for ref_path in sorted(refs_dir.glob("*.md")):
                content = ref_path.read_text(encoding="utf-8")
                references.append(
                    SkillReference(
                        name=ref_path.stem,
                        path=ref_path,
                        content=content,
                        line_count=len(content.split("\n")),
                    )
                )

        # Extract metadata from frontmatter
        metadata = main_file.frontmatter.copy()
        metadata["skill_name"] = skill_dir.name

        return SkillFile(
            name=skill_dir.name,
            path=skill_dir,
            main_file=main_file,
            references=references,
            metadata=metadata,
        )

    def save_skill(self, skill: SkillFile, output_dir: Optional[Path] = None) -> Path:
        """
        Save a skill to disk.

        Args:
            skill: SkillFile to save
            output_dir: Optional output directory (uses skill.path if not provided)

        Returns:
            Path to the saved skill directory
        """
        save_dir = output_dir or skill.path
        save_dir.mkdir(parents=True, exist_ok=True)

        # Save main file
        main_content = self.prompt_parser.serialize(skill.main_file)
        (save_dir / self.SKILL_FILENAME).write_text(main_content, encoding="utf-8")

        # Save references
        if skill.references:
            refs_dir = save_dir / self.REFERENCES_DIR
            refs_dir.mkdir(exist_ok=True)
            for ref in skill.references:
                (refs_dir / ref.filename).write_text(ref.content, encoding="utf-8")

        return save_dir

    def create_skill(
        self,
        name: str,
        title: str,
        workflow: str,
        references: Optional[dict[str, str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> SkillFile:
        """
        Create a new skill programmatically.

        Args:
            name: Skill directory name
            title: Skill title for SKILL.md
            workflow: Main workflow content
            references: Dict of {filename: content} for references
            metadata: Optional metadata dict

        Returns:
            SkillFile object (not saved to disk)
        """
        # Create main file content
        main_content = f"# {title}\n\n{workflow}"
        main_file = self.prompt_parser.parse_content(
            main_content, Path(name) / self.SKILL_FILENAME
        )

        # Create reference objects
        ref_objects = []
        if references:
            for ref_name, ref_content in references.items():
                filename = ref_name if ref_name.endswith(".md") else f"{ref_name}.md"
                ref_objects.append(
                    SkillReference(
                        name=ref_name.replace(".md", ""),
                        path=Path(name) / self.REFERENCES_DIR / filename,
                        content=ref_content,
                        line_count=len(ref_content.split("\n")),
                    )
                )

        return SkillFile(
            name=name,
            path=Path(name),
            main_file=main_file,
            references=ref_objects,
            metadata=metadata or {},
        )


def load_skills(skills_dir: Path) -> dict[str, SkillFile]:
    """
    Load all skills from a directory.

    Args:
        skills_dir: Directory containing skill subdirectories

    Returns:
        Dictionary mapping skill name to SkillFile
    """
    parser = SkillParser()
    skills = {}

    for item in skills_dir.iterdir():
        if item.is_dir() and (item / SkillParser.SKILL_FILENAME).exists():
            try:
                skills[item.name] = parser.parse_directory(item)
            except ValueError:
                continue

    return skills
