# Meeting Notes -> Jira -> Slack Automation

A small pipeline that takes a raw meeting transcript and automatically:

1. **Extracts** a summary, key decisions, and action items (with owner, due date,
   priority, and a source quote for each item) using the Gemini API with a strict
   JSON response schema.
2. **Creates Jira tickets** for each action item via the Jira Cloud REST API,
   attempting to resolve the named owner to a Jira account and falling back to an
   unassigned ticket with a note if it can't confidently match one.
3. **Posts a Slack summary** with the meeting recap, decisions, and links to the
   created Jira tickets (plus any that failed to create).

## Project structure

```
automation/
  main.py                  # CLI entry point - runs the full pipeline
  extract_action_items.py  # Gemini-based extraction (summary, decisions, action items)
  jira_client.py           # Jira Cloud REST API v3 client
  slack_client.py          # Slack Web API client (chat.postMessage)
  config.py                # Loads configuration from environment variables (.env)
  tests/                   # Unit tests
transcripts/
  sample_meeting_transcript.txt
```

## Setup

See [SETUP.md](SETUP.md) for getting API keys for Gemini, Jira Cloud, and Slack,
configuring `automation/.env`, and installing dependencies.

## Usage

Dry run (extraction only, no Jira/Slack calls):

```bash
cd automation
python main.py ../transcripts/sample_meeting_transcript.txt --meeting-date 2026-06-10 --dry-run
```

Full run (creates Jira tickets and posts the Slack summary):

```bash
python main.py ../transcripts/sample_meeting_transcript.txt --meeting-date 2026-06-10
```

## Tests

```bash
cd automation
pip install pytest
pytest
```
