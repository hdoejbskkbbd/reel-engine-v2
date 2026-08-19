"""
Reel Engine V2 — CLI entrypoint.

Commands:
    init      — create data/output directories and initialize the SQLite schema
    status    — verify configuration, directories, and database are in order
    generate  — generate content ideas and scripts using Groq/Gemini
    voice     — generate voiceover using ElevenLabs
    bot       — start Telegram admin bot
    trends    — analyze trends using Gemini
"""

from __future__ import annotations

import argparse
import logging
import sys
import os

from config.settings import get_settings, ensure_directories, ConfigError
from config.logging_setup import configure_logging
from storage.database import init_database, list_tables

logger = logging.getLogger(__name__)

EXPECTED_TABLES = {
    "content_sources",
    "trends",
    "content_ideas",
    "scripts",
    "videos",
    "performance",
    "experiments",
}


def cmd_init(_args: argparse.Namespace) -> int:
    """Create directories and initialize the database schema."""
    try:
        settings = get_settings()
    except ConfigError as e:
        print(f"[ERROR] Configuration problem: {e}", file=sys.stderr)
        return 1

    configure_logging(settings)

    created = ensure_directories(settings)
    if created:
        logger.info("[COLLECT] Created %d directories: %s", len(created), [str(p) for p in created])
    else:
        logger.info("[COLLECT] All directories already exist.")

    init_database(settings)
    print("Reel Engine V2 initialized.")
    print(f"  Project:  {settings.project_name} ({settings.environment})")
    print(f"  Database: {settings.paths.database_file}")
    print(f"  Log file: {settings.logging.log_file}")
    return 0


def cmd_status(_args: argparse.Namespace) -> int:
    """Report whether config, directories, and DB schema are all in place."""
    try:
        settings = get_settings()
    except ConfigError as e:
        print(f"[ERROR] Configuration problem: {e}", file=sys.stderr)
        return 1

    configure_logging(settings)

    print(f"Project:      {settings.project_name}")
    print(f"Environment:  {settings.environment}")
    print(f"Categories:   {', '.join(settings.categories)}")
    print(f"Content types:{', '.join(settings.content_types)}")

    missing_dirs = [d for d in settings.paths.all_dirs() if not d.exists()]
    if missing_dirs:
        print(f"Directories:  MISSING -> {[str(d) for d in missing_dirs]}")
    else:
        print("Directories:  OK (all present)")

    if not settings.paths.database_file.exists():
        print("Database:     MISSING (run `python main.py init`)")
        return 1

    tables = set(list_tables(settings))
    missing_tables = EXPECTED_TABLES - tables
    if missing_tables:
        print(f"Database:     INCOMPLETE -> missing tables {sorted(missing_tables)}")
        return 1

    print(f"Database:     OK ({len(tables)} tables present)")

    # Check API keys
    apis = {
        "GROQ": os.getenv("GROQ_API_KEY"),
        "GEMINI": os.getenv("GEMINI_API_KEY"),
        "ELEVENLABS": os.getenv("ELEVENLABS_API_KEY"),
        "TELEGRAM": os.getenv("TELEGRAM_BOT_TOKEN"),
    }
    print("\nAPI Status:")
    for name, key in apis.items():
        status = "OK" if key else "NOT SET"
        print(f"  {name}: {status}")

    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    """Generate content ideas or scripts using Groq LLM."""
    try:
        settings = get_settings()
    except ConfigError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    configure_logging(settings)

    from api.groq_client import GroqClient

    client = GroqClient()

    if args.mode == "ideas":
        print(f"Generating {args.count} ideas for topic: {args.topic}")
        ideas = client.generate_ideas(args.topic, args.category, count=args.count)
        print(f"\nGenerated {len(ideas)} ideas:\n")
        for i, idea in enumerate(ideas, 1):
            print(f"{i}. {idea.get('hook', 'N/A')}")
            print(f"   Type: {idea.get('content_type', 'N/A')}")
            print(f"   Duration: {idea.get('estimated_duration', 'N/A')}s")
            print(f"   CTA: {idea.get('cta', 'N/A')}")
            print()

    elif args.mode == "script":
        print(f"Generating script for hook: {args.hook}")
        script = client.generate_script(args.hook, args.body, args.duration)
        print(f"\nScript Generated:\n")
        print(f"HOOK: {script.get('hook_line', 'N/A')}")
        print(f"\nBODY: {script.get('script_body', 'N/A')}")
        print(f"\nCTA: {script.get('cta_line', 'N/A')}")
        print(f"\nVISUAL NOTES: {script.get('visual_notes', 'N/A')}")

    return 0


