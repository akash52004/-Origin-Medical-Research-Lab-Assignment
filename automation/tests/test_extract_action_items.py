import json
import unittest
from unittest.mock import Mock, patch

import extract_action_items as eai

SAMPLE_RESULT = {
    "meeting_summary": "Discussed cardiac model retraining and demo prep.",
    "decisions": ["Prioritize dataset v3 retrain before Friday's demo."],
    "action_items": [
        {
            "title": "Retrain cardiac anomaly model on dataset v3",
            "description": "Rahul will retrain using the augmented dataset.",
            "owner": "Rahul Nair",
            "due_date": "2026-06-17",
            "priority": "High",
            "source_quote": "I'll kick off the retraining run today...",
        }
    ],
}


class TestExtract(unittest.TestCase):
    @patch("extract_action_items.genai.Client")
    def test_extract_returns_parsed_json(self, mock_client_cls):
        mock_response = Mock()
        mock_response.text = json.dumps(SAMPLE_RESULT)

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = eai.extract("some transcript text", meeting_date="2026-06-10")

        self.assertEqual(result, SAMPLE_RESULT)

        _, kwargs = mock_client.models.generate_content.call_args
        self.assertEqual(kwargs["config"].response_mime_type, "application/json")
        self.assertEqual(kwargs["config"].response_schema, eai.RESPONSE_SCHEMA)

    @patch("extract_action_items.genai.Client")
    def test_extract_raises_if_response_not_json(self, mock_client_cls):
        mock_response = Mock()
        mock_response.text = "not json"

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with self.assertRaises(RuntimeError):
            eai.extract("some transcript text", meeting_date="2026-06-10")

    @patch("extract_action_items.genai.Client")
    def test_extract_raises_if_response_empty(self, mock_client_cls):
        mock_response = Mock()
        mock_response.text = None

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with self.assertRaises(RuntimeError):
            eai.extract("some transcript text", meeting_date="2026-06-10")


if __name__ == "__main__":
    unittest.main()
