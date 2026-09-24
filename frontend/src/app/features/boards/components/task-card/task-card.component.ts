import { ChangeDetectionStrategy, Component, inject, input } from '@angular/core';
import { SlicePipe } from '@angular/common';
import { TranslateModule } from '@ngx-translate/core';
import { Task } from '../../../../core/tasks/tasks-api.service';
import { MarkdownPipe } from '../../../../shared/pipes/markdown.pipe';
import { BoardStateService } from '../../services/board-state.service';

@Component({
  selector: 'app-task-card',
  imports: [SlicePipe, TranslateModule, MarkdownPipe],
  templateUrl: './task-card.component.html',
  styleUrl: './task-card.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TaskCardComponent {
  protected readonly state = inject(BoardStateService);

  task = input.required<Task>();
}
