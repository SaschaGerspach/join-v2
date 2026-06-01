"""Prompt builders for each AI feature.

Each builder returns a (system, user_prompt) tuple. Features that need
structured output instruct the model to return JSON; the view parses it.
"""

from tasks_api.models import Task

PRIORITIES = [choice.value for choice in Task.Priority]


def generate_description(title, keywords=""):
    system = (
        "You write concise, actionable task descriptions for a kanban board. "
        "Reply with the description text only, no preamble, 1-3 sentences."
    )
    user = f"Task title: {title}\nKeywords: {keywords or '(none)'}"
    return system, user


def suggest_subtasks(title, description=""):
    system = (
        "You break a kanban task into a few concrete subtasks. "
        'Reply with JSON only: {"subtasks": ["...", "..."]}. '
        "Use 2-6 short, imperative items."
    )
    user = f"Task title: {title}\nDescription: {description or '(none)'}"
    return system, user


def summarize(items):
    system = (
        "You summarize the state of a set of kanban tasks for a status update. "
        "Reply with a short plain-text summary, max 4 sentences."
    )
    joined = "\n".join(f"- {item}" for item in items)
    user = f"Tasks:\n{joined}"
    return system, user


def categorize(title, description=""):
    system = (
        "You triage a kanban task. "
        'Reply with JSON only: {"priority": "<one of '
        f"{', '.join(PRIORITIES)}>\", \"labels\": [\"...\"]}}. "
        "Pick exactly one priority and 1-3 short label suggestions."
    )
    user = f"Task title: {title}\nDescription: {description or '(none)'}"
    return system, user
