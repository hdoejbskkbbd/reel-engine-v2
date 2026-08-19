"""Google Gemini API client."""
from __future__ import annotations

import os
import logging
from typing import Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        if genai is None:
            raise RuntimeError("google-generativeai not installed. Run: pip install google-generativeai")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        logger.info("[API] Gemini client initialized")

    def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        try:
            resp = self.model.generate_content(prompt)
            return resp.text or ""
        except Exception as e:
            logger.error("[API] Gemini error: %s", e)
            raise

    def analyze_trend(self, topic: str, raw_data: str) -> dict:
        prompt = f"""Analyze this trend data and score it for short-form video potential.

Topic: {topic}
Raw data: {raw_data}

Score each 0-100:
- trend_strength: How hot is this trend right now?
- niche_relevance: How relevant to business/mindset/self-improvement niche?
- novelty: How fresh/original is the angle?
- repeatability: Can this format be repeated with variations?
- saturation_risk: How saturated is this topic? (lower = better)

Return ONLY valid JSON:
{{"trend_strength": 85, "niche_relevance": 90, "novelty": 70, "repeatability": 80, "saturation_risk": 30, "summary": "brief analysis"}}
"""
        raw = self.generate(prompt, max_tokens=1500)
        import json
        try:
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0]
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0]
            return json.loads(raw.strip())
        except json.JSONDecodeError:
            return {"trend_strength": 50, "niche_relevance": 50, "novelty": 50, "repeatability": 50, "saturation_risk": 50, "summary": "fallback"}
