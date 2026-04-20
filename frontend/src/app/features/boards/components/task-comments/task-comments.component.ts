import { ChangeDetectionStrategy, Component, DestroyRef, ElementRef, ViewChild, inject, input, signal, computed, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { SlicePipe } from '@angular/common';
import { Comment, CommentsApiService } from '../../../../core/tasks/comments-api.service';
import { AuthService } from '../../../../core/auth/auth.service';
import { Contact } from '../../../../core/contacts/contacts-api.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { MarkdownPipe } from '../../../../shared/pipes/markdown.pipe';

@Component({
  selector: 'app-task-comments',
  standalone: true,
  imports: [FormsModule, SlicePipe, MarkdownPipe],
  templateUrl: './task-comments.component.html',
  styleUrl: './task-comments.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TaskCommentsComponent implements OnInit {
  @ViewChild('commentTextarea') commentTextarea!: ElementRef<HTMLTextAreaElement>;
  private readonly commentsApi = inject(CommentsApiService);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly auth = inject(AuthService);

  taskId = input.required<number>();
  contacts = input<Contact[]>([]);

  comments = signal<Comment[]>([]);
  newCommentText = signal('');
  editingCommentId = signal<number | null>(null);
  editingCommentText = '';

  mentionQuery = signal('');
  mentionActive = signal(false);
  mentionStartIndex = signal(0);
  mentionSelectedIndex = signal(0);

  mentionSuggestions = computed(() => {
    const q = this.mentionQuery().toLowerCase();
    if (!q) return this.contacts().filter(c => c.email).slice(0, 8);
    return this.contacts()
      .filter(c => c.email && (
        c.first_name.toLowerCase().includes(q) ||
        c.last_name.toLowerCase().includes(q) ||
        c.email.toLowerCase().includes(q)
      ))
      .slice(0, 8);
  });

  ngOnInit(): void {
    this.commentsApi.getAll(this.taskId())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(comments => this.comments.set(comments));
  }

  addComment(): void {
    const text = this.newCommentText().trim();
    if (!text) return;
    this.commentsApi.create(this.taskId(), text)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: c => {
          this.comments.update(list => [...list, c]);
          this.newCommentText.set('');
        },
        error: () => this.toast.show('Failed to add comment.', 'error'),
      });
  }

  startEditComment(c: Comment): void {
    this.editingCommentId.set(c.id);
    this.editingCommentText = c.text;
  }

  confirmEditComment(c: Comment): void {
    const text = this.editingCommentText.trim();
    this.editingCommentId.set(null);
    if (!text || text === c.text) return;
    this.commentsApi.patch(this.taskId(), c.id, text)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: updated => this.comments.update(list => list.map(x => x.id === updated.id ? updated : x)),
        error: () => this.toast.show('Failed to edit comment.', 'error'),
      });
  }

  isOwnComment(c: Comment): boolean {
    return c.author_id === (this.auth.user()?.id ?? 0);
  }

  deleteComment(id: number): void {
    this.commentsApi.delete(this.taskId(), id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => this.comments.update(list => list.filter(c => c.id !== id)),
        error: () => this.toast.show('Failed to delete comment.', 'error'),
      });
  }

  onCommentInput(event: Event): void {
    const textarea = event.target as HTMLTextAreaElement;
    const text = textarea.value;
    const cursorPos = textarea.selectionStart;

    const beforeCursor = text.slice(0, cursorPos);
    const atMatch = beforeCursor.match(/@([^\s@]*)$/);

    if (atMatch) {
      this.mentionActive.set(true);
      this.mentionStartIndex.set(cursorPos - atMatch[1].length);
      this.mentionQuery.set(atMatch[1]);
      this.mentionSelectedIndex.set(0);
    } else {
      this.mentionActive.set(false);
    }
  }

  onCommentKeydown(event: KeyboardEvent): void {
    if (!this.mentionActive()) return;
    const suggestions = this.mentionSuggestions();
    if (suggestions.length === 0) return;

    if (event.key === 'ArrowDown') {
      event.preventDefault();
      this.mentionSelectedIndex.update(i => Math.min(i + 1, suggestions.length - 1));
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      this.mentionSelectedIndex.update(i => Math.max(i - 1, 0));
    } else if (event.key === 'Enter' || event.key === 'Tab') {
      event.preventDefault();
      this.selectMention(suggestions[this.mentionSelectedIndex()]);
    } else if (event.key === 'Escape') {
      this.mentionActive.set(false);
    }
  }

  selectMention(contact: Contact): void {
    const textarea = this.commentTextarea.nativeElement;
    const text = this.newCommentText();
    const cursorPos = textarea.selectionStart;
    const start = this.mentionStartIndex() - 1; // include the @
    const before = text.slice(0, start);
    const after = text.slice(cursorPos);
    const mention = `@${contact.email} `;
    this.newCommentText.set(before + mention + after);
    this.mentionActive.set(false);

    setTimeout(() => {
      const newPos = before.length + mention.length;
      textarea.focus();
      textarea.setSelectionRange(newPos, newPos);
    });
  }
}
