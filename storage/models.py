"""
Lightweight dataclass models mirroring the database schema.

These are plain data containers — no DB logic lives here (that's
database.py's job). Later phases (idea_engine, script_engine, renderer)
will construct and pass these around instead of raw dicts/tuples, and
storage/database.py will grow insert_/get_ functions that accept them.

Phase 1 only defines the shapes; nothing here is wired up yet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ContentSource:
    name: str
    type: str
    url: Optional[str] = None
    is_active: bool = True
    notes: Optional[str] = None
    source_id: Optional[int] = None


@dataclass
class Trend:
    topic: str
    source_id: Optional[int] = None
    keyword: Optional[str] = None
    category: Optional[str] = None
    trend_strength: Optional[float] = None
    data_status: str = "unavailable"
    raw_payload: Optional[str] = None
    trend_id: Optional[int] = None


@dataclass
class ContentIdea:
    content_id: str
    topic: str
    category: Optional[str] = None
    content_type: Optional[str] = None  # trend | evergreen | experimental | repeatable_series
    hook: Optional[str] = None
    topic_score: Optional[float] = None
    hook_score: Optional[float] = None
    novelty_score: Optional[float] = None
    relevance_score: Optional[float] = None
    repeatability_score: Optional[float] = None
    overall_score: Optional[float] = None
    status: str = "pending"  # pending | approved | rejected
    source_trend_id: Optional[int] = None
    notes: Optional[str] = None


@dataclass
class Script:
    content_id: str
    hook: Optional[str] = None
    body: Optional[str] = None
    cta: Optional[str] = None
    estimated_duration: Optional[float] = None
    status: str = "draft"
    notes: Optional[str] = None
    script_id: Optional[int] = None


@dataclass
class Video:
    content_id: str
    template: Optional[str] = None
    duration: Optional[float] = None
    resolution: Optional[str] = None
    file_path: Optional[str] = None
    status: str = "draft"
    notes: Optional[str] = None
    video_id: Optional[int] = None


@dataclass
class Performance:
    content_id: str
    video_id: Optional[int] = None
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    saves: Optional[int] = None
    watch_time: Optional[float] = None
    retention: Optional[float] = None
    engagement_rate: Optional[float] = None
    data_status: str = "unavailable"
    source: Optional[str] = None
    notes: Optional[str] = None
    performance_id: Optional[int] = None


@dataclass
class Experiment:
    name: str
    variable_tested: Optional[str] = None
    content_id_a: Optional[str] = None
    content_id_b: Optional[str] = None
    hypothesis: Optional[str] = None
    result: Optional[str] = None
    confidence: Optional[str] = None
    status: str = "planned"
    notes: Optional[str] = None
    experiment_id: Optional[int] = None
