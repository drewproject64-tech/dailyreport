# Daily Report Telegram Bot

A small Telegram-native news briefing bot built with Python 3.12 and aiogram 3.x.

## Three core functions

1. **Daily Brief** — current headlines across technology, business, science, sports, and world.
2. **Topic Brief** — current headlines for a selected category.
3. **Search Headlines** — search recent headlines by keyword.

The bot does not use a landing-page redirect. Users receive useful content directly inside Telegram.

## Commands

- `/start` — opens the main menu and safely ignores optional start parameters.
- `/help` — explains the three functions and navigation.

## Environment

Required:

```
BOT_TOKEN=your_telegram_bot_token_here
```

Optional:

```
LOG_LEVEL=INFO
```

Never commit real bot tokens or API credentials.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export BOT_TOKEN="your_token"
python bot.py
```

Windows PowerShell:

```powershell
$env:BOT_TOKEN="your_token"
python bot.py
```

## Docker

```bash
docker build -t dailyreport .
docker run --rm -e BOT_TOKEN="your_token" dailyreport
```

## Render

The included `render.yaml` defines a Docker worker. Add `BOT_TOKEN` as a secret environment variable in Render. The container starts with:

```bash
python bot.py
```

This bot uses long polling, so it should run as a worker rather than a web service.

## Data sources

Headline content is fetched at runtime from RSS feeds. If a feed is temporarily unavailable, the bot shows a retry option instead of placeholder content or an error traceback.

## QA checklist

Before advertising, manually verify:

- `/start` responds.
- `/help` responds.
- Daily Brief loads.
- Each topic loads.
- Search accepts valid text.
- Invalid/empty search input is handled.
- Every button responds.
- Main Menu returns to the start screen.
- Source buttons open the corresponding article.
- Bot works from Telegram mobile and desktop.
- Render starts without exceptions.
