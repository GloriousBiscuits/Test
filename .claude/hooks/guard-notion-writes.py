#!/usr/bin/env python3
"""PreToolUse guard: the agent may change only a task's date, priority, urgency and progress.

- notion-update-page is allowed only as update_properties, and only on Timeline,
  Priority, Urgency and Progress. No content, title, icon or other property edits.
- Deleting, moving, restoring and schema changes are blocked outright.

Creating approved tasks and adding comments are not touched here; the spec governs those.
Exit code 2 blocks the tool call and shows stderr to the model.
"""
import json
import sys

ALLOWED_PROPS = {
    "date:Timeline:start",
    "date:Timeline:end",
    "date:Timeline:is_datetime",
    "Priority",
    "Urgency",
    "Progress",
}
ALLOWED_KEYS = {"page_id", "command", "properties", "allow_async", "skill", "instructions_version"}

BLOCKED = {
    "notion-delete-pages": "Deleting pages is blocked.",
    "notion-delete-databases": "Deleting databases is blocked.",
    "notion-delete-comment": "Deleting comments is blocked.",
    "notion-move-pages": "Moving pages is blocked.",
    "notion-restore-version": "Restoring page versions is blocked.",
    "notion-update-data-source": "Changing the Tasks Table schema is blocked.",
    "notion-update-view": "Changing views is blocked.",
}


def block(msg):
    print(f"Blocked by guard-notion-writes: {msg}", file=sys.stderr)
    sys.exit(2)


try:
    event = json.load(sys.stdin)
except Exception:
    block("could not read hook input, failing closed.")

action = event.get("tool_name", "").split("__")[-1]
args = event.get("tool_input") or {}

if action in BLOCKED:
    block(BLOCKED[action])

if action == "notion-update-page":
    if args.get("command") != "update_properties":
        block("Only update_properties is allowed. Don't edit page content.")
    extra = sorted(set(args) - ALLOWED_KEYS)
    if extra:
        block(f"Only properties may change. Remove: {', '.join(extra)}.")
    props = args.get("properties") or {}
    if not props:
        block("No properties given.")
    bad = sorted(set(props) - ALLOWED_PROPS)
    if bad:
        block(
            "Only Timeline, Priority, Urgency and Progress may change on an existing task. "
            f"Not allowed: {', '.join(bad)}."
        )

sys.exit(0)
