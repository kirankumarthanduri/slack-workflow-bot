import re
import logging
from slack_bolt import App
from app.config import config
from app.tasks import (
    add_task, get_tasks_for_user, complete_task,
    get_open_tasks, load_tasks
)
 
logger = logging.getLogger(__name__)
app = App(token=config["SLACK_BOT_TOKEN"])
 
 
# ─────────────────────────────────────────────
# Helper: parse /task command
# ─────────────────────────────────────────────
def parse_task_command(text):
    """Handle <@U123>, <@U123|name>, @name, or no mention."""
    text = text.strip()
    if not text:
        return None
 
    user_id = None
    rest = text
 
    match = re.match(r'^<@([A-Z0-9]+)(?:\|[^>]+)?>\s*(.*)', text, re.DOTALL)
    if match:
        user_id = match.group(1)
        rest = match.group(2).strip()
    elif text.startswith("@"):
        parts = text.split(None, 1)
        user_id = parts[0].lstrip("@")
        rest = parts[1].strip() if len(parts) > 1 else ""
    else:
        rest = text
 
    if not rest:
        return None
 
    due_date = None
    by_match = re.search(r'\s+by\s+(.+)$', rest, re.IGNORECASE)
    if by_match:
        due_date = by_match.group(1).strip()
        rest = rest[:by_match.start()].strip()
 
    if not rest:
        return None
 
    return user_id, rest, due_date
 
 
# ─────────────────────────────────────────────
# Helper: fetch thread messages
# ─────────────────────────────────────────────
def fetch_thread_messages(client, channel, thread_ts):
    """Fetch all messages in a thread and return formatted list."""
    try:
        result = client.conversations_replies(
            channel=channel,
            ts=thread_ts
        )
        messages = []
        for msg in result.get("messages", []):
            # Skip bot messages
            if msg.get("bot_id"):
                continue
            user_id = msg.get("user", "Unknown")
            text = msg.get("text", "").strip()
            if text:
                # Try to get display name
                try:
                    user_info = client.users_info(user=user_id)
                    name = user_info["user"]["profile"].get("display_name") or \
                           user_info["user"]["profile"].get("real_name", user_id)
                except Exception:
                    name = user_id
                messages.append({"user": name, "text": text})
        return messages
    except Exception as e:
        logger.error(f"Failed to fetch thread messages: {e}")
        return []
 
 
# ─────────────────────────────────────────────
# Slash command: /task
# ─────────────────────────────────────────────
@app.command("/task")
def handle_task_command(ack, command, client, respond):
    ack()
    text = command.get("text", "").strip()
    assigned_by = command["user_id"]
 
    if not text:
        respond(
            "📋 *How to assign a task:*\n"
            "`/task @person description`\n"
            "`/task @person description by Friday`\n"
            "`/task description` ← assigns to yourself\n\n"
            "*Examples:*\n"
            "• `/task @john Review the Q3 report`\n"
            "• `/task Update the docs by tomorrow`"
        )
        return
 
    parsed = parse_task_command(text)
    if not parsed:
        respond("❌ Couldn't parse that. Try: `/task @person description`")
        return
 
    user_id, description, due_date = parsed
    if not user_id:
        user_id = assigned_by
 
    task = add_task(
        assigned_to=user_id,
        description=description,
        assigned_by=assigned_by,
        due_date=due_date
    )
 
    due_text = f" _(due: {due_date})_" if due_date else ""
    respond(
        f"✅ *Task #{task['id']} assigned!*\n\n"
        f"👤 Assigned to: <@{user_id}>\n"
        f"📋 Task: {description}{due_text}\n"
        f"👏 Assigned by: <@{assigned_by}>\n\n"
        f"_<@{user_id}> will be nudged if no update is given._"
    )
 
    try:
        client.chat_postMessage(
            channel=user_id,
            text=(
                f"📋 *New task assigned to you!*\n\n"
                f"*Task #{task['id']}:* {description}{due_text}\n"
                f"*Assigned by:* <@{assigned_by}>\n\n"
                f"Reply `done {task['id']}` here when finished!"
            )
        )
    except Exception as e:
        logger.error(f"Failed to DM user {user_id}: {e}")
 
 
# ─────────────────────────────────────────────
# Slash command: /standup
# ─────────────────────────────────────────────
@app.command("/standup")
def handle_standup_command(ack, command, client, respond):
    ack()
    from app.scheduler import post_standup
    post_standup(client)
    respond("✅ Standup posted to the standup channel!")
 
 
