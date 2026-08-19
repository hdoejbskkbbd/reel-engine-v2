"""ElevenLabs API client — voice generation & cloning."""
from __future__ import annotations

import os
import logging
from typing import Optional

try:
    from elevenlabs import ElevenLabs
except ImportError:
    ElevenLabs = None

logger = logging.getLogger(__name__)

class ElevenLabsClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise RuntimeError("ELEVENLABS_API_KEY not set")
        if ElevenLabs is None:
            raise RuntimeError("elevenlabs package not installed. Run: pip install elevenlabs")
        self.client = ElevenLabs(api_key=self.api_key)
        logger.info("[API] ElevenLabs client initialized")

    def generate_voice(self, text: str, voice_id: str = "pNInz6obpgDQGcFmaJgB", model: str = "eleven_multilingual_v2") -> bytes:
        """Generate voice audio from text. Returns MP3 bytes."""
        try:
            audio = self.client.generate(text=text, voice=voice_id, model=model)
            return b"".join(audio)
        except Exception as e:
            logger.error("[API] ElevenLabs error: %s", e)
            raise

    def save_voiceover(self, text: str, output_path: str, voice_id: str = "pNInz6obpgDQGcFmaJgB") -> str:
        """Generate and save voiceover to file."""
        audio = self.generate_voice(text, voice_id)
        with open(output_path, "wb") as f:
            f.write(audio)
        logger.info("[API] Voiceover saved: %s", output_path)
        return output_path

    def list_voices(self) -> list[dict]:
        try:
            voices = self.client.voices.get_all()
            return [{"id": v.voice_id, "name": v.name} for v in voices.voices]
        except Exception as e:
            logger.error("[API] ElevenLabs voices error: %s", e)
            return []
