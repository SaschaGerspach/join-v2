import { Component, inject, input, output, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Column } from '../../../../core/columns/columns-api.service';
import { Contact, ContactsApiService } from '../../../../core/contacts/contacts-api.service';
import { CreateTaskPayload } from '../../../../core/tasks/tasks-api.service';

@Component({
  selector: 'app-create-task-modal',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './create-task-modal.component.html',
  styleUrl: './create-task-modal.component.scss',
})
export class CreateTaskModalComponent implements OnInit {
  private readonly contactsApi = inject(ContactsApiService);

  columnId = input.required<number>();
  columns = input.required<Column[]>();
  contacts = input<Contact[]>([]);

  confirmed = output<CreateTaskPayload>();
  cancelled = output<void>();

  title = '';
  description = '';
  priority: 'low' | 'medium' | 'high' | 'urgent' = 'medium';
  dueDate = '';
  assignedTo: number | null = null;
  selectedColumnId: number | null = null;

  readonly priorities = ['urgent', 'high', 'medium', 'low'] as const;

  ngOnInit(): void {
    this.selectedColumnId = this.columnId();
  }

  submit(): void {
    const t = this.title.trim();
    if (!t) return;
    this.confirmed.emit({
      title: t,
      description: this.description.trim() || undefined,
      priority: this.priority,
      due_date: this.dueDate || null,
      column: this.selectedColumnId,
      assigned_to: this.assignedTo,
    } as CreateTaskPayload);
  }
}
