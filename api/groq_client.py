"""Groq API client — ultra-fast LLM inference."""
from __future__ import annotations

import os
import logging
from typing import Optional

try:
    from groq import Groq
except ImportError:
    Groq = None

logger = logging.getLogger(__name__)

class GroqClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY not set")
        if Groq is None:
            raise RuntimeError("groq package not installed. Run: pip install groq")
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"
        logger.info("[API] Groq client initialized")

    def generate(self, prompt: str, max_tokens: int = 2048, temperature: float = 0.7) -> str:
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            logger.error("[API] Groq error: %s", e)
            raise

    def generate_ideas(self, topic: str, category: str, count: int = 5) -> list[dict]:
        prompt = f"""Generate {count} viral short-form video content ideas for category: {category}.
Topic: {topic}

For each idea, provide:
- hook: Attention-grabbing first line (max 15 words)
- body: Brief outline (2-3 sentences)
- cta: Call-to-action
- content_type: trend | evergreen | experimental | repeatable_series
- estimated_duration: in seconds (15-90)

Return ONLY valid JSON array format:
[{{"hook": "...", "body": "...", "cta": "...", "content_type": "...", "estimated_duration": 30}}]
"""
        raw = self.generate(prompt, max_tokens=3000, temperature=0.8)
        import json
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0]
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0]
            return json.loads(raw.strip())
        except json.JSONDecodeError as e:
            logger.error("[API] Failed to parse Groq response: %s", e)
            return []

    def generate_script(self, hook: str, body: str, duration: int) -> dict:
        prompt = f"""Write a viral short-form video script.

Hook: {hook}
Body outline: {body}
Target duration: {duration} seconds

Provide:
- hook_line: The exact opening hook (max 5 seconds when spoken)
- script_body: Main content, timed for {duration}s
- cta_line: Strong call-to-action
- visual_notes: Key visual cues for each segment

Return ONLY valid JSON:
{{"hook_line": "...", "script_body": "...", "cta_line": "...", "visual_notes": "..."}}
"""
        raw = self.generate(prompt, max_tokens=2500, temperature=0.7)
        import json
        try:
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0]
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0]
            return json.loads(raw.strip())
        except json.JSONDecodeError:
            return {"hook_line": hook, "script_body": body, "cta_line": "Follow for more!", "visual_notes": ""}
