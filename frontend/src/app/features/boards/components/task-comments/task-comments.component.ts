import { ChangeDetectionStrategy, Component, DestroyRef, inject, input, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { SlicePipe } from '@angular/common';
import { Comment, CommentsApiService } from '../../../../core/tasks/comments-api.service';
import { AuthService } from '../../../../core/auth/auth.service';
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
  private readonly commentsApi = inject(CommentsApiService);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly auth = inject(AuthService);

  taskId = input.required<number>();

  comments = signal<Comment[]>([]);
  newCommentText = signal('');
  editingCommentId = signal<number | null>(null);
  editingCommentText = '';

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
    return c.author_id === +(this.auth.user()?.id ?? 0);
  }

  deleteComment(id: number): void {
    this.commentsApi.delete(this.taskId(), id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => this.comments.update(list => list.filter(c => c.id !== id)),
        error: () => this.toast.show('Failed to delete comment.', 'error'),
      });
  }
}