# ─────────────────────────────────────────────
# Slash command: /mytasks
# ─────────────────────────────────────────────
@app.command("/mytasks")
def handle_mytasks_command(ack, command, respond):
    ack()
    user_id = command["user_id"]
    tasks = get_tasks_for_user(user_id)
 
    if not tasks:
        respond("🎉 You have no open tasks right now!")
        return
 
    task_lines = "\n".join(
        f"• *#{t['id']}* {t['description']}"
        + (f" _(due: {t['due_date']})_" if t.get('due_date') else "")
        for t in tasks
    )
    respond(
        f"📋 *Your open tasks ({len(tasks)}):*\n\n"
        f"{task_lines}\n\n"
        f"_DM the bot `done <id>` to complete a task._"
    )
 
 
# ─────────────────────────────────────────────
# Slash command: /alltasks
# ─────────────────────────────────────────────
@app.command("/alltasks")
def handle_alltasks_command(ack, command, respond):
    ack()
    tasks = get_open_tasks()
 
    if not tasks:
        respond("🎉 No open tasks — team is all caught up!")
        return
 
    task_lines = "\n".join(
        f"• *#{t['id']}* <@{t['assigned_to']}> — {t['description']}"
        + (f" _(due: {t['due_date']})_" if t.get('due_date') else "")
        for t in tasks
    )
    respond(f"📋 *All open tasks ({len(tasks)}):*\n\n{task_lines}")
 
 
# ─────────────────────────────────────────────
# Slash command: /summarise
# Summarise the most recent thread in a channel
# ─────────────────────────────────────────────
@app.command("/summarise")
def handle_summarise_command(ack, command, client, respond):
    ack()
    from app.ai import summarise_thread
 
    channel = command["channel_id"]
    respond("🤖 Fetching thread and generating summary... (this takes a few seconds)")
 
    try:
        # Get recent messages in the channel
        history = client.conversations_history(channel=channel, limit=1)
        messages = history.get("messages", [])
 
        if not messages:
            respond("No messages found in this channel.")
            return
 
        # Get the most recent thread
        latest = messages[0]
        thread_ts = latest.get("thread_ts") or latest.get("ts")
 
        thread_messages = fetch_thread_messages(client, channel, thread_ts)
 
        if not thread_messages:
            respond("No thread messages found to summarise.")
            return
 
        summary = summarise_thread(thread_messages)
        if summary:
            respond(f"🤖 *Thread Summary*\n\n{summary}")
        else:
            respond("❌ Couldn't generate summary. Please try again.")
 
    except Exception as e:
        logger.error(f"Summarise command error: {e}")
        respond("❌ Something went wrong. Please try again.")
 
 
# ─────────────────────────────────────────────
# Slash command: /digest
# Manually trigger weekly digest (for testing)
# ─────────────────────────────────────────────
@app.command("/digest")
def handle_digest_command(ack, command, client, respond):
    ack()
    from app.scheduler import post_weekly_digest
    respond("📊 Generating weekly digest with Claude AI... (a few seconds)")
    post_weekly_digest(client)
    respond("✅ Weekly digest posted to your general channel!")
 
 
