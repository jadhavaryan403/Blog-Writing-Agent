"""
app/langgraph/agents/section_editor.py
────────────────────────────────────────
Section Editor Agent
─────────────────────
Receives the full blog context + a user edit instruction for one section.
Rewrites ONLY that section, preserving factual accuracy, citations, and
consistency with surrounding sections.

Design: single LLM call with a richly-structured prompt.
Returns only the updated section markdown body (no heading).
"""

from __future__ import annotations

import time

from langchain_core.messages import HumanMessage, SystemMessage

from app.langgraph.llm import get_llm
from app.langgraph.state import SectionDict, ResearchResultDict, CitationDict

SYSTEM_PROMPT = """You are an expert blog editor. You will receive:
- The full blog title and outline (all section titles)
- The current content of ONE specific section
- Research notes used when writing that section (may be empty)
- A natural-language edit instruction from the user

Your task: rewrite ONLY the specified section following the instruction precisely.

Rules:
1. Return ONLY the revised markdown body — no section heading, no preamble, no explanation.
2. Preserve all factual accuracy; do not invent statistics or claims.
3. Keep existing inline citations ([Title](URL)) unless the instruction explicitly removes them.
4. Maintain consistent tone, terminology, and voice with the rest of the blog.
5. Match the target word count of the original section (± 10%) unless instructed otherwise.
6. Do not modify any other section.
7. If the instruction is ambiguous, apply the most reasonable interpretation."""


def _build_outline(sections: list[SectionDict]) -> str:
    '''Format the full blog outline for inclusion in the prompt.'''
    return "\n".join(
        f"  {i}. {section.get('title', f'Section {i}')}"
        for i, section in enumerate(sections, start=1)
    )


def _find_research_for_section(
    section_idx: int,
    research_results: list[ResearchResultDict],
    citations: list[CitationDict],
) -> str:
    """
    Compile relevant research notes and citations for a specific section.
    Since research results aren't indexed per-section, we include all research
    notes (they are short) and citations tagged for this section.
    """
    parts: list[str] = []

    if research_results:
        parts.append("### Research Notes")
        for r in research_results:
            parts.append(f"**Query:** {r.get('task', '')}")
            parts.append(r.get("content", "")[:5000])   # truncate long results

    section_cites = [
        c for c in citations
        if c.get("section_idx") == section_idx or c.get("section_idx") == -1
    ]
    if section_cites:
        parts.append("\n### Available Citations")
        for c in section_cites:
            parts.append(f"- [{c.get('source_title', 'Source')}]({c.get('source_url', '')})")

    return "\n".join(parts) if parts else "No specific research available."


def _build_user_message(
    blog_title: str,
    sections: list[SectionDict],
    section_idx: int,
    research_notes: str,
    instruction: str,
) -> str:
    target = sections[section_idx]

    return f"""BLOG TITLE: {blog_title}

FULL OUTLINE:
{_build_outline(sections)}

TARGET SECTION ({section_idx + 1} of {len(sections)}): "{target.get('title', '')}"
Target word count: ~{target.get('word_count', 300)} words

CURRENT SECTION CONTENT:
---
{target.get('draft', '(empty)')}
---

RESEARCH NOTES:
{research_notes}

USER EDIT INSTRUCTION:
{instruction}

Now rewrite the section following the instruction. Return only the revised markdown body:"""


async def edit_section(
    blog_title: str,
    sections: list[SectionDict],
    section_idx: int,
    instruction: str,
    research_results: list[ResearchResultDict],
    citations: list[CitationDict],
) -> tuple[str, dict]:
    """
    Run the section editor LLM call.

    Returns:
        (updated_draft: str, usage_metadata: dict)
    """
    t0 = time.monotonic()
    llm = get_llm(temperature=0.5)

    research_notes = _find_research_for_section(section_idx, research_results, citations)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=_build_user_message(
            blog_title=blog_title,
            sections=sections,
            section_idx=section_idx,
            research_notes=research_notes,
            instruction=instruction,
        )),
    ]

    response = await llm.ainvoke(messages)
    latency = time.monotonic() - t0
    usage   = response.response_metadata.get("token_usage", {})

    return response.content.strip(), {
        "tokens":  usage.get("total_tokens", 0),
        "cost":    usage.get("total_tokens", 0) * 0.25 / 1_000_000,
        "latency": latency,
    }