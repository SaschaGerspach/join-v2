import { Component, inject, input, output, signal, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Task, TasksApiService } from '../../../../core/tasks/tasks-api.service';
import { Column } from '../../../../core/columns/columns-api.service';
import { Subtask, SubtasksApiService } from '../../../../core/tasks/subtasks-api.service';

@Component({
  selector: 'app-task-detail-modal',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './task-detail-modal.component.html',
  styleUrl: './task-detail-modal.component.scss',
})
export class TaskDetailModalComponent implements OnInit {
  private readonly tasksApi = inject(TasksApiService);
  private readonly subtasksApi = inject(SubtasksApiService);

  task = input.required<Task>();
  columns = input.required<Column[]>();

  closed = output<void>();
  taskUpdated = output<Task>();
  taskDeleted = output<number>();

  title = signal('');
  description = signal('');
  priority = signal<'low' | 'medium' | 'high' | 'urgent'>('medium');
  dueDate = signal('');
  columnId = signal<number | null>(null);

  subtasks = signal<Subtask[]>([]);
  newSubtaskTitle = signal('');

  readonly priorities = ['urgent', 'high', 'medium', 'low'] as const;

  ngOnInit(): void {
    const t = this.task();
    this.title.set(t.title);
    this.description.set(t.description ?? '');
    this.priority.set(t.priority);
    this.dueDate.set(t.due_date ?? '');
    this.columnId.set(t.column);

    this.subtasksApi.getByTask(t.id).subscribe(subs => this.subtasks.set(subs));
  }

  save(): void {
    const payload = {
      title: this.title().trim(),
      description: this.description().trim(),
      priority: this.priority(),
      due_date: this.dueDate() || null,
      column: this.columnId(),
    };

    this.tasksApi.patch(this.task().id, payload).subscribe(updated => {
      this.taskUpdated.emit(updated);
      this.closed.emit();
    });
  }

  deleteTask(): void {
    this.tasksApi.delete(this.task().id).subscribe(() => {
      this.taskDeleted.emit(this.task().id);
      this.closed.emit();
    });
  }

  addSubtask(): void {
    const title = this.newSubtaskTitle().trim();
    if (!title) return;

    this.subtasksApi.create(this.task().id, title).subscribe(sub => {
      this.subtasks.update(s => [...s, sub]);
      this.newSubtaskTitle.set('');
    });
  }

  toggleSubtask(sub: Subtask): void {
    this.subtasksApi.patch(this.task().id, sub.id, { done: !sub.done }).subscribe(updated => {
      this.subtasks.update(s => s.map(x => x.id === updated.id ? updated : x));
    });
  }

  deleteSubtask(sub: Subtask): void {
    this.subtasksApi.delete(this.task().id, sub.id).subscribe(() => {
      this.subtasks.update(s => s.filter(x => x.id !== sub.id));
    });
  }

  close(): void {
    this.closed.emit();
  }
}
