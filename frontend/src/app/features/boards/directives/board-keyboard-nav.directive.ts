import { Directive, ElementRef, HostListener, inject, signal } from '@angular/core';
import { BoardStateService } from '../services/board-state.service';

@Directive({
  selector: '[appBoardKeyboardNav]',
  standalone: true,
  exportAs: 'boardKeyNav',
})
export class BoardKeyboardNavDirective {
  private readonly state = inject(BoardStateService);
  private readonly el = inject(ElementRef);

  readonly focusedColumnIndex = signal(-1);
  readonly focusedTaskIndex = signal(-1);

  focusedColumnId(): number | null {
    const cols = this.state.columns();
    const idx = this.focusedColumnIndex();
    return idx >= 0 && idx < cols.length ? cols[idx].id : null;
  }

  focusedTaskId(): number | null {
    const colId = this.focusedColumnId();
    if (colId === null) return null;
    const tasks = this.state.tasksForColumn(colId);
    const idx = this.focusedTaskIndex();
    return idx >= 0 && idx < tasks.length ? tasks[idx].id : null;
  }

  @HostListener('document:keydown', ['$event'])
  onKeydown(event: KeyboardEvent): void {
    if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement || event.target instanceof HTMLSelectElement) return;
    if (this.state.selectedTask() || this.state.addingTaskForColumn() !== null) return;

    const columns = this.state.columns();
    if (!columns.length) return;

    switch (event.key) {
      case '/':
        event.preventDefault();
        this.focusSearch();
        break;
      case 'n': {
        const colIdx = Math.max(0, this.focusedColumnIndex());
        this.state.addingTaskForColumn.set(columns[colIdx].id);
        break;
      }
      case 'ArrowRight': {
        event.preventDefault();
        const next = Math.min(this.focusedColumnIndex() + 1, columns.length - 1);
        this.focusedColumnIndex.set(next);
        this.focusedTaskIndex.set(0);
        break;
      }
      case 'ArrowLeft': {
        event.preventDefault();
        const prev = Math.max(this.focusedColumnIndex() - 1, 0);
        this.focusedColumnIndex.set(prev);
        this.focusedTaskIndex.set(0);
        break;
      }
      case 'ArrowDown': {
        event.preventDefault();
        const colIdx = Math.max(0, this.focusedColumnIndex());
        const tasks = this.state.tasksForColumn(columns[colIdx].id);
        this.focusedTaskIndex.set(Math.min(this.focusedTaskIndex() + 1, tasks.length - 1));
        break;
      }
      case 'ArrowUp': {
        event.preventDefault();
        this.focusedTaskIndex.set(Math.max(this.focusedTaskIndex() - 1, 0));
        break;
      }
      case 'Enter': {
        const colIdx = this.focusedColumnIndex();
        const taskIdx = this.focusedTaskIndex();
        if (colIdx >= 0 && taskIdx >= 0) {
          const tasks = this.state.tasksForColumn(columns[colIdx].id);
          if (tasks[taskIdx]) {
            this.state.selectedTask.set(tasks[taskIdx]);
          }
        }
        break;
      }
      case 'Escape':
        this.focusedColumnIndex.set(-1);
        this.focusedTaskIndex.set(-1);
        break;
    }
  }

  private focusSearch(): void {
    const input = this.el.nativeElement.querySelector('input[type="search"]') as HTMLInputElement | null;
    input?.focus();
  }
}