# ─────────────────────────────────────────────
# Event: app_mention
# Now with AI thread summariser + smart replies
# ─────────────────────────────────────────────
@app.event("app_mention")
def handle_mention(event, say, client):
    """Respond to @mentions — with AI thread summarisation."""
    from app.ai import summarise_thread, smart_reply
    from app.scheduler import standup_replies
 
    user = event.get("user")
    text = event.get("text", "").strip()
    channel = event.get("channel")
    thread_ts = event.get("thread_ts")
    message_ts = event.get("ts")
 
    logger.info(f"Mention from {user} in {channel}: {text}")
 
    clean_text = " ".join(
        word for word in text.split()
        if not word.startswith("<@")
    ).strip().lower()
 
    # ── Thread summariser ──────────────────────
    # If mentioned inside a thread → summarise it
    if thread_ts and thread_ts != message_ts:
        say(
            text="🤖 Let me summarise this thread for you...",
            thread_ts=thread_ts
        )
        messages = fetch_thread_messages(client, channel, thread_ts)
        if messages:
            summary = summarise_thread(messages)
            if summary:
                say(
                    text=f"🤖 *Thread Summary*\n\n{summary}\n\n"
                         f"_Summarised by Claude AI_",
                    thread_ts=thread_ts
                )
                return
        say(
            text="❌ Couldn't summarise this thread. Try again in a moment.",
            thread_ts=thread_ts
        )
        return
 
    # ── Standard commands ──────────────────────
    if "hello" in clean_text or "hi" in clean_text or clean_text == "":
        say(
            text=(
                f"👋 Hi <@{user}>! I'm your AI-powered workflow bot.\n\n"
                "*Slash commands:*\n"
                "• `/standup` — post standup now\n"
                "• `/task @person description` — assign task\n"
                "• `/mytasks` — your open tasks\n"
                "• `/alltasks` — all team tasks\n"
                "• `/summarise` — summarise latest thread\n"
                "• `/digest` — generate weekly digest\n\n"
                "*Mention commands:*\n"
                "• Mention me *inside any thread* → I'll summarise it with AI 🤖\n"
                "• `@WorkflowBot help` — show commands\n"
                "• `@WorkflowBot status` — bot status\n\n"
                "*Via DM:*\n"
                "• `done <task_id>` — complete a task\n"
                "• Ask me anything!"
            ),
            thread_ts=message_ts
        )
 
    elif "help" in clean_text:
        say(
            text=(
                "🤖 *Workflow Bot — Full Command Reference*\n\n"
                "*📋 Tasks:*\n"
                "• `/task @person description [by deadline]`\n"
                "• `/mytasks` — your open tasks\n"
                "• `/alltasks` — all team tasks\n"
                "• DM `done <id>` — complete a task\n\n"
                "*🌅 Standups:*\n"
                "• `/standup` — trigger manually\n"
                "• Auto-posts weekdays at 9am\n"
                "• AI synthesis at 10am\n\n"
                "*🤖 AI Features:*\n"
                "• Mention me in any thread → instant summary\n"
                "• `/summarise` — summarise latest thread\n"
                "• `/digest` — generate weekly digest\n"
                "• Auto weekly digest every Friday 5pm\n\n"
                "*🔔 Nudges:*\n"
                "• Auto DMs for open tasks at 10am & 3pm"
            ),
            thread_ts=message_ts
        )
 
    elif "status" in clean_text:
        bot_info = client.auth_test()
        open_tasks = get_open_tasks()
        say(
            text=(
                f"✅ *Bot status: Online*\n"
                f"• Bot: {bot_info['user']}\n"
                f"• Workspace: {bot_info['team']}\n"
                f"• Open tasks: {len(open_tasks)}\n"
                f"• AI: Claude claude-sonnet-4-5 ✨\n"
                f"• Scheduler: running\n"
                f"• Standup: weekdays 9am\n"
                f"• AI synthesis: weekdays 10am\n"
                f"• Nudges: weekdays 10am & 3pm\n"
                f"• Weekly digest: Fridays 5pm"
            ),
            thread_ts=message_ts
        )
 
    elif "summarise" in clean_text or "summarize" in clean_text or "summary" in clean_text:
        say(
            text="💡 To summarise a thread, mention me *inside the thread* you want summarised!",
            thread_ts=message_ts
        )
 
    else:
        # Smart AI reply for anything not matched
        say(text="🤖 Let me think about that...", thread_ts=message_ts)
        reply = smart_reply(clean_text, user_name=f"<@{user}>")
        if reply:
            say(text=f"{reply}\n\n_Powered by Claude AI_", thread_ts=message_ts)
        else:
            say(
                text=(
                    f"Got it, <@{user}>! I received: _{clean_text}_\n"
                    "Try `@WorkflowBot help` to see all commands."
                ),
                thread_ts=message_ts
            )
 
 
