"""Registry of available AI features.

A feature must be listed here to be toggleable in the admin area and callable
through the API. The key is the stable identifier stored in the database; label
and description are surfaced to admins in the UI.
"""


class AIFeature:
    GENERATE_DESCRIPTION = "generate_description"
    SUGGEST_SUBTASKS = "suggest_subtasks"
    SUMMARIZE = "summarize"
    CATEGORIZE = "categorize"


FEATURES = {
    AIFeature.GENERATE_DESCRIPTION: {
        "label": "Generate task description",
        "description": "Draft a task description from a title and keywords.",
    },
    AIFeature.SUGGEST_SUBTASKS: {
        "label": "Suggest subtasks",
        "description": "Propose sensible subtasks for a task.",
    },
    AIFeature.SUMMARIZE: {
        "label": "Summarize board/tasks",
        "description": "Produce a short summary across open tasks or a board.",
    },
    AIFeature.CATEGORIZE: {
        "label": "Auto-categorize",
        "description": "Suggest priority and category from the task text.",
    },
}

FEATURE_KEYS = tuple(FEATURES.keys())
