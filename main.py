import logging
import sys
from slack_bolt.adapter.socket_mode import SocketModeHandler
from app.bot import app
from app.config import config
from app.scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


def main():
    logger.info("─" * 52)
    logger.info("🤖  Workflow Bot — Phase 3 (Claude AI)")
    logger.info("─" * 52)

    try:
        client = app.client
        scheduler = start_scheduler(client)

        handler = SocketModeHandler(app, config["SLACK_APP_TOKEN"])

        logger.info("✅  Connected to Slack via Socket Mode")
        logger.info("🤖  Claude AI: thread summaries + standup synthesis")
        logger.info("📅  Standup:   weekdays 9:00 AM")
        logger.info("🧠  Synthesis: weekdays 10:00 AM")
        logger.info("🔔  Nudges:    weekdays 10:00 AM & 3:00 PM")
        logger.info("📊  Digest:    Fridays 5:00 PM")
        logger.info("💬  Slash:     /task /standup /mytasks /alltasks /summarise /digest")
        logger.info("🔴  Press Ctrl+C to stop\n")

        handler.start()

    except KeyboardInterrupt:
        logger.info("\n👋  Bot stopped.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌  Failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
