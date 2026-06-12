import unittest
from unittest.mock import Mock, patch

from slack_client import SlackClient, SlackError


def make_client():
    return SlackClient(bot_token="xoxb-test", channel="C123")


def blocks_text(payload):
    return " ".join(b["text"]["text"] for b in payload["blocks"] if "text" in b)


class TestPostSummary(unittest.TestCase):
    @patch("slack_client.requests.post")
    def test_success_with_issues_and_decisions(self, mock_post):
        mock_post.return_value = Mock(json=lambda: {"ok": True})

        make_client().post_summary(
            meeting_summary="Discussed cardiac model retraining and demo prep.",
            decisions=["Prioritize dataset v3 retrain before Friday's demo."],
            created_issues=[
                {
                    "key": "OMA-1",
                    "url": "https://example.atlassian.net/browse/OMA-1",
                    "title": "Retrain cardiac model on dataset v3",
                    "owner": "Rahul Nair",
                    "due_date": "2026-06-17",
                }
            ],
            failed_items=[],
        )

        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["channel"], "C123")
        text = blocks_text(payload)
        self.assertIn("Discussed cardiac model retraining", text)
        self.assertIn("Prioritize dataset v3 retrain", text)
        self.assertIn("OMA-1", text)
        self.assertIn("Rahul Nair", text)

    @patch("slack_client.requests.post")
    def test_no_action_items_message(self, mock_post):
        mock_post.return_value = Mock(json=lambda: {"ok": True})

        make_client().post_summary(
            meeting_summary="Quick sync, nothing actionable.",
            decisions=[],
            created_issues=[],
            failed_items=[],
        )

        text = blocks_text(mock_post.call_args.kwargs["json"])
        self.assertIn("No action items were identified", text)

    @patch("slack_client.requests.post")
    def test_failed_items_surfaced(self, mock_post):
        mock_post.return_value = Mock(json=lambda: {"ok": True})

        make_client().post_summary(
            meeting_summary="Summary",
            decisions=[],
            created_issues=[],
            failed_items=[{"title": "Bad ticket", "error": "400 Bad Request"}],
        )

        text = blocks_text(mock_post.call_args.kwargs["json"])
        self.assertIn("Failed to create", text)
        self.assertIn("Bad ticket", text)

    @patch("slack_client.requests.post")
    def test_api_error_raises(self, mock_post):
        mock_post.return_value = Mock(json=lambda: {"ok": False, "error": "channel_not_found"})

        with self.assertRaises(SlackError):
            make_client().post_summary("summary", [], [], [])


if __name__ == "__main__":
    unittest.main()
