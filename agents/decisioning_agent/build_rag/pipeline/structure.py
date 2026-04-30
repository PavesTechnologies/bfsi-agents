"""
STAGE 2: Reconstruct document hierarchy from a flat element list.

Regulatory docs nest deeply (Chapter -> Section -> Sub-section -> Clause).
Without this tree, a chunk that says "subject to (a) above" loses meaning.
Every element ends up tagged with its full breadcrumb so chunks remain
self-contained.
"""

from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class SectionNode:
    title: str
    level: int
    section_number: Optional[str] = None
    elements: list = field(default_factory=list)
    children: list = field(default_factory=list)
    parent: Optional["SectionNode"] = None
    page_start: int = 0
    page_end: int = 0

    @property
    def breadcrumb(self) -> str:
        parts = []
        node: Optional["SectionNode"] = self
        while node:
            parts.append(node.title)
            node = node.parent
        return " > ".join(reversed(parts))

    @property
    def section_summary(self) -> str:
        all_text = " ".join(
            e.text for e in self.elements if e.element_type == "NarrativeText"
        )
        return all_text[:200] + "..." if len(all_text) > 200 else all_text


def build_section_tree(elements: list) -> list[SectionNode]:
    """
    Walk parsed elements and assemble a section hierarchy.

    Title elements open new sections; non-title elements attach to the
    most recent section. Heading level comes from the numbering pattern.
    """
    root_sections: list[SectionNode] = []
    section_stack: list[SectionNode] = []
    current_section: Optional[SectionNode] = None

    for elem in elements:
        if elem.element_type == "Title":
            level = _detect_heading_level(elem.text)
            section_num = _extract_section_number(elem.text)

            new_section = SectionNode(
                title=elem.text.strip(),
                level=level,
                section_number=section_num,
                page_start=elem.page_number,
            )

            while section_stack and section_stack[-1].level >= level:
                section_stack.pop()

            if section_stack:
                parent = section_stack[-1]
                new_section.parent = parent
                parent.children.append(new_section)
            else:
                root_sections.append(new_section)

            section_stack.append(new_section)
            current_section = new_section

        else:
            if current_section is None:
                # Orphan element before any heading — wrap in a synthetic root.
                current_section = SectionNode(title="(preamble)", level=0)
                root_sections.append(current_section)
            current_section.elements.append(elem)
            current_section.page_end = elem.page_number

    return root_sections


def _detect_heading_level(text: str) -> int:
    text = text.strip()

    if re.match(r"^(chapter|CHAPTER)\s", text, re.IGNORECASE):
        return 0
    if re.match(r"^\d+\.\d+\.\d+", text):
        return 2
    if re.match(r"^\d+\.\d+", text):
        return 1
    if re.match(r"^\d+\s", text):
        return 0
    if re.match(r"^\([a-z]\)", text):
        return 3
    return 1


def _extract_section_number(text: str) -> Optional[str]:
    match = re.match(r"^(\d+(?:\.\d+)*)", text.strip())
    return match.group(1) if match else None


def flatten_with_context(root_sections: list[SectionNode]) -> list[dict]:
    """
    Walk the tree and emit one dict per element, each carrying its
    full breadcrumb / section / chapter context.
    """
    result: list[dict] = []

    def _walk(node: SectionNode):
        for elem in node.elements:
            result.append({
                "element": elem,
                "breadcrumb": node.breadcrumb,
                "section_number": node.section_number,
                "section_title": node.title,
                "parent_summary": node.parent.section_summary if node.parent else "",
                "chapter": _get_chapter(node),
                "page": elem.page_number,
            })
        for child in node.children:
            _walk(child)

    for section in root_sections:
        _walk(section)

    return result


def _get_chapter(node: SectionNode) -> str:
    while node.parent:
        node = node.parent
    return node.title
