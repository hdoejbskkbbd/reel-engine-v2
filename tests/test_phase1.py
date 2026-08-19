"""
Phase 1 tests: configuration loading, directory setup, and database schema.

Run with:
    python -m pytest tests/test_phase1.py -v

or without pytest installed:
    python tests/test_phase1.py
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings as settings_module
from config.settings import load_settings, ensure_directories, ConfigError
from storage.database import init_database, list_tables, get_connection


EXPECTED_TABLES = {
    "content_sources",
    "trends",
    "content_ideas",
    "scripts",
    "videos",
    "performance",
    "experiments",
}


class TestSettings(unittest.TestCase):
    def test_load_default_config(self) -> None:
        settings_module._settings_cache = None
        s = load_settings(force_reload=True)
        self.assertEqual(s.project_name, "reel_engine_v2")
        self.assertIn("business", s.categories)
        self.assertEqual(s.video_defaults.aspect_ratio, "9:16")

    def test_missing_config_raises(self) -> None:
        with self.assertRaises(ConfigError):
            load_settings(config_path=Path("/nonexistent/config.json"), force_reload=True)

    def test_malformed_config_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_path = Path(tmp) / "bad.json"
            bad_path.write_text("{not valid json", encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_settings(config_path=bad_path, force_reload=True)


class TestDirectorySetup(unittest.TestCase):
    def test_ensure_directories_creates_all(self) -> None:
        settings_module._settings_cache = None
        s = load_settings(force_reload=True)
        # Remove one dir to confirm ensure_directories recreates it
        target = s.paths.trends_dir
        if target.exists():
            shutil.rmtree(target)
        self.assertFalse(target.exists())

        ensure_directories(s)
        self.assertTrue(target.exists())


class TestDatabase(unittest.TestCase):
    def setUp(self) -> None:
        settings_module._settings_cache = None
        self.settings = load_settings(force_reload=True)
        ensure_directories(self.settings)
        init_database(self.settings)

    def test_all_expected_tables_exist(self) -> None:
        tables = set(list_tables(self.settings))
        self.assertTrue(EXPECTED_TABLES.issubset(tables))

    def test_init_database_is_idempotent(self) -> None:
        # Running init twice must not raise or duplicate tables.
        init_database(self.settings)
        tables = list_tables(self.settings)
        self.assertEqual(len(tables), len(set(tables)))

    def test_connection_context_manager_commits(self) -> None:
        with get_connection(self.settings) as conn:
            conn.execute(
                "INSERT INTO content_sources (name, type) VALUES (?, ?)",
                ("test_source", "manual"),
            )
        with get_connection(self.settings) as conn:
            row = conn.execute(
                "SELECT name FROM content_sources WHERE name = 'test_source'"
            ).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "test_source")


if __name__ == "__main__":
    unittest.main()