# ─────────────────────────────────────────────
# Event: message in standup thread
# Collect standup replies automatically
# ─────────────────────────────────────────────
@app.event("message")
def handle_message(event, say, client):
    """Handle DMs and collect standup thread replies."""
    from app.scheduler import standup_replies
 
    if event.get("bot_id") or event.get("subtype"):
        return
 
    channel_type = event.get("channel_type")
    user = event.get("user")
    text = event.get("text", "").strip()
    thread_ts = event.get("thread_ts")
 
    # ── Collect standup replies ────────────────
    if thread_ts and channel_type != "im":
        from datetime import date
        today_key = date.today().isoformat()
        standup = standup_replies.get(today_key)
 
        if standup and standup.get("thread_ts") == thread_ts:
            # Get user display name
            try:
                user_info = client.users_info(user=user)
                name = user_info["user"]["profile"].get("display_name") or \
                       user_info["user"]["profile"].get("real_name", user)
            except Exception:
                name = user
 
            standup["replies"][name] = text
            # Add checkmark reaction to confirm we logged it
            try:
                client.reactions_add(
                    channel=event["channel"],
                    timestamp=event["ts"],
                    name="white_check_mark"
                )
            except Exception:
                pass
            logger.info(f"Standup reply logged from {name}")
            return
 
    # ── DM handler ────────────────────────────
    if channel_type != "im":
        return
 
    logger.info(f"DM from {user}: {text}")
    text_lower = text.lower()
 
    # Mark task done
    if text_lower.startswith("done"):
        parts = text_lower.split()
        if len(parts) == 2 and parts[1].isdigit():
            task_id = int(parts[1])
            task = complete_task(task_id)
            if task:
                say(
                    f"✅ *Task #{task_id} marked as done!*\n"
                    f"_{task['description']}_\n\nGreat work! 🎉"
                )
            else:
                say(f"❌ Couldn't find task #{task_id}. Check `/mytasks` for your open tasks.")
        else:
            say("To mark a task done, use: `done <task_id>`\nExample: `done 3`")
 
    elif "my tasks" in text_lower or "mytasks" in text_lower:
        tasks = get_tasks_for_user(user)
        if not tasks:
            say("🎉 You have no open tasks right now!")
        else:
            task_lines = "\n".join(
                f"• *#{t['id']}* {t['description']}"
                + (f" _(due: {t['due_date']})_" if t.get('due_date') else "")
                for t in tasks
            )
            say(f"📋 *Your open tasks:*\n\n{task_lines}\n\n_Reply `done <id>` to complete._")
 
    elif "hello" in text_lower or "hi" in text_lower:
        say(
            f"👋 Hi <@{user}>!\n\n"
            "You can DM me:\n"
            "• `done <task_id>` — complete a task\n"
            "• `my tasks` — see your open tasks\n"
            "• `help` — all commands\n"
            "• Ask me anything — I'm powered by Claude AI! 🤖"
        )
 
    elif "help" in text_lower:
        say(
            "🤖 *DM commands:*\n\n"
            "• `done <task_id>` — mark task complete\n"
            "• `my tasks` — see your open tasks\n"
            "• `hello` / `hi` — say hello\n"
            "• `status` — check bot status\n"
            "• Ask me anything — Claude AI will answer!"
        )
 
    elif "status" in text_lower:
        say("✅ I'm online! Powered by Claude AI 🤖")
 
    else:
        # Smart AI reply in DMs
        from app.ai import smart_reply
        say("🤖 Thinking...")
        reply = smart_reply(text)
        if reply:
            say(f"{reply}\n\n_Powered by Claude AI_")
        else:
            say(
                f"I received: _{text}_\n\n"
                "Try `help` to see what I can do, or ask me anything!"
            )
 
 
# ─────────────────────────────────────────────
# Error handler
# ─────────────────────────────────────────────
@app.error
def handle_error(error, body, logger):
    logger.error(f"Slack error: {error}")
    logger.debug(f"Request body: {body}")
 
 
# ─────────────────────────────────────────────
# Slash command: /done
# Mark a task complete from any channel
# ─────────────────────────────────────────────
@app.command("/done")
def handle_done_command(ack, command, respond):
    """Mark a task complete via slash command — no DM needed."""
    ack()
    text = command.get("text", "").strip()
    user_id = command["user_id"]
 
    if not text or not text.isdigit():
        # Show their open tasks so they know which ID to use
        tasks = get_tasks_for_user(user_id)
        if not tasks:
            respond("🎉 You have no open tasks right now!")
            return
        task_lines = "\n".join(
            f"• *#{t['id']}* {t['description']}"
            + (f" _(due: {t['due_date']})_" if t.get('due_date') else "")
            for t in tasks
        )
        respond(
            f"Usage: `/done <task_id>`\n\n"
            f"*Your open tasks:*\n{task_lines}"
        )
        return
 
    task_id = int(text)
    task = complete_task(task_id)
    if task:
        respond(
            f"✅ *Task #{task_id} marked as done!*\n"
            f"_{task['description']}_\n\n"
            f"Great work! 🎉"
        )
    else:
        respond(
            f"❌ Couldn't find task #{task_id}.\n"
            f"Use `/done` to see your open tasks."
        )
