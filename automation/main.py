"""End-to-end pipeline: meeting transcript -> Jira tickets -> Slack summary.

Usage:
    python main.py ../transcripts/sample_meeting_transcript.txt
    python main.py ../transcripts/sample_meeting_transcript.txt --dry-run
    python main.py ../transcripts/meeting_transcript.txt --meeting-date 2026-06-11
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from config import load_config
from extract_action_items import extract
from jira_client import JiraClient, JiraError
from slack_client import SlackClient, SlackError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transcript", help="Path to the meeting transcript/notes text file.")
    parser.add_argument(
        "--meeting-date",
        default=date.today().isoformat(),
        help="Meeting date (YYYY-MM-DD), used to resolve relative due dates. Defaults to today.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only run extraction and print the result; skip Jira/Slack calls.",
    )
    parser.add_argument(
        "--output",
        default="output/action_items.json",
        help="Where to save the extracted JSON for auditing.",
    )
    args = parser.parse_args()

    transcript_path = Path(args.transcript)
    if not transcript_path.exists():
        sys.exit(f"Transcript not found: {transcript_path}")
    transcript_text = transcript_path.read_text(encoding="utf-8")

    print(f"Extracting action items from {transcript_path} (meeting date: {args.meeting_date}) ...")
    extraction = extract(transcript_text, meeting_date=args.meeting_date)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(extraction, indent=2), encoding="utf-8")
    print(f"Saved extraction to {out_path}\n")

    print(f"Meeting summary:\n{extraction['meeting_summary']}\n")

    decisions = extraction["decisions"]
    print(f"Decisions ({len(decisions)}):")
    for d in decisions:
        print(f"  - {d}")

    action_items = extraction["action_items"]
    print(f"\nAction items found ({len(action_items)}):")
    for item in action_items:
        owner = item.get("owner") or "unassigned"
        due = item.get("due_date") or "no due date"
        print(f"  - [{item['priority']}] {item['title']} (owner: {owner}, due: {due})")

    if args.dry_run:
        print("\nDry run - skipping Jira ticket creation and Slack post.")
        return

    config = load_config()

    jira = JiraClient(
        base_url=config.jira_base_url,
        email=config.jira_email,
        api_token=config.jira_api_token,
        project_key=config.jira_project_key,
        issue_type=config.jira_issue_type,
    )

    created_issues = []
    failed_items = []
    print("\nCreating Jira tickets...")
    for item in action_items:
        try:
            issue = jira.create_issue(item)
            issue.update(
                {
                    "title": item["title"],
                    "owner": item.get("owner"),
                    "due_date": item.get("due_date"),
                }
            )
            created_issues.append(issue)
            print(f"  Created {issue['key']}: {item['title']}")
        except JiraError as e:
            print(f"  FAILED: {e}")
            failed_items.append({"title": item["title"], "error": str(e)})

    if not action_items:
        print("  (no action items to create)")

    print("\nPosting summary to Slack...")
    slack = SlackClient(bot_token=config.slack_bot_token, channel=config.slack_channel)
    try:
        slack.post_summary(
            meeting_summary=extraction["meeting_summary"],
            decisions=decisions,
            created_issues=created_issues,
            failed_items=failed_items,
        )
        print("  Posted.")
    except SlackError as e:
        print(f"  FAILED to post Slack summary: {e}")
        sys.exit(1)

    if failed_items:
        sys.exit(1)


if __name__ == "__main__":
    main()
