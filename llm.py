"""
LLM Service — Anthropic Claude
Generates a 3-step personalised study plan based on session performance.
"""

import os
import json
import anthropic
from typing import List
from app.models.schemas import ResponseRecord


def build_prompt(
    student_name: str,
    final_ability: float,
    responses: List[ResponseRecord],
    weak_topics: List[str],
    score_pct: float,
) -> str:
    summary_lines = []
    for r in responses:
        status = "✓" if r.correct else "✗"
        summary_lines.append(
            f"  {status} Topic: {r.topic}, Difficulty: {r.difficulty:.2f}"
        )
    summary = "\n".join(summary_lines)

    return f"""
You are an expert GRE tutor and learning coach.

A student named {student_name} just completed an adaptive GRE diagnostic test.
Here is their performance summary:

- Final Ability Score (0–1 scale): {final_ability:.2f}
- Questions Answered: {len(responses)}
- Accuracy: {score_pct:.1f}%
- Weak Topics: {', '.join(weak_topics) if weak_topics else 'None identified'}

Detailed question log:
{summary}

Based on this data, generate a concise and actionable 3-step personalized study plan.
Return ONLY a valid JSON object with NO extra text or markdown, in this exact structure:

{{
  "steps": [
    {{
      "step": 1,
      "title": "Short title",
      "focus": "Topic or skill to focus on",
      "action": "Specific actionable recommendation (2-3 sentences)",
      "resources": ["resource 1", "resource 2"]
    }},
    {{
      "step": 2,
      "title": "Short title",
      "focus": "Topic or skill to focus on",
      "action": "Specific actionable recommendation (2-3 sentences)",
      "resources": ["resource 1", "resource 2"]
    }},
    {{
      "step": 3,
      "title": "Short title",
      "focus": "Topic or skill to focus on",
      "action": "Specific actionable recommendation (2-3 sentences)",
      "resources": ["resource 1", "resource 2"]
    }}
  ]
}}
""".strip()


def generate_study_plan(
    student_name: str,
    final_ability: float,
    responses: List[ResponseRecord],
) -> List[dict]:
    """Call Anthropic API and return parsed 3-step study plan."""
    weak_topics = _identify_weak_topics(responses)
    correct = sum(1 for r in responses if r.correct)
    score_pct = (correct / len(responses) * 100) if responses else 0.0

    prompt = build_prompt(student_name, final_ability, responses, weak_topics, score_pct)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY not set in environment variables.")

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    parsed = json.loads(raw)
    return parsed.get("steps", [])


def _identify_weak_topics(responses: List[ResponseRecord]) -> List[str]:
    """Return topics where the student got < 50% correct."""
    topic_stats: dict = {}
    for r in responses:
        if r.topic not in topic_stats:
            topic_stats[r.topic] = {"correct": 0, "total": 0}
        topic_stats[r.topic]["total"] += 1
        if r.correct:
            topic_stats[r.topic]["correct"] += 1

    weak = [
        topic
        for topic, stats in topic_stats.items()
        if stats["total"] > 0 and stats["correct"] / stats["total"] < 0.5
    ]
    return weak
