from __future__ import annotations

import uuid
from datetime import timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.utils import timezone

from activity_api.models import ActivityEntry
from boards_api.models import Board, BoardFavorite, BoardMember
from columns_api.models import Column
from contacts_api.models import Contact
from notifications_api.models import Notification
from tasks_api.models import Comment, Label, Subtask, Task, TaskDependency, TimeEntry

from ._helpers import User

if TYPE_CHECKING:
    from auth_api.models import User as UserModel

TEAMMATES = [
    ("Sofia", "Martinez"),
    ("Lukas", "Weber"),
    ("David", "Chen"),
    ("Emma", "Wilson"),
]

EXTERNAL_CONTACTS = [
    ("Olivia", "Brown", "olivia.brown@example.com", "+1 555 0142"),
    ("Noah", "Taylor", "noah.taylor@example.com", ""),
]

# Offsets are days relative to today, so the calendar, Gantt chart and
# overdue markers always look current no matter when the guest logs in.
BOARDS = [
    {
        "title": "Website Relaunch",
        "color": "#29abe2",
        "favorite": True,
        "members": {"Sofia": BoardMember.Role.ADMIN, "Lukas": BoardMember.Role.EDITOR, "David": BoardMember.Role.EDITOR},
        "labels": {"Design": "#ff7a00", "Frontend": "#29abe2", "Backend": "#9327ff", "Content": "#1fd7c1", "Bug": "#ff3d00"},
        "tasks": [
            {
                "column": "To do", "title": "Implement contact form", "priority": "medium",
                "description": "Contact form with validation and spam protection. Submissions go to the support inbox.",
                "start": 2, "due": 9, "labels": ["Frontend", "Backend"], "assignees": ["Lukas"],
                "subtasks": [("Form layout", False), ("Client-side validation", False), ("Spam protection", False)],
            },
            {
                "column": "To do", "title": "Write SEO meta texts", "priority": "low",
                "description": "Title and description for all top-level pages.",
                "start": 8, "due": 14, "labels": ["Content"], "assignees": ["Emma"],
            },
            {
                "column": "To do", "title": "Set up analytics dashboard", "priority": "low",
                "description": "Privacy-friendly analytics without cookies.",
                "start": 12, "due": 21, "labels": ["Backend"], "assignees": ["David"],
            },
            {
                "column": "In progress", "title": "Build responsive navigation", "priority": "high",
                "description": "Main navigation for desktop and mobile, including a burger menu and keyboard support.",
                "start": -4, "due": 2, "labels": ["Frontend", "Design"], "assignees": ["me", "Sofia"],
                "subtasks": [("Desktop menu", True), ("Mobile burger menu", True), ("Keyboard navigation", False), ("Dark mode styles", False)],
                "comments": [("David", "Keep in mind the burger menu must also close with Esc.", 1)],
                "time": [("me", 90, "Mobile menu"), ("Sofia", 60, "Design review")],
            },
            {
                "column": "In progress", "title": "Migrate blog posts to new CMS", "priority": "medium",
                "description": "Move all 120 posts including images and categories.",
                "start": -6, "due": 5, "labels": ["Backend", "Content"], "assignees": ["David"],
                "subtasks": [("Export old posts", True), ("Map categories", True), ("Import and verify", False)],
                "time": [("David", 120, "Export script")],
            },
            {
                "column": "Await feedback", "title": "Homepage hero design", "priority": "urgent",
                "description": "Two variants of the hero section are ready for review.",
                "start": -10, "due": -1, "labels": ["Design"], "assignees": ["Sofia"],
                "comments": [
                    ("Sofia", "First draft is ready. Which headline do you prefer, A or B?", 2),
                    ("Lukas", "Variant B looks great on mobile, the call to action is much easier to reach.", 1),
                ],
            },
            {
                "column": "Await feedback", "title": "Cookie consent banner", "priority": "medium",
                "description": "Waiting for the legal team to approve the wording.",
                "start": -3, "due": 1, "labels": ["Frontend"], "assignees": ["Lukas"],
            },
            {
                "column": "Done", "title": "Define sitemap", "priority": "low",
                "start": -20, "due": -12, "labels": ["Content"], "assignees": ["me"],
            },
            {
                "column": "Done", "title": "Choose color palette and typography", "priority": "medium",
                "start": -18, "due": -10, "labels": ["Design"], "assignees": ["Sofia"],
                "time": [("Sofia", 180, "Moodboard and palette")],
            },
            {
                "column": "Done", "title": "Fix broken image links on legacy site", "priority": "high",
                "start": -15, "due": -13, "labels": ["Bug"], "assignees": ["David"],
            },
        ],
        "dependencies": [("Write SEO meta texts", "Migrate blog posts to new CMS")],
        "activity": [
            ("Sofia", "moved", "Homepage hero design", 1),
            ("Lukas", "created", "Cookie consent banner", 3),
            ("David", "updated", "Migrate blog posts to new CMS", 4),
        ],
    },
    {
        "title": "Mobile App Launch",
        "color": "#9327ff",
        "favorite": False,
        "members": {"Lukas": BoardMember.Role.ADMIN, "David": BoardMember.Role.EDITOR, "Emma": BoardMember.Role.EDITOR},
        "labels": {"iOS": "#29abe2", "Android": "#1fd7c1", "QA": "#ffbb2b", "Release": "#ff7a00"},
        "tasks": [
            {
                "column": "To do", "title": "Prepare App Store screenshots", "priority": "medium",
                "start": 6, "due": 12, "labels": ["Release"], "assignees": ["Emma"],
            },
            {
                "column": "To do", "title": "Write release notes", "priority": "low",
                "start": 10, "due": 16, "labels": ["Release"], "assignees": ["me"],
            },
            {
                "column": "In progress", "title": "Push notification support", "priority": "high",
                "description": "Notifications for task assignments and due dates on both platforms.",
                "start": -3, "due": 6, "labels": ["iOS", "Android"], "assignees": ["Lukas"],
                "subtasks": [("Register device tokens", True), ("iOS permission prompt", False), ("Android notification channels", False)],
                "time": [("Lukas", 150, "Device token endpoint")],
            },
            {
                "column": "Await feedback", "title": "Beta test round 2", "priority": "medium",
                "description": "Collect feedback from the 25 beta testers.",
                "start": -7, "due": 3, "labels": ["QA"], "assignees": ["David", "Emma"],
                "comments": [("David", "12 of 25 testers have already sent their feedback.", 1)],
            },
            {
                "column": "Done", "title": "Crash on login with expired token", "priority": "urgent",
                "start": -9, "due": -8, "labels": ["QA", "iOS"], "assignees": ["Lukas"],
            },
            {
                "column": "Done", "title": "Set up CI build pipeline", "priority": "medium",
                "start": -14, "due": -9, "labels": ["Release"], "assignees": ["David"],
            },
        ],
        "dependencies": [("Prepare App Store screenshots", "Beta test round 2")],
        "activity": [("Emma", "updated", "Beta test round 2", 2)],
    },
    {
        "title": "Marketing Q4",
        "color": "#ff7a00",
        "favorite": False,
        "members": {"Emma": BoardMember.Role.EDITOR},
        "labels": {},
        "tasks": [
            {
                "column": "To do", "title": "Plan newsletter campaign", "priority": "medium",
                "start": 5, "due": 18, "labels": [], "assignees": ["Emma"],
            },
            {
                "column": "In progress", "title": "Product launch blog post", "priority": "high",
                "start": -2, "due": 4, "labels": [], "assignees": ["me", "Emma"],
                "subtasks": [("Outline", True), ("First draft", False), ("Proofreading", False)],
            },
            {
                "column": "Done", "title": "Competitor analysis", "priority": "low",
                "start": -12, "due": -6, "labels": [], "assignees": ["Olivia"],
            },
        ],
        "dependencies": [],
        "activity": [],
    },
]

