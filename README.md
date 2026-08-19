# Reel Engine V2

AI-powered short-form content production system. Groq + Gemini + ElevenLabs + Telegram bot — all wired up.

## Features

- **Content Generation** — Groq LLM se viral ideas aur scripts
- **Trend Analysis** — Gemini se trend scoring aur analysis
- **Voiceover** — ElevenLabs se AI voice generation
- **Admin Bot** — Telegram bot se remote control
- **SQLite Database** — Full content pipeline tracking

## Quick Start

```bash
# Clone
git clone https://github.com/anonymouscoderx/reel-engine-v2.git
cd reel-engine-v2

# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Config
cp .env.example .env
# Edit .env with your API keys

# Init
python main.py init
python main.py status
```

## Commands

```bash
# Initialize
python main.py init

# Check status
python main.py status

# Generate ideas
python main.py generate ideas --topic "productivity hacks" --count 5

# Generate script
python main.py generate script --hook "5AM club secret" --duration 60

# Generate voiceover
python main.py voice "Welcome to the 5AM club. Here is the secret..."

# Analyze trend
python main.py trends "morning routine" --data "trending on TikTok"

# Start Telegram bot
python main.py bot
```

## API Keys Required

| Service | Key | Purpose |
|---------|-----|---------|
| Groq | `GROQ_API_KEY` | LLM inference (ideas, scripts) |
| Gemini | `GEMINI_API_KEY` | Trend analysis |
| ElevenLabs | `ELEVENLABS_API_KEY` | Voice generation |
| Telegram | `TELEGRAM_BOT_TOKEN` | Admin bot |
| Telegram | `TELEGRAM_ADMIN_ID` | Admin user ID |

## VPS Deployment

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y python3-pip python3-venv git
git clone https://github.com/anonymouscoderx/reel-engine-v2.git
cd reel-engine-v2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # Add your keys
python main.py init
python main.py bot  # Start bot in foreground

# Or run with nohup
nohup python main.py bot > bot.log 2>&1 &
```

## Tech Stack

- Python 3.10+
- SQLite (WAL mode)
- Groq API (Llama 3.3 70B)
- Gemini API (Flash 1.5)
- ElevenLabs API (Multilingual v2)
- python-telegram-bot

## License

anonymous world — sab legal hai.
