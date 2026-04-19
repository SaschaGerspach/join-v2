from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from boards_api.models import Board
from columns_api.models import Column
from contacts_api.models import Contact
from tasks_api.models import Task


def create_demo_data(user):
    board = Board.objects.create(title="My First Board", created_by=user)
    columns = Column.objects.bulk_create([
        Column(board=board, title=t, order=i)
        for i, t in enumerate(settings.DEFAULT_BOARD_COLUMNS)
    ])
    col_map = {c.title: c for c in columns}

    contact = Contact.objects.create(
        owner=user,
        first_name=user.first_name or "Demo",
        last_name=user.last_name or "User",
        email=user.email,
    )

    today = timezone.now().date()

    tasks = Task.objects.bulk_create([
        Task(board=board, column=col_map["To do"], title="Explore the board", description="Click on tasks to see details, drag them between columns.", priority="low", order=0),
        Task(board=board, column=col_map["To do"], title="Create your first task", description="Use the '+ Add Task' button at the bottom of any column.", priority="medium", order=1, due_date=today + timedelta(days=3)),
        Task(board=board, column=col_map["To do"], title="Invite a team member", description="Go to the boards overview and click the members icon.", priority="high", order=2),
        Task(board=board, column=col_map["In progress"], title="Try drag & drop", description="Move this task to another column.", priority="medium", order=0),
        Task(board=board, column=col_map["Await feedback"], title="Check the calendar", description="Tasks with due dates show up in the calendar view.", priority="low", order=0, due_date=today + timedelta(days=7)),
        Task(board=board, column=col_map["Done"], title="Sign up for Join", description="Welcome aboard!", priority="low", order=0),
    ])
    tasks[3].assignees.add(contact)
