import unittest
from unittest.mock import Mock, patch

from jira_client import JiraClient, JiraError

SAMPLE_ITEM = {
    "title": "Retrain cardiac anomaly model on dataset v3",
    "description": "Rahul will retrain the model using the augmented dataset.",
    "owner": "Rahul Nair",
    "due_date": "2026-06-17",
    "priority": "High",
    "source_quote": "I'll kick off the retraining run today... by Wednesday.",
}


def make_client():
    return JiraClient(
        base_url="https://example.atlassian.net",
        email="me@example.com",
        api_token="token123",
        project_key="OMA",
        issue_type="Task",
    )


class TestFindAccountId(unittest.TestCase):
    @patch("jira_client.requests.get")
    def test_single_match_returns_account_id(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200, json=lambda: [{"accountId": "abc123"}], raise_for_status=lambda: None
        )
        self.assertEqual(make_client().find_account_id("Rahul Nair"), "abc123")

    @patch("jira_client.requests.get")
    def test_multiple_matches_returns_none(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: [{"accountId": "abc123"}, {"accountId": "def456"}],
            raise_for_status=lambda: None,
        )
        self.assertIsNone(make_client().find_account_id("Rahul"))

    @patch("jira_client.requests.get")
    def test_no_match_returns_none(self, mock_get):
        mock_get.return_value = Mock(status_code=200, json=lambda: [], raise_for_status=lambda: None)
        self.assertIsNone(make_client().find_account_id("Nobody"))

    def test_no_name_returns_none(self):
        client = make_client()
        self.assertIsNone(client.find_account_id(None))
        self.assertIsNone(client.find_account_id(""))


class TestCreateIssue(unittest.TestCase):
    @patch("jira_client.requests.post")
    @patch("jira_client.requests.get")
    def test_known_owner_and_due_date(self, mock_get, mock_post):
        mock_get.return_value = Mock(
            status_code=200, json=lambda: [{"accountId": "abc123"}], raise_for_status=lambda: None
        )
        mock_post.return_value = Mock(status_code=201, json=lambda: {"key": "OMA-1"})

        result = make_client().create_issue(SAMPLE_ITEM)

        self.assertEqual(result, {"key": "OMA-1", "url": "https://example.atlassian.net/browse/OMA-1"})

        fields = mock_post.call_args.kwargs["json"]["fields"]
        self.assertEqual(fields["project"], {"key": "OMA"})
        self.assertEqual(fields["assignee"], {"id": "abc123"})
        self.assertEqual(fields["duedate"], "2026-06-17")
        self.assertIn("priority-high", fields["labels"])

    @patch("jira_client.requests.post")
    @patch("jira_client.requests.get")
    def test_unknown_owner_left_unassigned(self, mock_get, mock_post):
        mock_get.return_value = Mock(status_code=200, json=lambda: [], raise_for_status=lambda: None)
        mock_post.return_value = Mock(status_code=201, json=lambda: {"key": "OMA-2"})

        item = dict(SAMPLE_ITEM, owner="Someone Unknown")
        make_client().create_issue(item)

        fields = mock_post.call_args.kwargs["json"]["fields"]
        self.assertNotIn("assignee", fields)
        description_text = fields["description"]["content"][0]["content"][0]["text"]
        self.assertIn("Someone Unknown", description_text)

    @patch("jira_client.requests.post")
    @patch("jira_client.requests.get")
    def test_invalid_due_date_omitted(self, mock_get, mock_post):
        mock_get.return_value = Mock(status_code=200, json=lambda: [], raise_for_status=lambda: None)
        mock_post.return_value = Mock(status_code=201, json=lambda: {"key": "OMA-3"})

        item = dict(SAMPLE_ITEM, owner=None, due_date="next sprint")
        make_client().create_issue(item)

        fields = mock_post.call_args.kwargs["json"]["fields"]
        self.assertNotIn("duedate", fields)
        description_text = fields["description"]["content"][0]["content"][0]["text"]
        self.assertIn("next sprint", description_text)

    @patch("jira_client.requests.post")
    @patch("jira_client.requests.get")
    def test_api_error_raises_jira_error(self, mock_get, mock_post):
        mock_get.return_value = Mock(status_code=200, json=lambda: [], raise_for_status=lambda: None)
        mock_post.return_value = Mock(status_code=400, text="Bad Request")

        item = dict(SAMPLE_ITEM, owner=None, due_date=None)
        with self.assertRaises(JiraError):
            make_client().create_issue(item)


if __name__ == "__main__":
    unittest.main()
