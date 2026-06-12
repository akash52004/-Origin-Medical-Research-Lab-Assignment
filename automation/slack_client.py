"""Minimal Slack Web API client for posting the meeting follow-up summary."""

import requests

SLACK_POST_MESSAGE_URL = "https://slack.com/api/chat.postMessage"


class SlackError(Exception):
    pass


class SlackClient:
    def __init__(self, bot_token, channel):
        self.bot_token = bot_token
        self.channel = channel

    def post_summary(self, meeting_summary, decisions, created_issues, failed_items):
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Meeting Follow-up Summary"},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Summary*\n{meeting_summary}"},
            },
        ]

        if decisions:
            decisions_text = "\n".join(f"- {d}" for d in decisions)
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Decisions*\n{decisions_text}"},
                }
            )

        blocks.append({"type": "divider"})

        if created_issues:
            lines = []
            for item in created_issues:
                line = f"- <{item['url']}|{item['key']}>: {item['title']}"
                if item.get("owner"):
                    line += f" (owner: {item['owner']})"
                if item.get("due_date"):
                    line += f" - due {item['due_date']}"
                lines.append(line)
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Action items created ({len(created_issues)})*\n" + "\n".join(lines),
                    },
                }
            )
        else:
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "_No action items were identified in this meeting._"},
                }
            )

        if failed_items:
            lines = [f"- {f['title']}: {f['error']}" for f in failed_items]
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*:warning: Failed to create ({len(failed_items)})*\n" + "\n".join(lines),
                    },
                }
            )

        resp = requests.post(
            SLACK_POST_MESSAGE_URL,
            headers={
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json={
                "channel": self.channel,
                "text": "Meeting follow-up summary",  # fallback for notifications
                "blocks": blocks,
            },
            timeout=15,
        )

        data = resp.json()
        if not data.get("ok"):
            raise SlackError(f"Slack API error: {data.get('error')}")
        return data