NOTIFICATIONS = [
    (Notification.Type.ASSIGNMENT, 'Sofia assigned you to "Build responsive navigation"', "Build responsive navigation", False),
    (Notification.Type.COMMENT, 'Lukas commented on "Homepage hero design"', "Homepage hero design", False),
    (Notification.Type.ASSIGNMENT, 'Emma assigned you to "Product launch blog post"', "Product launch blog post", True),
]


def create_guest_demo_data(guest: UserModel) -> None:
    now = timezone.now()
    today = now.date()
    suffix = uuid.uuid4().hex[:8]

    people: dict[str, UserModel] = {"me": guest}
    for first, last in TEAMMATES:
        people[first] = User.objects.create_user(
            email=f"{first}.{last}.{suffix}@{settings.GUEST_EMAIL_DOMAIN}".lower(),
            password=None,
            first_name=first,
            last_name=last,
            is_verified=True,
            is_guest=True,
        )

    contacts = {
        key: Contact.objects.create(owner=guest, first_name=u.first_name, last_name=u.last_name, email=u.email)
        for key, u in people.items()
    }
    for first, last, email, phone in EXTERNAL_CONTACTS:
        contacts[first] = Contact.objects.create(owner=guest, first_name=first, last_name=last, email=email, phone=phone)

    tasks_by_title: dict[str, Task] = {}
    for spec in BOARDS:
        board = Board.objects.create(title=spec["title"], color=spec["color"], created_by=guest)
        if spec["favorite"]:
            BoardFavorite.objects.create(board=board, user=guest)
        BoardMember.objects.bulk_create([
            BoardMember(board=board, user=people[name], role=role) for name, role in spec["members"].items()
        ])
        columns = {
            c.title: c
            for c in Column.objects.bulk_create([
                Column(board=board, title=title, order=i)
                for i, title in enumerate(settings.DEFAULT_BOARD_COLUMNS)
            ])
        }
        labels = {
            lbl.name: lbl
            for lbl in Label.objects.bulk_create([
                Label(board=board, name=name, color=color) for name, color in spec["labels"].items()
            ])
        }

        for order, t in enumerate(spec["tasks"]):
            task = Task.objects.create(
                board=board,
                column=columns[t["column"]],
                title=t["title"],
                description=t.get("description", ""),
                priority=t["priority"],
                start_date=today + timedelta(days=t["start"]),
                due_date=today + timedelta(days=t["due"]),
                order=(order + 1) * 1024.0,
            )
            task.labels.set([labels[name] for name in t["labels"]])
            task.assignees.set([contacts[name] for name in t["assignees"]])
            Subtask.objects.bulk_create([
                Subtask(task=task, title=title, done=done, order=i) for i, (title, done) in enumerate(t.get("subtasks", []))
            ])
            TimeEntry.objects.bulk_create([
                TimeEntry(task=task, user=people[name], duration_minutes=minutes, note=note)
                for name, minutes, note in t.get("time", [])
            ])
            for author, text, days_ago in t.get("comments", []):
                comment = Comment.objects.create(task=task, author=people[author], text=text)
                posted_at = now - timedelta(days=days_ago)
                Comment.objects.filter(pk=comment.pk).update(created_at=posted_at, updated_at=posted_at)
            tasks_by_title[task.title] = task

        TaskDependency.objects.bulk_create([
            TaskDependency(task=tasks_by_title[task], depends_on=tasks_by_title[depends_on])
            for task, depends_on in spec["dependencies"]
        ])
        for name, action, title, days_ago in spec["activity"]:
            entry = ActivityEntry.objects.create(
                board=board, user=people[name], task=tasks_by_title[title],
                action=action, entity_type=ActivityEntry.EntityType.TASK, entity_title=title,
            )
            ActivityEntry.objects.filter(pk=entry.pk).update(created_at=now - timedelta(days=days_ago))

    Notification.objects.bulk_create([
        Notification(
            recipient=guest,
            type=notification_type,
            message=message,
            board=tasks_by_title[title].board,
            task=tasks_by_title[title],
            is_read=is_read,
        )
        for notification_type, message, title, is_read in NOTIFICATIONS
    ])
