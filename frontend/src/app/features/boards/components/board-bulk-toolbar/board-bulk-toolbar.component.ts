import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';
import { BoardStateService } from '../../services/board-state.service';

@Component({
  selector: 'app-board-bulk-toolbar',
  imports: [FormsModule, TranslateModule],
  templateUrl: './board-bulk-toolbar.component.html',
  styleUrl: './board-bulk-toolbar.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardBulkToolbarComponent {
  protected readonly state = inject(BoardStateService);
}
