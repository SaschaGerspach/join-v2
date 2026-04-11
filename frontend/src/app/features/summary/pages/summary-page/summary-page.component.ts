import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { SlicePipe } from '@angular/common';
import { AuthService } from '../../../../core/auth/auth.service';
import { BoardsApiService, Board } from '../../../../core/boards/boards-api.service';
import { TasksApiService, Task } from '../../../../core/tasks/tasks-api.service';
import { forkJoin } from 'rxjs';

@Component({
  selector: 'app-summary-page',
  standalone: true,
  imports: [SlicePipe],
  templateUrl: './summary-page.component.html',
  styleUrl: './summary-page.component.scss',
})
export class SummaryPageComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly tasksApi = inject(TasksApiService);
  private readonly router = inject(Router);

  boards = signal<Board[]>([]);
  tasks = signal<Task[]>([]);

  userName = computed(() => {
    const user = this.auth.user();
    if (!user) return '';
    const namePart = user.email.split('@')[0];
    return namePart.charAt(0).toUpperCase() + namePart.slice(1);
  });

  totalTasks = computed(() => this.tasks().length);
  urgentTasks = computed(() => this.tasks().filter(t => t.priority === 'urgent').length);
  highTasks = computed(() => this.tasks().filter(t => t.priority === 'high').length);

  nextDeadline = computed(() => {
    const upcoming = this.tasks()
      .filter(t => t.due_date)
      .sort((a, b) => new Date(a.due_date!).getTime() - new Date(b.due_date!).getTime());
    return upcoming[0]?.due_date ?? null;
  });

  greeting = computed(() => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  });

  ngOnInit(): void {
    this.boardsApi.getAll().subscribe(boards => {
      this.boards.set(boards);
      if (boards.length === 0) {
        this.tasks.set([]);
        return;
      }
      forkJoin(boards.map(b => this.tasksApi.getByBoard(b.id))).subscribe(taskArrays => {
        this.tasks.set(taskArrays.flat());
      });
    });
  }

  goToBoards(): void {
    this.router.navigate(['/boards']);
  }
}
