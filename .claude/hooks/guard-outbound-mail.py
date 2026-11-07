#!/usr/bin/env python3
"""PreToolUse guard: nothing leaves Brian's mailbox for anyone else.

- outlook_send_mail is allowed only when every to/cc/bcc address is Brian.
- Tools that send or forward to arbitrary recipients are blocked outright.
- Drafts are allowed, without Bcc. They sit in Outlook Drafts until Brian sends them himself.

Exit code 2 blocks the tool call and shows stderr to the model.
"""
import json
import sys

OWNER = "bfauver@hargetthunter.com"

BLOCKED = {
    "outlook_send_draft": "Sending drafts is blocked. Leave the draft in Outlook for Brian to send.",
    "outlook_forward_mail": "Forwarding is blocked. Create a draft instead.",
    "outlook_create_filter": "Mail rules are blocked (they can auto-forward).",
    "outlook_set_vacation": "Auto-replies are blocked.",
    "teams_send_chat_message": "Teams messages are blocked.",
    "teams_send_channel_message": "Teams messages are blocked.",
    "teams_reply_channel_message": "Teams messages are blocked.",
    "teams_create_chat": "Creating Teams chats is blocked.",
}


def block(msg):
    print(f"Blocked by guard-outbound-mail: {msg}", file=sys.stderr)
    sys.exit(2)


try:
    event = json.load(sys.stdin)
except Exception:
    block("could not read hook input, failing closed.")

tool = event.get("tool_name", "")
action = tool.split("__")[-1]
args = event.get("tool_input") or {}

if action in BLOCKED:
    block(BLOCKED[action])

if action in ("outlook_update_draft", "outlook_create_draft") and args.get("bcc"):
    block("Bcc on drafts is blocked. Put recipients on To or Cc where Brian can see them.")

if action == "outlook_send_mail":
    recipients = [
        str(addr).strip().lower()
        for field in ("to", "cc", "bcc")
        for addr in (args.get(field) or [])
    ]
    others = [r for r in recipients if r != OWNER]
    if not recipients or others:
        block(
            f"send_mail may only go to {OWNER}. "
            f"Other recipients: {', '.join(others) or 'none given'}. "
            "Create a draft for Brian to review instead."
        )

sys.exit(0)
