import os
from dotenv import load_dotenv

load_dotenv()

def get_config():
    """Load and validate all required environment variables."""
    config = {
        "SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN"),
        "SLACK_APP_TOKEN": os.getenv("SLACK_APP_TOKEN"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "STANDUP_CHANNEL_ID": os.getenv("STANDUP_CHANNEL_ID"),
        "GENERAL_CHANNEL_ID": os.getenv("GENERAL_CHANNEL_ID"),
    }

    # Check the tokens needed for Phase 1 are present
    required = ["SLACK_BOT_TOKEN", "SLACK_APP_TOKEN"]
    missing = [key for key in required if not config[key]]

    if missing:
        raise EnvironmentError(
            f"\n❌ Missing required environment variables: {', '.join(missing)}"
            f"\n   Copy .env.example to .env and fill in your tokens."
            f"\n   Get them from: https://api.slack.com/apps"
        )

    return config


# A single shared config object used across the app
config = get_config()