def cmd_voice(args: argparse.Namespace) -> int:
    """Generate voiceover using ElevenLabs."""
    try:
        settings = get_settings()
    except ConfigError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    configure_logging(settings)

    from api.elevenlabs_client import ElevenLabsClient
    import uuid

    client = ElevenLabsClient()
    out_path = args.output or f"output/final/voice_{uuid.uuid4().hex[:8]}.mp3"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    print(f"Generating voiceover...")
    client.save_voiceover(args.text, out_path, voice_id=args.voice)
    print(f"Saved: {out_path}")
    return 0


def cmd_bot(_args: argparse.Namespace) -> int:
    """Start Telegram admin bot."""
    try:
        settings = get_settings()
    except ConfigError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    configure_logging(settings)

    from api.telegram_bot import TelegramAdminBot

    print("Starting Telegram admin bot...")
    print("Press Ctrl+C to stop")
    bot = TelegramAdminBot()
    bot.run()
    return 0


def cmd_trends(args: argparse.Namespace) -> int:
    """Analyze trends using Gemini."""
    try:
        settings = get_settings()
    except ConfigError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    configure_logging(settings)

    from api.gemini_client import GeminiClient

    client = GeminiClient()
    print(f"Analyzing trend: {args.topic}")
    result = client.analyze_trend(args.topic, args.data or "No raw data provided")

    print(f"\nTrend Analysis:\n")
    print(f"  Trend Strength:    {result.get('trend_strength', 'N/A')}/100")
    print(f"  Niche Relevance:   {result.get('niche_relevance', 'N/A')}/100")
    print(f"  Novelty:           {result.get('novelty', 'N/A')}/100")
    print(f"  Repeatability:     {result.get('repeatability', 'N/A')}/100")
    print(f"  Saturation Risk:   {result.get('saturation_risk', 'N/A')}/100")
    print(f"\nSummary: {result.get('summary', 'N/A')}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reel_engine_v2",
        description="Reel Engine V2 — modular short-form content production system",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    sub.add_parser("init", help="Initialize project directories and database")

    # status
    sub.add_parser("status", help="Check configuration and database status")

    # generate
    gen_parser = sub.add_parser("generate", help="Generate ideas or scripts using AI")
    gen_parser.add_argument("mode", choices=["ideas", "script"], help="Generation mode")
    gen_parser.add_argument("--topic", default="business growth", help="Topic for ideas")
    gen_parser.add_argument("--category", default="business", help="Content category")
    gen_parser.add_argument("--count", type=int, default=5, help="Number of ideas")
    gen_parser.add_argument("--hook", default="3 habits that changed my life", help="Hook for script")
    gen_parser.add_argument("--body", default="Productivity tips video", help="Body outline")
    gen_parser.add_argument("--duration", type=int, default=60, help="Target duration in seconds")

    # voice
    voice_parser = sub.add_parser("voice", help="Generate voiceover with ElevenLabs")
    voice_parser.add_argument("text", help="Text to convert to speech")
    voice_parser.add_argument("--voice", default="pNInz6obpgDQGcFmaJgB", help="Voice ID")
    voice_parser.add_argument("--output", "-o", help="Output file path")

    # bot
    sub.add_parser("bot", help="Start Telegram admin bot")

    # trends
    trends_parser = sub.add_parser("trends", help="Analyze trends using Gemini")
    trends_parser.add_argument("topic", help="Trend topic to analyze")
    trends_parser.add_argument("--data", "-d", help="Raw trend data for context")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "status": cmd_status,
        "generate": cmd_generate,
        "voice": cmd_voice,
        "bot": cmd_bot,
        "trends": cmd_trends,
    }

    handler = commands.get(args.command)
    if handler is None:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
