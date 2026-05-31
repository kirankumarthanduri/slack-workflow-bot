# Slack Workflow Bot

A Slack bot that automates team workflows — standups, task nudges, AI-generated summaries, and weekly digests.

Built with Python, slack-bolt, and Claude AI.

## Current status
- ✅ Phase 1 — Bot setup, mention handling, DM responses
- 🔧 Phase 2 — Standups, task assignment, nudges (coming next)
- 🔧 Phase 3 — Claude AI summaries and digests (coming next)
- 🔧 Phase 4 — Deployment

## Setup

### 1. Create your Slack app

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → Create New App → From scratch
2. Under **Settings → Socket Mode**: enable it. Copy your **App Token** (starts with `xapp-`)
3. Under **OAuth & Permissions → Bot Token Scopes**, add:
   - `chat:write`
   - `channels:history`
   - `channels:read`
   - `app_mentions:read`
   - `im:history`
   - `im:write`
   - `users:read`
4. Under **Event Subscriptions → Subscribe to bot events**, add:
   - `app_mention`
   - `message.im`
5. Install the app to your workspace. Copy your **Bot Token** (starts with `xoxb-`)

### 2. Clone and install

```bash
git clone https://github.com/your-username/slack-workflow-bot.git
cd slack-workflow-bot
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your tokens:

```
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
```

### 4. Run the bot

```bash
python main.py
```

You should see:
```
✅  Connected to Slack via Socket Mode
💬  Mention the bot in any channel to test it
```

### 5. Test it

In any Slack channel where the bot is invited:
- `@WorkflowBot hello` — bot greets you
- `@WorkflowBot help` — shows available commands
- `@WorkflowBot status` — confirms bot is online

Or send the bot a direct message.

## Project structure

```
slack-workflow-bot/
├── app/
│   ├── __init__.py
│   ├── bot.py        # Event handlers (mention, DM, errors)
│   └── config.py     # Loads and validates .env variables
├── main.py           # Entry point
├── requirements.txt
├── .env.example      # Token template
└── .gitignore
```

## Tech stack

- [slack-bolt](https://github.com/slackapi/bolt-python) — Slack's official Python SDK
- [python-dotenv](https://github.com/theskumar/python-dotenv) — environment variable management
- [APScheduler](https://github.com/agronholm/apscheduler) — scheduled jobs (Phase 2)
- [Anthropic SDK](https://github.com/anthropic/anthropic-sdk-python) — Claude AI (Phase 3)
