"""
app/langgraph/agents/planner.py
────────────────────────────────
Planner Agent
─────────────
Input : topic, user_preferences
Output: title, sections, research_required, research_tasks, estimated_word_count

Design: structured output via JSON-mode prompt + manual parse.
"""

from __future__ import annotations

import json
import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.langgraph.llm import get_llm
from app.langgraph.state import BlogState

SYSTEM_PROMPT = """You are an expert blog planner. Your job is to create a concise, well-structured plan for a high-quality blog post.

You will receive a topic and optional user preferences. Return ONLY a valid JSON object with this schema:

{
  "title": "<engaging blog title>",
  "sections": [
    {
      "title": "<section title>",
      "description": "<what this section covers>",
      "word_count": <target word count integer>
    }
  ],
  "research_required": <true|false>,
  "research_tasks": {<section_index>: "<specific research query>", ...},
  "estimated_word_count": <total integer>
}

Guidelines:

- Create 5–6 sections, including an Introduction and Conclusion.
- Focus on a logical flow that answers the user's topic comprehensively without unnecessary sections.
- Assign realistic word counts per section.
- Set research_required=true only when the topic requires external facts, statistics, studies, expert opinions, historical information, comparisons, or recent developments.
- Set research_required=false for opinion pieces, creative writing, personal reflections, tutorials based on common knowledge, or topics that can be answered without external research.
- Generate a maximum of 3 research tasks.
- Each research task should be broad enough to support multiple sections and avoid redundant searches.
- Do not create separate research tasks for every section.
- Align title, structure, tone, and depth with user preferences when provided.
- Estimated word count should equal the sum of all section word counts.
- Return ONLY the JSON object.
- Do not include markdown fences, explanations, notes, or additional text.
"""

def build_user_message(topic: str, preferences: dict[str, Any]) -> str:
    pref_str = ""
    if preferences:
        pref_str = f"""
User preferences:
- Tone: {preferences.get('preferred_tone', 'professional')}
- Style: {preferences.get('preferred_style', 'informative')}
- Target word count: {preferences.get('preferred_word_count', 1500)}
- Language: {preferences.get('preferred_language', 'English')}
- Technical depth: {preferences.get('technical_depth', 'intermediate')}
"""
    return f"Topic: {topic}{pref_str}"


async def run_planner(state: BlogState) -> dict:
    """LangGraph node: Planner."""
    t0 = time.monotonic()
    llm = get_llm(temperature=0.4)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=build_user_message(
            state["topic"],
            state.get("user_preferences", {}),
        )),
    ]

    response = await llm.ainvoke(messages)
    raw = response.content.strip()

    # Strip accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    plan: dict = json.loads(raw)

    latency = time.monotonic() - t0
    usage = response.response_metadata.get("token_usage", {})
    tokens = usage.get("total_tokens", 0)
    cost = _estimate_cost(tokens)

    metrics = state.get("metrics", {})
    node_latencies = metrics.get("node_latencies", {})
    node_latencies["planner"] = latency
    node_token = metrics.get("node_token", {})
    node_token["planner"] = tokens

    print(state.get("metrics", {}).get("node_latencies", {}))
    print(state.get("metrics", {}).get("node_token", {}))

    return {
        "title": plan["title"],
        "sections": plan["sections"],
        "research_required": plan.get("research_required", False),
        "research_tasks": plan.get("research_tasks", {}),
        "estimated_word_count": plan.get("estimated_word_count", 1500),
        "status": "awaiting_approval",
        "current_node": "human_approval",
        "metrics": {
            **metrics,
            "total_tokens": metrics.get("total_tokens", 0) + tokens,
            "total_cost": metrics.get("total_cost", 0.0) + cost,
            "node_latencies": node_latencies,
            "node_token": node_token
        },
    }


def _estimate_cost(tokens: int) -> float:
    """Rough openai/gpt-oss-120b cost estimation: $0.25 / 1M input tokens."""
    return tokens * 0.25 / 1_000_000