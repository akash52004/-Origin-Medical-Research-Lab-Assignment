"""Minimal Jira Cloud REST API v3 client for creating issues from action items."""

from datetime import date

import requests
from requests.auth import HTTPBasicAuth


class JiraError(Exception):
    pass


def _is_valid_iso_date(value):
    if not value:
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


class JiraClient:
    def __init__(self, base_url, email, api_token, project_key, issue_type="Task"):
        self.base_url = base_url.rstrip("/")
        self.auth = HTTPBasicAuth(email, api_token)
        self.project_key = project_key
        self.issue_type = issue_type
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}

    def find_account_id(self, name_or_email):
        """Best-effort lookup of a Jira accountId by display name or email.

        Returns None if no name was given, the lookup fails, or there's no
        confident single match - callers should fall back to leaving the
        ticket unassigned rather than guessing.
        """
        if not name_or_email:
            return None
        try:
            resp = requests.get(
                f"{self.base_url}/rest/api/3/user/search",
                params={"query": name_or_email},
                auth=self.auth,
                headers=self.headers,
                timeout=10,
            )
            resp.raise_for_status()
            users = resp.json()
        except requests.RequestException:
            return None

        if len(users) == 1:
            return users[0]["accountId"]
        return None

    def create_issue(self, action_item):
        """Create a Jira issue for one extracted action item.

        Returns {"key": ..., "url": ...} on success, raises JiraError on failure.
        """
        notes = []

        owner = action_item.get("owner")
        account_id = self.find_account_id(owner) if owner else None
        if owner and not account_id:
            notes.append(f"Suggested owner (no unique Jira user match): {owner}")

        due_date = action_item.get("due_date")
        use_due_date = _is_valid_iso_date(due_date)
        if due_date and not use_due_date:
            notes.append(f"Mentioned deadline (could not resolve to a date): {due_date}")

        description_text = action_item["description"]
        if notes:
            description_text += "\n\n" + "\n".join(notes)
        if action_item.get("source_quote"):
            description_text += f"\n\n---\nFrom meeting transcript: \"{action_item['source_quote']}\""

        priority = action_item.get("priority", "Medium")

        fields = {
            "project": {"key": self.project_key},
            "summary": action_item["title"][:255],
            "issuetype": {"name": self.issue_type},
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description_text}],
                    }
                ],
            },
            # Priority is surfaced as a label rather than the native "priority"
            # field, since team-managed Jira projects don't always have that
            # field on the create screen and an unknown field would make the
            # whole request fail.
            "labels": ["auto-generated", "meeting-followup", f"priority-{priority.lower()}"],
        }

        if use_due_date:
            fields["duedate"] = due_date

        if account_id:
            fields["assignee"] = {"id": account_id}

        resp = requests.post(
            f"{self.base_url}/rest/api/3/issue",
            json={"fields": fields},
            auth=self.auth,
            headers=self.headers,
            timeout=15,
        )

        if resp.status_code >= 300:
            raise JiraError(
                f"Failed to create issue '{action_item['title']}': "
                f"{resp.status_code} {resp.text}"
            )

        data = resp.json()
        key = data["key"]
        return {"key": key, "url": f"{self.base_url}/browse/{key}"}
