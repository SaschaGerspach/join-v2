import { ChangeDetectionStrategy, Component, AfterViewInit, DestroyRef, ElementRef, HostListener, inject, input, output, OnInit, signal, ViewChild } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';
import { Column } from '../../../../core/columns/columns-api.service';
import { Contact } from '../../../../core/contacts/contacts-api.service';
import { CreateTaskPayload } from '../../../../core/tasks/tasks-api.service';
import { AiApiService, AI_FEATURE } from '../../../../core/ai/ai-api.service';
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

  private readonly destroyRef = inject(DestroyRef);
  readonly ai = inject(AiApiService);
  readonly aiFeature = AI_FEATURE;

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
  generatingDescription = signal(false);
  categorizing = signal(false);

  readonly priorities = ['urgent', 'high', 'medium', 'low'] as const;

  ngOnInit(): void {
    this.selectedColumnId.set(this.columnId());
    this.ai.ensureLoaded();
  }

  generateDescription(): void {
    const title = this.title().trim();
    if (!title || this.generatingDescription()) return;
    this.generatingDescription.set(true);
    this.ai.generateDescription(title)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: text => { this.description.set(text); this.generatingDescription.set(false); },
        error: () => this.generatingDescription.set(false),
      });
  }

  suggestCategory(): void {
    const title = this.title().trim();
    if (!title || this.categorizing()) return;
    this.categorizing.set(true);
    this.ai.categorize(title, this.description().trim() || undefined)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          if ((this.priorities as readonly string[]).includes(res.priority)) {
            this.priority.set(res.priority as 'low' | 'medium' | 'high' | 'urgent');
          }
          this.categorizing.set(false);
        },
        error: () => this.categorizing.set(false),
      });
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
