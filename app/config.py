import os
import logging
from dotenv import load_dotenv

# Load .env file if present (local dev)
# On Railway, environment variables are injected directly
load_dotenv(override=False)

logger = logging.getLogger(__name__)

def get_config():
    """Load and validate all required environment variables."""

    # Strip whitespace — prevents common copy-paste issues
    def clean(key):
        val = os.getenv(key, "")
        return val.strip().strip('"').strip("'") if val else None

    config = {
        "SLACK_BOT_TOKEN": clean("SLACK_BOT_TOKEN"),
        "SLACK_APP_TOKEN": clean("SLACK_APP_TOKEN"),
        "ANTHROPIC_API_KEY": clean("ANTHROPIC_API_KEY"),
        "STANDUP_CHANNEL_ID": clean("STANDUP_CHANNEL_ID"),
        "GENERAL_CHANNEL_ID": clean("GENERAL_CHANNEL_ID"),
    }

    # Check required tokens
    required = ["SLACK_BOT_TOKEN", "SLACK_APP_TOKEN"]
    missing = [key for key in required if not config[key]]

    if missing:
        raise EnvironmentError(
            f"\n❌ Missing required environment variables: {', '.join(missing)}"
            f"\n   On Railway: add them in the Variables tab."
            f"\n   Locally: copy .env.example to .env and fill in your tokens."
        )

    return config

config = get_config()