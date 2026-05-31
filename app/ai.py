import logging
import anthropic
from app.config import config

logger = logging.getLogger(__name__)

# Initialise the Anthropic client once — reused across all AI calls
claude = anthropic.Anthropic(api_key=config["ANTHROPIC_API_KEY"])
MODEL = "claude-sonnet-4-5"


# ─────────────────────────────────────────────
# Helper: call Claude with a prompt
# Central function — all AI features use this
# ─────────────────────────────────────────────
def ask_claude(system_prompt, user_prompt, max_tokens=1000):
    """
    Send a prompt to Claude and return the text response.
    Returns None if the API call fails.
    """
    try:
        response = claude.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.content[0].text.strip()

    except anthropic.AuthenticationError:
        logger.error("❌ Invalid Anthropic API key — check ANTHROPIC_API_KEY in .env")
        return None
    except anthropic.RateLimitError:
        logger.error("❌ Anthropic rate limit hit — try again in a moment")
        return None
    except Exception as e:
        logger.error(f"❌ Claude API error: {e}")
        return None


# ─────────────────────────────────────────────
# Feature 1: Thread Summariser
# Takes a list of Slack messages and summarises them
# ─────────────────────────────────────────────
def summarise_thread(messages, channel_name=""):
    """
    Summarise a Slack thread using Claude.
    messages: list of dicts with 'user' and 'text' keys
    Returns: summary string or None
    """
    if not messages:
        return "No messages found in this thread."

    # Format messages into readable text for Claude
    conversation = "\n".join(
        f"- {m.get('user', 'Unknown')}: {m.get('text', '')}"
        for m in messages
        if m.get('text', '').strip()
    )

    system_prompt = """You are a helpful Slack assistant that summarises conversations clearly and concisely.
Your summaries are:
- Brief but complete (3-5 bullet points)
- Written in plain English
- Focused on decisions made, action items, and key points
- Free of filler words and jargon
Always end with any action items or next steps if present."""

    user_prompt = f"""Please summarise this Slack thread{f' from #{channel_name}' if channel_name else ''}:

{conversation}

Provide:
1. A one-line TL;DR
2. Key points (bullet list)
3. Action items / next steps (if any)"""

    logger.info(f"Summarising thread with {len(messages)} messages")
    return ask_claude(system_prompt, user_prompt, max_tokens=600)


# ─────────────────────────────────────────────
# Feature 2: Standup Synthesis
# Takes all standup replies and generates a team summary
# ─────────────────────────────────────────────
def synthesise_standup(replies, date_str="today"):
    """
    Synthesise standup replies into a team summary.
    replies: dict of { user_display_name: reply_text }
    Returns: synthesis string or None
    """
    if not replies:
        return "No standup replies received today."

    # Format replies for Claude
    replies_text = "\n\n".join(
        f"**{name}:**\n{text}"
        for name, text in replies.items()
    )

    system_prompt = """You are a helpful team assistant that synthesises daily standup updates.
Your synthesis is:
- Clear and professional
- Grouped by theme (not by person)
- Highlighting blockers prominently
- Actionable and easy to scan
Keep it concise — busy managers should be able to read it in 30 seconds."""

    user_prompt = f"""Here are the standup replies from the team for {date_str}:

{replies_text}

Please provide a synthesis with these sections:
1. 🔨 Work in Progress — what the team is working on today
2. ✅ Completed Yesterday — what got done
3. 🚨 Blockers — anything blocking progress (highlight these clearly)
4. 📋 Action Items — any follow-ups needed

If a section has nothing to report, write "None reported"."""

    logger.info(f"Synthesising standup for {len(replies)} team members")
    return ask_claude(system_prompt, user_prompt, max_tokens=800)


# ─────────────────────────────────────────────
# Feature 3: Weekly Digest
# Summarises the week's standups and tasks
# ─────────────────────────────────────────────
def generate_weekly_digest(standup_data, task_data, week_str="this week"):
    """
    Generate a weekly digest from standup history and task data.
    standup_data: list of daily standup summaries
    task_data: dict with completed and open task counts/details
    Returns: digest string or None
    """
    # Format standup history
    if standup_data:
        standup_text = "\n\n".join(
            f"**{day}:**\n{summary}"
            for day, summary in standup_data.items()
        )
    else:
        standup_text = "No standup data recorded this week."

    # Format task summary
    completed = task_data.get("completed", [])
    open_tasks = task_data.get("open", [])

    completed_text = "\n".join(
        f"- {t['description']} (by {t.get('assigned_to', 'unknown')})"
        for t in completed
    ) or "None"

    open_text = "\n".join(
        f"- {t['description']} → assigned to {t.get('assigned_to', 'unknown')}"
        for t in open_tasks
    ) or "None"

    system_prompt = """You are a helpful team assistant that writes engaging weekly digest reports.
Your digests are:
- Narrative and readable, not just bullet points
- Celebratory of progress made
- Honest about what's still open
- Forward-looking — what's coming next week
Written in a warm, professional tone suitable for a team Slack channel."""

    user_prompt = f"""Please write a weekly digest for {week_str}.

STANDUP HIGHLIGHTS:
{standup_text}

TASKS COMPLETED THIS WEEK:
{completed_text}

TASKS STILL OPEN:
{open_text}

Write a digest with:
1. 🌟 Weekly Highlights — key achievements and progress
2. 📊 By the Numbers — tasks completed vs open
3. 🚧 Still in Progress — what carries over to next week
4. 🔭 Looking Ahead — suggested focus for next week

Keep it positive, concise, and under 300 words."""

    logger.info("Generating weekly digest")
    return ask_claude(system_prompt, user_prompt, max_tokens=1000)


# ─────────────────────────────────────────────
# Feature 4: Smart Reply
# Claude answers general questions in context
# ─────────────────────────────────────────────
def smart_reply(user_question, user_name=""):
    """
    Answer a general question intelligently using Claude.
    Used as the fallback when no command is matched.
    """
    system_prompt = """You are a helpful Slack workflow bot assistant for a team.
You help with:
- Answering questions about tasks and workflows
- Giving productivity tips
- Explaining how to use bot commands
- General workplace questions

Keep replies concise and friendly. Use Slack markdown formatting.
Available bot commands: /task, /standup, /mytasks, /alltasks, done <id>"""

    user_prompt = f"{f'{user_name} asks: ' if user_name else ''}{user_question}"

    return ask_claude(system_prompt, user_prompt, max_tokens=400)
