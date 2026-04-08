"""Prompt parser for reading and writing skill.md and claude.md files."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass
class PromptSection:
    """A section within a prompt file."""

    title: str
    content: str
    level: int = 1  # Heading level (1 = #, 2 = ##, etc.)
    subsections: list["PromptSection"] = field(default_factory=list)


@dataclass
class PromptFile:
    """Parsed representation of a prompt markdown file."""

    path: Path
    frontmatter: dict[str, Any]
    title: Optional[str]
    description: Optional[str]
    sections: list[PromptSection]
    raw_content: str

    @property
    def name(self) -> str:
        """Get the filename without extension."""
        return self.path.stem

    def get_section(self, title: str) -> Optional[PromptSection]:
        """Find a section by title (case-insensitive)."""
        title_lower = title.lower()
        for section in self.sections:
            if section.title.lower() == title_lower:
                return section
            for subsection in section.subsections:
                if subsection.title.lower() == title_lower:
                    return subsection
        return None

    def get_full_text(self) -> str:
        """Get the full prompt text (excluding frontmatter)."""
        lines = []
        if self.title:
            lines.append(f"# {self.title}")
        if self.description:
            lines.append(f"\n{self.description}")
        for section in self.sections:
            lines.append(self._section_to_text(section))
        return "\n\n".join(lines)

    def _section_to_text(self, section: PromptSection) -> str:
        """Convert a section back to markdown text."""
        prefix = "#" * section.level
        lines = [f"{prefix} {section.title}", section.content]
        for subsection in section.subsections:
            lines.append(self._section_to_text(subsection))
        return "\n\n".join(filter(None, lines))


class PromptParser:
    """Parser for skill.md and claude.md prompt files."""

    FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    def parse_file(self, path: Path) -> PromptFile:
        """
        Parse a prompt markdown file.

        Args:
            path: Path to the markdown file

        Returns:
            PromptFile object with parsed content
        """
        with open(path, "r", encoding="utf-8") as f:
            raw_content = f.read()

        return self.parse_content(raw_content, path)

    def parse_content(self, content: str, path: Path = Path("unknown.md")) -> PromptFile:
        """
        Parse prompt content from a string.

        Args:
            content: Raw markdown content
            path: Optional path for reference

        Returns:
            PromptFile object with parsed content
        """
        # Extract frontmatter
        frontmatter = {}
        body = content

        frontmatter_match = self.FRONTMATTER_PATTERN.match(content)
        if frontmatter_match:
            try:
                frontmatter = yaml.safe_load(frontmatter_match.group(1)) or {}
            except yaml.YAMLError:
                frontmatter = {}
            body = content[frontmatter_match.end() :]

        # Extract title (first # heading)
        title = None
        description = None
        lines = body.strip().split("\n")
        content_start = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("# ") and title is None:
                title = stripped[2:].strip()
                content_start = i + 1
            elif title and not stripped.startswith("#") and stripped:
                # First non-heading, non-empty line after title is description
                description = stripped
                content_start = i + 1
                break
            elif stripped.startswith("#"):
                break

        # Parse sections
        remaining_content = "\n".join(lines[content_start:])
        sections = self._parse_sections(remaining_content)

        return PromptFile(
            path=path,
            frontmatter=frontmatter,
            title=title,
            description=description,
            sections=sections,
            raw_content=content,
        )

    def _parse_sections(self, content: str) -> list[PromptSection]:
        """Parse markdown content into sections."""
        sections: list[PromptSection] = []
        current_section: Optional[PromptSection] = None
        current_content_lines: list[str] = []

        lines = content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]
            heading_match = self.HEADING_PATTERN.match(line)

            if heading_match:
                # Save previous section content
                if current_section is not None:
                    current_section.content = "\n".join(current_content_lines).strip()

                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                new_section = PromptSection(title=title, content="", level=level)

                if level == 2:
                    # Top-level section
                    sections.append(new_section)
                    current_section = new_section
                elif level > 2 and current_section is not None:
                    # Subsection
                    current_section.subsections.append(new_section)
                else:
                    sections.append(new_section)
                    current_section = new_section

                current_content_lines = []
            else:
                current_content_lines.append(line)

            i += 1

        # Save final section content
        if current_section is not None:
            current_section.content = "\n".join(current_content_lines).strip()

        return sections

    def serialize(self, prompt: PromptFile) -> str:
        """
        Serialize a PromptFile back to markdown.

        Args:
            prompt: PromptFile to serialize

        Returns:
            Markdown string
        """
        parts = []

        # Frontmatter
        if prompt.frontmatter:
            parts.append("---")
            parts.append(yaml.dump(prompt.frontmatter, default_flow_style=False).strip())
            parts.append("---")
            parts.append("")

        # Title
        if prompt.title:
            parts.append(f"# {prompt.title}")
            parts.append("")

        # Description
        if prompt.description:
            parts.append(prompt.description)
            parts.append("")

        # Sections
        for section in prompt.sections:
            parts.append(self._serialize_section(section))
            parts.append("")

        return "\n".join(parts)

    def _serialize_section(self, section: PromptSection) -> str:
        """Serialize a single section to markdown."""
        prefix = "#" * section.level
        lines = [f"{prefix} {section.title}"]

        if section.content:
            lines.append("")
            lines.append(section.content)

        for subsection in section.subsections:
            lines.append("")
            lines.append(self._serialize_section(subsection))

        return "\n".join(lines)

    def update_section(
        self, prompt: PromptFile, section_title: str, new_content: str
    ) -> PromptFile:
        """
        Update a specific section's content.

        Args:
            prompt: PromptFile to update
            section_title: Title of section to update
            new_content: New content for the section

        Returns:
            Updated PromptFile
        """
        section = prompt.get_section(section_title)
        if section:
            section.content = new_content
        return prompt

    def add_section(
        self,
        prompt: PromptFile,
        title: str,
        content: str,
        level: int = 2,
        after_section: Optional[str] = None,
    ) -> PromptFile:
        """
        Add a new section to the prompt.

        Args:
            prompt: PromptFile to update
            title: Title for the new section
            content: Content for the new section
            level: Heading level (default 2 = ##)
            after_section: Insert after this section title (or at end if None)

        Returns:
            Updated PromptFile
        """
        new_section = PromptSection(title=title, content=content, level=level)

        if after_section:
            for i, section in enumerate(prompt.sections):
                if section.title.lower() == after_section.lower():
                    prompt.sections.insert(i + 1, new_section)
                    return prompt

        prompt.sections.append(new_section)
        return prompt


def load_prompts(prompts_dir: Path) -> dict[str, PromptFile]:
    """
    Load all prompt files from a directory.

    Args:
        prompts_dir: Directory containing prompt files

    Returns:
        Dictionary mapping filename to PromptFile
    """
    parser = PromptParser()
    prompts = {}

    for md_file in prompts_dir.glob("*.md"):
        prompts[md_file.stem] = parser.parse_file(md_file)

    return prompts


def save_prompt(prompt: PromptFile, path: Optional[Path] = None) -> None:
    """
    Save a PromptFile to disk.

    Args:
        prompt: PromptFile to save
        path: Optional path (uses prompt.path if not provided)
    """
    parser = PromptParser()
    save_path = path or prompt.path
    content = parser.serialize(prompt)

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(content)
