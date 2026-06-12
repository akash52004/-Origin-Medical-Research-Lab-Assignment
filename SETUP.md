# Setup Guide

This walks through getting all three external services configured, then running the
pipeline against the sample transcript before using your real meeting transcript.

## 1. Gemini API key (action-item extraction)

1. Go to https://aistudio.google.com/app/apikey and sign in with a Google account.
2. Click **Create API key** (or reuse an existing one).
3. Copy it - you'll paste it into `automation/.env` as `GEMINI_API_KEY`.

New accounts typically get free quota, which is more than enough for this task (each
extraction call is a few thousand tokens). The pipeline defaults to `gemini-2.5-flash`;
override with `GEMINI_MODEL` in `.env` if your account needs a different model.

## 2. Jira Cloud (free)

1. Go to https://www.atlassian.com/software/jira/free and create a free site
   (e.g. `https://your-name.atlassian.net`).
2. Create a new project:
   - Choose **Team-managed** project, template **Kanban** (or **Scrum**) is fine.
   - Note the **project key** shown during creation (e.g. `OMA`) - this is
     `JIRA_PROJECT_KEY`.
3. Confirm the issue type you want to create is available - "Task" exists by default
   on Team-managed projects, so `JIRA_ISSUE_TYPE=Task` should work as-is.
4. Create an API token:
   - Go to https://id.atlassian.com/manage-profile/security/api-tokens
   - Click **Create API token**, give it a label (e.g. "meeting-automation"), and copy
     the value - this is `JIRA_API_TOKEN`.
5. `JIRA_BASE_URL` is your site URL (e.g. `https://your-name.atlassian.net`), and
   `JIRA_EMAIL` is the email you used to sign up to Atlassian.

## 3. Slack app + bot

1. Go to https://api.slack.com/apps and click **Create New App** -> **From scratch**.
2. Name it (e.g. "Meeting Automation") and pick a workspace (create a free workspace
   first at https://slack.com/get-started if you don't have one).
3. Under **OAuth & Permissions**, scroll to **Scopes -> Bot Token Scopes** and add:
   - `chat:write`
4. Click **Install to Workspace** at the top of that page, and approve.
5. Copy the **Bot User OAuth Token** (starts with `xoxb-`) - this is `SLACK_BOT_TOKEN`.
6. Create or pick a channel (e.g. `#meeting-automation`), and **invite the bot** to it:
   in the channel, type `/invite @Meeting Automation` (or your app's name).
7. Get the channel ID: open the channel in Slack, click the channel name -> scroll to
   the bottom of the "About" tab -> copy the **Channel ID** (looks like `C0123456789`).
   This is `SLACK_CHANNEL`.

## 4. Configure environment

```bash
cd automation
cp .env.example .env
```

Fill in `.env` with the values gathered above.

## 5. Install dependencies

```bash
cd automation
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## 6. Run it

First, a dry run on the sample transcript - this only calls Gemini and prints/saves the
extracted action items, without touching Jira or Slack:

```bash
python main.py ../transcripts/sample_meeting_transcript.txt --meeting-date 2026-06-10 --dry-run
```

Inspect `output/action_items.json` and the printed summary. Once it looks right, run the
full pipeline (creates Jira tickets + posts to Slack):

```bash
python main.py ../transcripts/sample_meeting_transcript.txt --meeting-date 2026-06-10
```

## 7. Run it on your real meeting

1. Conduct the meeting (10-15 min, at least one other person, with discussion points,
   decisions, and action items).
2. Save the transcript/notes as `transcripts/meeting_transcript.txt`.
3. Run:

```bash
python main.py ../transcripts/meeting_transcript.txt --meeting-date <YYYY-MM-DD of the meeting>
```

4. Take screenshots of the created Jira tickets and the Slack message for the
   submission.
