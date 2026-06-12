"""Environment-based configuration for the meeting automation pipeline."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

_REQUIRED_VARS = {
    "GEMINI_API_KEY": "gemini_api_key",
    "JIRA_BASE_URL": "jira_base_url",
    "JIRA_EMAIL": "jira_email",
    "JIRA_API_TOKEN": "jira_api_token",
    "JIRA_PROJECT_KEY": "jira_project_key",
    "SLACK_BOT_TOKEN": "slack_bot_token",
    "SLACK_CHANNEL": "slack_channel",
}


@dataclass(frozen=True)
class Config:
    gemini_api_key: str
    jira_base_url: str
    jira_email: str
    jira_api_token: str
    jira_project_key: str
    jira_issue_type: str
    slack_bot_token: str
    slack_channel: str


def load_config() -> Config:
    values = {}
    missing = []
    for env_name, field in _REQUIRED_VARS.items():
        val = os.environ.get(env_name)
        if not val:
            missing.append(env_name)
        values[field] = val

    if missing:
        raise EnvironmentError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Copy automation/.env.example to automation/.env and fill it in."
        )

    values["jira_issue_type"] = os.environ.get("JIRA_ISSUE_TYPE", "Task")
    return Config(**values)
