import { ChangeDetectionStrategy, Component, HostListener, input, output } from '@angular/core';
import { TranslateModule } from '@ngx-translate/core';
import { FocusTrapDirective } from '../../../shared/directives/focus-trap.directive';

@Component({
  selector: 'app-confirm-dialog',
  standalone: true,
  imports: [TranslateModule, FocusTrapDirective],
  templateUrl: './confirm-dialog.component.html',
  styleUrl: './confirm-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ConfirmDialogComponent {
  message = input<string>('Are you sure?');
  confirmLabel = input<string>('');
  confirmed = output<void>();
  cancelled = output<void>();

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.cancelled.emit();
  }
}
