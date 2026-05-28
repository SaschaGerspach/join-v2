import { ChangeDetectionStrategy, Component, AfterViewInit, ElementRef, HostListener, inject, input, output, OnInit, signal, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';
import { Column } from '../../../../core/columns/columns-api.service';
import { Contact } from '../../../../core/contacts/contacts-api.service';
import { CreateTaskPayload } from '../../../../core/tasks/tasks-api.service';
import { FocusTrapDirective } from '../../../../shared/directives/focus-trap.directive';

@Component({
  selector: 'app-create-task-modal',
  standalone: true,
  imports: [FormsModule, TranslateModule, FocusTrapDirective],
  templateUrl: './create-task-modal.component.html',
  styleUrl: './create-task-modal.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreateTaskModalComponent implements OnInit, AfterViewInit {
  @ViewChild('titleInput') titleInput!: ElementRef<HTMLInputElement>;

  columnId = input.required<number>();
  columns = input.required<Column[]>();
  contacts = input<Contact[]>([]);

  confirmed = output<CreateTaskPayload>();
  cancelled = output<void>();

  title = signal('');
  description = signal('');
  priority = signal<'low' | 'medium' | 'high' | 'urgent'>('medium');
  dueDate = signal('');
  assignedTo = signal<number[]>([]);
  selectedColumnId = signal<number | null>(null);
  submitted = signal(false);

  readonly priorities = ['urgent', 'high', 'medium', 'low'] as const;

  ngOnInit(): void {
    this.selectedColumnId.set(this.columnId());
  }

  ngAfterViewInit(): void {
    this.titleInput?.nativeElement.focus();
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.cancelled.emit();
  }

  toggleAssignee(id: number): void {
    const current = this.assignedTo();
    if (current.includes(id)) {
      this.assignedTo.set(current.filter(x => x !== id));
    } else {
      this.assignedTo.set([...current, id]);
    }
  }

  submit(): void {
    this.submitted.set(true);
    const t = this.title().trim();
    if (!t) return;
    this.confirmed.emit({
      title: t,
      description: this.description().trim() || undefined,
      priority: this.priority(),
      due_date: this.dueDate() || null,
      column: this.selectedColumnId(),
      assigned_to: this.assignedTo(),
    });
  }
}
