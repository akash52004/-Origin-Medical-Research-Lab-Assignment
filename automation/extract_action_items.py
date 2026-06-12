"""Turn a raw meeting transcript into a structured summary + action items using Gemini."""

import json
import os

from google import genai
from google.genai import types

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "meeting_summary": {
            "type": "string",
            "description": "2-4 sentence summary of what the meeting covered.",
        },
        "decisions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Key decisions explicitly made during the meeting.",
        },
        "action_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Short imperative summary suitable as a Jira ticket title (<= 100 chars).",
                    },
                    "description": {
                        "type": "string",
                        "description": "Fuller context/detail for the task, written for someone who wasn't in the meeting.",
                    },
                    "owner": {
                        "type": "string",
                        "nullable": True,
                        "description": "Name of the person responsible, only if explicitly stated or unambiguously implied. Null if unclear.",
                    },
                    "due_date": {
                        "type": "string",
                        "nullable": True,
                        "description": "ISO 8601 date (YYYY-MM-DD) if a deadline was explicitly mentioned (resolve relative dates like 'by Friday' using the provided meeting date). Null if no deadline was mentioned.",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["High", "Medium", "Low"],
                        "description": "Inferred urgency based on the language and context used.",
                    },
                    "source_quote": {
                        "type": "string",
                        "description": "The verbatim sentence(s) from the transcript this action item is derived from.",
                    },
                },
                "required": ["title", "description", "priority", "source_quote"],
            },
        },
    },
    "required": ["meeting_summary", "decisions", "action_items"],
}

SYSTEM_PROMPT = """You are part of a workflow-automation pipeline for Origin Medical, a fetal-medicine AI \
research lab. Your job is to read a raw meeting transcript and extract everything needed to file \
follow-up Jira tickets and post a Slack recap.

Rules:
- Only extract action items that reflect a real commitment or agreed follow-up - something someone \
said they (or the team) will do. Do not invent action items from general discussion that did not \
result in a commitment.
- Assign "owner" only when a specific person is clearly named as responsible. If it's unclear or \
shared, set owner to null - do not guess.
- Only set "due_date" when a date or relative timeframe (e.g. "by Friday", "before the demo next \
week") is explicitly mentioned. Convert relative dates to YYYY-MM-DD using the provided meeting date. \
If you cannot confidently resolve a relative date, leave due_date null and mention the original \
phrasing in the description instead.
- "priority" should reflect urgency as expressed in the conversation (e.g. blocking issues, deadlines \
tied to external stakeholders = High), not just the order mentioned.
- Every action item must include a "source_quote" - the exact text from the transcript it is based on, \
so a human can audit the extraction.
- "decisions" should capture conclusions the group reached, separate from action items (a decision \
may or may not have an associated action item).
"""


def extract(transcript_text: str, meeting_date: str, model: str = DEFAULT_MODEL) -> dict:
    """Send the transcript to Gemini and return the structured extraction as a dict."""
    client = genai.Client()

    response = client.models.generate_content(
        model=model,
        contents=(
            f"Meeting date: {meeting_date}\n\n"
            f"Transcript:\n{transcript_text}"
        ),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
        ),
    )

    try:
        return json.loads(response.text)
    except (TypeError, ValueError) as e:
        raise RuntimeError("Gemini did not return the expected structured JSON output.") from e
