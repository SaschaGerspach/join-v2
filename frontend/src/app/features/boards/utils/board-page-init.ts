import { assertInInjectionContext, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute } from '@angular/router';
import { BoardsApiService } from '../../../core/boards/boards-api.service';

export function initBoardPage() {
  assertInInjectionContext(initBoardPage);
  const route = inject(ActivatedRoute);
  const boardsApi = inject(BoardsApiService);
  const destroyRef = inject(DestroyRef);

  const boardId = signal(Number(route.snapshot.paramMap.get('id')));
  const boardTitle = signal('Board');

  boardsApi.getById(boardId())
    .pipe(takeUntilDestroyed(destroyRef))
    .subscribe({ next: b => boardTitle.set(b.title) });

  return { boardId, boardTitle, destroyRef };
}
