import { ChangeDetectionStrategy, Component, DestroyRef, inject, input, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { CustomField, TaskFieldValue, TasksApiService } from '../../../../core/tasks/tasks-api.service';
import { BoardsApiService } from '../../../../core/boards/boards-api.service';
import { ToastService } from '../../../../shared/services/toast.service';

@Component({
  selector: 'app-task-custom-fields',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './task-custom-fields.component.html',
  styleUrl: './task-custom-fields.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TaskCustomFieldsComponent implements OnInit {
  private readonly tasksApi = inject(TasksApiService);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  taskId = input.required<number>();
  boardId = input.required<number>();

  fields = signal<CustomField[]>([]);
  values = signal<Record<number, string>>({});

  ngOnInit(): void {
    forkJoin({
      fields: this.boardsApi.getCustomFields(this.boardId()),
      values: this.tasksApi.getTaskFieldValues(this.taskId()),
    }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: ({ fields, values }) => {
        this.fields.set(fields);
        const map: Record<number, string> = {};
        for (const v of values.values) {
          map[v.field_id] = v.value;
        }
        this.fields().forEach(f => { if (!(f.id in map)) map[f.id] = ''; });
        this.values.set(map);
      },
    });
  }

  updateValue(fieldId: number, value: string): void {
    this.values.update(v => ({ ...v, [fieldId]: value }));
  }

  save(): void {
    const entries: TaskFieldValue[] = this.fields().map(f => ({
      field_id: f.id,
      value: this.values()[f.id] ?? '',
    }));
    this.tasksApi.setTaskFieldValues(this.taskId(), entries)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => this.toast.show('Custom fields saved'),
        error: () => this.toast.show('Failed to save fields.', 'error'),
      });
  }
}
