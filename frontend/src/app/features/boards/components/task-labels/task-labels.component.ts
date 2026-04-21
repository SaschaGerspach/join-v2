import { ChangeDetectionStrategy, Component, DestroyRef, inject, input, signal, OnInit, model } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';
import { Label, LabelsApiService } from '../../../../core/tasks/labels-api.service';
import { ToastService } from '../../../../shared/services/toast.service';

@Component({
  selector: 'app-task-labels',
  standalone: true,
  imports: [FormsModule, TranslateModule],
  templateUrl: './task-labels.component.html',
  styleUrl: './task-labels.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TaskLabelsComponent implements OnInit {
  private readonly labelsApi = inject(LabelsApiService);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  boardId = input.required<number>();
  selectedLabelIds = model.required<Set<number>>();

  boardLabels = signal<Label[]>([]);
  newLabelName = '';
  newLabelColor = '#29abe2';

  ngOnInit(): void {
    this.labelsApi.getByBoard(this.boardId())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(labels => this.boardLabels.set(labels));
  }

  toggleLabel(labelId: number): void {
    this.selectedLabelIds.update(set => {
      const next = new Set(set);
      if (next.has(labelId)) next.delete(labelId);
      else next.add(labelId);
      return next;
    });
  }

  createLabel(): void {
    const name = this.newLabelName.trim();
    if (!name) return;
    this.labelsApi.create(this.boardId(), name, this.newLabelColor)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: label => {
          this.boardLabels.update(l => [...l, label]);
          this.selectedLabelIds.update(s => { const n = new Set(s); n.add(label.id); return n; });
          this.newLabelName = '';
        },
        error: () => this.toast.show('Failed to create label.', 'error'),
      });
  }
}
