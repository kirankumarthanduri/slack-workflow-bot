# 🤖 Slack Workflow Bot

A production-ready Slack bot that automates team workflows using **Rule-based automation** and **Claude AI** — deployed 24/7 on Railway.

Built as a hands-on learning project to explore the combination of workflow automation and generative AI — the same architecture used in enterprise AI decisioning systems.

---

## 🔗 Live Demo

> Bot is running live in a Slack workspace. [Request a demo](https://www.linkedin.com/in/kirankumarthanduri/) or deploy your own using the setup guide below.

---

## ✨ Features

### 📋 Task Management
- `/task @person description [by deadline]` — assign tasks to teammates
- `/mytasks` — view your open tasks
- `/alltasks` — view all team tasks
- DM `done <task_id>` — mark a task complete
- Automatic nudge DMs for overdue tasks (10am & 3pm weekdays)

### 🌅 Daily Standups
- Automated standup prompt every weekday at 9am
- Collects replies in the thread with ✅ confirmation
- **Claude AI synthesises all replies** into a team summary at 10am

### 🤖 AI-Powered Features (Claude claude-sonnet-4-5)
- **Thread Summariser** — mention the bot inside any thread → instant AI summary
- `/summarise` — summarise the latest thread in a channel
- **Weekly Digest** — every Friday at 5pm, Claude generates a narrative weekly report
- `/digest` — trigger weekly digest manually
- **Smart Replies** — ask the bot anything via DM, Claude answers intelligently

### 🔔 Automated Scheduling
| Job | Schedule |
|---|---|
| Daily standup prompt | Weekdays 9:00 AM |
| AI standup synthesis | Weekdays 10:00 AM |
| Task nudge reminders | Weekdays 10:00 AM & 3:00 PM |
| Weekly digest | Fridays 5:00 PM |

---

## 🏗️ Architecture

```
Slack Event (mention, command, message)
        ↓
slack-bolt Python SDK (event routing)
        ↓
Rule Engine (bot.py)          Claude AI (ai.py)
├── /task → tasks.py          ├── Thread summariser
├── /standup → scheduler.py   ├── Standup synthesis
├── /mytasks → tasks.py       ├── Weekly digest
└── nudges → scheduler.py     └── Smart DM replies
        ↓
Slack Response
```

This is a working example of **Rule Engine + LLM architecture**:
- Rules handle deterministic, structured workflows (task CRUD, scheduling, nudges)
- Claude handles language, reasoning, and synthesis (summaries, digests, smart replies)

---

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| [slack-bolt](https://github.com/slackapi/bolt-python) | Slack event handling & slash commands |
| [Anthropic SDK](https://github.com/anthropic/anthropic-sdk-python) | Claude AI integration |
| [APScheduler](https://github.com/agronholm/apscheduler) | Background job scheduling |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Environment variable management |
| [Railway](https://railway.app) | 24/7 cloud deployment |

---

## 🚀 Setup & Deployment

### Prerequisites
- Python 3.11+
- A Slack workspace (free)
- Anthropic API key ([console.anthropic.com](https://console.anthropic.com))

### 1. Clone the repo
```bash
git clone https://github.com/kirankumarthanduri/slack-workflow-bot.git
cd slack-workflow-bot
pip install -r requirements.txt
```

### 2. Create your Slack app

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → From scratch
2. Under **Socket Mode** → Enable it → generate **App Token** (`xapp-`)
3. Under **OAuth & Permissions** → Add Bot Token Scopes:
   - `chat:write` `channels:history` `channels:read`
   - `app_mentions:read` `im:history` `im:write` `users:read`
4. Install app to workspace → copy **Bot Token** (`xoxb-`)
5. Under **Event Subscriptions** → Enable → Subscribe to bot events:
   - `app_mention` `message.im`
6. Under **Slash Commands** → Create:
   - `/task` `/standup` `/mytasks` `/alltasks` `/summarise` `/digest`

### 3. Configure environment
```bash
cp .env.example .env
```

Edit `.env`:
```env
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
ANTHROPIC_API_KEY=sk-ant-your-key
STANDUP_CHANNEL_ID=C0xxxxxxxxx
GENERAL_CHANNEL_ID=C0xxxxxxxxx
```

### 4. Run locally
```bash
python main.py
```

```
✅  Connected to Slack via Socket Mode
🤖  Claude AI: thread summaries + standup synthesis
📅  Standup: weekdays 9:00 AM
```

### 5. Deploy to Railway

1. Push to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select this repo
4. Add all 5 environment variables in the Variables tab
5. Railway deploys automatically — bot runs 24/7

---

## 📁 Project Structure

```
slack-workflow-bot/
├── app/
│   ├── __init__.py
│   ├── ai.py          # Claude AI — summaries, digest, smart replies
│   ├── bot.py         # Slack event handlers & slash commands
│   ├── config.py      # Environment variable management
│   ├── scheduler.py   # APScheduler jobs — standup, synthesis, nudges, digest
│   └── tasks.py       # Task CRUD — add, complete, nudge tracking
├── main.py            # Entry point
├── Procfile           # Railway deployment config
├── requirements.txt
├── .env.example       # Token template
└── .gitignore
```

---

## 💡 What I Learned Building This

- **Slack API & slack-bolt** — event-driven architecture, slash commands, Socket Mode
- **LLM integration** — structuring prompts for consistent, useful AI output
- **Rule Engine + LLM pattern** — combining deterministic rules with adaptive AI
- **Background scheduling** — APScheduler for reliable cron-style jobs
- **Production deployment** — Railway, environment variables, 24/7 uptime
- **Enterprise AI concepts** — explainability, auditability, hybrid decisioning

---

## 👤 Author

**Kirankumar Thanduri** — AI/ML Engineer & Program Manager

- 🔗 [LinkedIn](https://www.linkedin.com/in/kirankumarthanduri/)
- 🐙 [GitHub](https://github.com/kirankumarthanduri)
- 🤖 [AI Readiness Assessor](https://avgs928mfw4qfc5w9pqjmp.streamlit.app/) — my other AI project
