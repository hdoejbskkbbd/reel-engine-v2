"""Telegram admin bot for Reel Engine V2."""
from __future__ import annotations

import os
import logging
import asyncio
from typing import Optional

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes
except ImportError:
    Application = None

logger = logging.getLogger(__name__)

class TelegramAdminBot:
    def __init__(self, token: Optional[str] = None, admin_id: Optional[str] = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.admin_id = admin_id or os.getenv("TELEGRAM_ADMIN_ID")
        if not self.token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN not set")
        if not self.admin_id:
            raise RuntimeError("TELEGRAM_ADMIN_ID not set")
        self.admin_id = int(self.admin_id)
        if Application is None:
            raise RuntimeError("python-telegram-bot not installed. Run: pip install python-telegram-bot")
        self.app = Application.builder().token(self.token).build()
        self._setup_handlers()
        logger.info("[API] Telegram bot initialized")

    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self._cmd_start))
        self.app.add_handler(CommandHandler("status", self._cmd_status))
        self.app.add_handler(CommandHandler("ideas", self._cmd_ideas))
        self.app.add_handler(CommandHandler("generate", self._cmd_generate))
        self.app.add_handler(CommandHandler("voice", self._cmd_voice))
        self.app.add_handler(CommandHandler("help", self._cmd_help))

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != self.admin_id:
            await update.message.reply_text("Unauthorized.")
            return
        await update.message.reply_text("DRC Bot active. /help for commands.")

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != self.admin_id:
            await update.message.reply_text("Unauthorized.")
            return
        from config.settings import get_settings
        from storage.database import list_tables
        try:
            settings = get_settings()
            tables = list_tables(settings)
            msg = "Reel Engine V2 Status:" + "
"
            msg += "Project: " + settings.project_name + "
"
            msg += "Env: " + settings.environment + "
"
            msg += "Tables: " + str(len(tables)) + " ready" + "
"
            msg += "Categories: " + ", ".join(settings.categories[:3]) + "..."
            await update.message.reply_text(msg)
        except Exception as e:
            await update.message.reply_text("Error: " + str(e))

    async def _cmd_ideas(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != self.admin_id:
            await update.message.reply_text("Unauthorized.")
            return
        args = context.args
        topic = " ".join(args) if args else "business growth"
        await update.message.reply_text("Generating ideas for: " + topic + "...")
        try:
            from api.groq_client import GroqClient
            client = GroqClient()
            ideas = client.generate_ideas(topic, "business", count=3)
            msg = "Generated Ideas:" + "

"
            for i, idea in enumerate(ideas, 1):
                msg += str(i) + ". " + idea.get("hook", "N/A") + "
"
                msg += "   Type: " + idea.get("content_type", "N/A") + "
"
                msg += "   Duration: " + str(idea.get("estimated_duration", "N/A")) + "s" + "

"
            await update.message.reply_text(msg[:4000])
        except Exception as e:
            await update.message.reply_text("Error: " + str(e))

    async def _cmd_generate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != self.admin_id:
            await update.message.reply_text("Unauthorized.")
            return
        args = context.args
        hook = " ".join(args) if args else "3 habits that made me $1M"
        await update.message.reply_text("Generating script for: " + hook + "...")
        try:
            from api.groq_client import GroqClient
            client = GroqClient()
            script = client.generate_script(hook, "Business mindset video", 60)
            msg = "Script Generated:" + "

"
            msg += "Hook: " + script.get("hook_line", "N/A") + "

"
            body = script.get("script_body", "N/A")
            msg += "Body: " + (body[:500] + "..." if len(body) > 500 else body) + "

"
            msg += "CTA: " + script.get("cta_line", "N/A")
            await update.message.reply_text(msg[:4000])
        except Exception as e:
            await update.message.reply_text("Error: " + str(e))

    async def _cmd_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != self.admin_id:
            await update.message.reply_text("Unauthorized.")
            return
        args = context.args
        text = " ".join(args) if args else "Welcome to Reel Engine V2. Let's create viral content."
        await update.message.reply_text("Generating voiceover...")
        try:
            from api.elevenlabs_client import ElevenLabsClient
            client = ElevenLabsClient()
            import uuid
            out_path = "output/final/voice_" + uuid.uuid4().hex[:8] + ".mp3"
            os.makedirs("output/final", exist_ok=True)
            client.save_voiceover(text, out_path)
            await update.message.reply_audio(audio=open(out_path, "rb"), caption="Voiceover ready")
        except Exception as e:
            await update.message.reply_text("Error: " + str(e))

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != self.admin_id:
            await update.message.reply_text("Unauthorized.")
            return
        help_text = """DRC Bot Commands:
/status — Engine status
/ideas [topic] — Generate content ideas
/generate [hook] — Generate script
/voice [text] — Generate voiceover
/help — This message"""
        await update.message.reply_text(help_text)

    def run(self):
        logger.info("[API] Telegram bot polling started")
        self.app.run_polling()

    def send_notification(self, message: str):
        """Send admin notification (sync wrapper)."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.app.bot.send_message(chat_id=self.admin_id, text=message))
            else:
                loop.run_until_complete(self.app.bot.send_message(chat_id=self.admin_id, text=message))
        except Exception as e:
            logger.error("[API] Telegram notify error: %s", e)
