"""
Settings loader for Reel Engine V2.

This is the single source of truth for configuration. Every other module
should import `get_settings()` from here rather than reading config.json
or environment variables directly.

Design rules followed:
- No secrets live in config.json (git-trackable). Secrets, if/when needed
  in later phases, come ONLY from environment variables.
- Paths are resolved relative to the project root, so the engine works
  regardless of the current working directory it's launched from.
- Settings are loaded once and cached (simple singleton) to avoid
  repeated disk reads.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "config.json"


class ConfigError(Exception):
    """Raised when configuration is missing or invalid."""


@dataclass
class Paths:
    data_dir: Path
    raw_dir: Path
    processed_dir: Path
    trends_dir: Path
    ideas_dir: Path
    scripts_dir: Path
    performance_dir: Path
    database_dir: Path
    database_file: Path
    drafts_dir: Path
    final_dir: Path
    logs_dir: Path

    def all_dirs(self) -> list[Path]:
        """Return every directory (not file) path, for setup/verification."""
        return [
            self.data_dir,
            self.raw_dir,
            self.processed_dir,
            self.trends_dir,
            self.ideas_dir,
            self.scripts_dir,
            self.performance_dir,
            self.database_dir,
            self.drafts_dir,
            self.final_dir,
            self.logs_dir,
        ]


@dataclass
class LoggingConfig:
    level: str
    log_file: Path
    console: bool


@dataclass
class VideoDefaults:
    aspect_ratio: str
    resolution: tuple[int, int]
    fps: int
    max_duration_seconds: int


@dataclass
class Settings:
    project_name: str
    environment: str
    paths: Paths
    logging: LoggingConfig
    categories: list[str]
    content_types: list[str]
    video_defaults: VideoDefaults
    scoring_weights: dict[str, float]
    raw: dict[str, Any] = field(repr=False, default_factory=dict)


def _load_raw_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        raise ConfigError(
            f"Config file not found at {config_path}. "
            "Copy/create config/config.json before running the engine."
        )
    try:
        with config_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"config.json is not valid JSON: {e}") from e


def _resolve_path(relative: str) -> Path:
    """Resolve a config-declared path relative to the project root."""
    return (PROJECT_ROOT / relative).resolve()


def _env_override(key: str, default: str) -> str:
    """
    Allow environment variables to override config.json values.
    Env var naming convention: REEL_ENGINE_<UPPER_KEY>
    """
    return os.environ.get(f"REEL_ENGINE_{key.upper()}", default)


_settings_cache: Settings | None = None


def load_settings(config_path: Path | None = None, force_reload: bool = False) -> Settings:
    """
    Load settings from config.json, applying environment variable overrides.

    Args:
        config_path: Optional override for the config file location.
        force_reload: If True, bypass the cache and reload from disk.

    Returns:
        A populated Settings object.

    Raises:
        ConfigError: if the config file is missing or malformed, or if
            required keys are absent.
    """
    global _settings_cache

    if _settings_cache is not None and not force_reload:
        return _settings_cache

    path = config_path or DEFAULT_CONFIG_PATH
    raw = _load_raw_config(path)

    try:
        raw_paths = raw["paths"]
        paths = Paths(
            data_dir=_resolve_path(raw_paths["data_dir"]),
            raw_dir=_resolve_path(raw_paths["raw_dir"]),
            processed_dir=_resolve_path(raw_paths["processed_dir"]),
            trends_dir=_resolve_path(raw_paths["trends_dir"]),
            ideas_dir=_resolve_path(raw_paths["ideas_dir"]),
            scripts_dir=_resolve_path(raw_paths["scripts_dir"]),
            performance_dir=_resolve_path(raw_paths["performance_dir"]),
            database_dir=_resolve_path(raw_paths["database_dir"]),
            database_file=_resolve_path(raw_paths["database_file"]),
            drafts_dir=_resolve_path(raw_paths["drafts_dir"]),
            final_dir=_resolve_path(raw_paths["final_dir"]),
            logs_dir=_resolve_path(raw_paths["logs_dir"]),
        )

        raw_logging = raw["logging"]
        logging_cfg = LoggingConfig(
            level=_env_override("log_level", raw_logging["level"]),
            log_file=_resolve_path(raw_logging["log_file"]),
            console=bool(raw_logging["console"]),
        )

        raw_video = raw["video_defaults"]
        video_defaults = VideoDefaults(
            aspect_ratio=raw_video["aspect_ratio"],
            resolution=tuple(raw_video["resolution"]),
            fps=int(raw_video["fps"]),
            max_duration_seconds=int(raw_video["max_duration_seconds"]),
        )

        settings = Settings(
            project_name=raw["project_name"],
            environment=_env_override("environment", raw["environment"]),
            paths=paths,
            logging=logging_cfg,
            categories=list(raw["categories"]),
            content_types=list(raw["content_types"]),
            video_defaults=video_defaults,
            scoring_weights=dict(raw["scoring_weights"]),
            raw=raw,
        )
    except KeyError as e:
        raise ConfigError(f"Missing required config key: {e}") from e

    _settings_cache = settings
    return settings


def get_settings() -> Settings:
    """Convenience accessor — loads (or returns cached) settings."""
    return load_settings()


def ensure_directories(settings: Settings | None = None) -> list[Path]:
    """
    Create all data/output directories declared in settings if they
    don't already exist. Safe to call repeatedly.

    Returns the list of directories that were created (empty if all
    already existed).
    """
    settings = settings or get_settings()
    created: list[Path] = []
    for d in settings.paths.all_dirs():
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(d)
    return created
