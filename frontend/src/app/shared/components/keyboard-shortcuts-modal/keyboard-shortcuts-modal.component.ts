import { ChangeDetectionStrategy, Component, HostListener, output } from '@angular/core';
import { TranslateModule } from '@ngx-translate/core';

export type Shortcut = { key: string; descriptionKey: string };

@Component({
  selector: 'app-keyboard-shortcuts-modal',
  standalone: true,
  imports: [TranslateModule],
  template: `
    <div class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="shortcuts-title" (click)="closed.emit()">
      <div class="modal-card" (click)="$event.stopPropagation()">
        <div class="modal-header">
          <h2 id="shortcuts-title">{{ 'SHORTCUTS.TITLE' | translate }}</h2>
          <button class="btn-close" aria-label="Close" (click)="closed.emit()">&#10005;</button>
        </div>
        <div class="modal-body">
          @for (s of shortcuts; track s.key) {
            <div class="shortcut-row">
              <kbd>{{ s.key }}</kbd>
              <span>{{ s.descriptionKey | translate }}</span>
            </div>
          }
        </div>
      </div>
    </div>
  `,
  styles: [`
    .modal-backdrop {
      position: fixed; inset: 0; background: rgba(0,0,0,0.4);
      display: flex; align-items: center; justify-content: center; z-index: 2000;
    }
    .modal-card {
      background: var(--color-surface, #fff); border-radius: 16px;
      width: 100%; max-width: 400px; box-shadow: 0 16px 48px rgba(0,0,0,0.2);
    }
    .modal-header {
      display: flex; align-items: center; justify-content: space-between;
      padding: 1rem 1.5rem; border-bottom: 1px solid var(--color-border, #d1d1d1);
      h2 { font-size: 1.1rem; font-weight: 700; color: var(--color-text, #2a3647); }
    }
    .btn-close {
      background: none; border: none; font-size: 1rem; cursor: pointer;
      color: var(--color-muted, #a8a8a8);
      &:hover { color: var(--color-error, #ff8190); }
    }
    .modal-body { padding: 1rem 1.5rem; }
    .shortcut-row {
      display: flex; align-items: center; gap: 1rem; padding: 0.4rem 0;
      kbd {
        background: var(--color-bg, #f6f7f8); border: 1px solid var(--color-border, #d1d1d1);
        border-radius: 4px; padding: 2px 8px; font-size: 0.85rem; font-weight: 600;
        font-family: monospace; min-width: 28px; text-align: center;
        color: var(--color-text, #2a3647);
      }
      span { font-size: 0.9rem; color: var(--color-text, #2a3647); }
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class KeyboardShortcutsModalComponent {
  closed = output<void>();

  shortcuts: Shortcut[] = [
    { key: '?', descriptionKey: 'SHORTCUTS.HELP' },
    { key: 'Esc', descriptionKey: 'SHORTCUTS.CLOSE_MODALS' },
    { key: 'n', descriptionKey: 'SHORTCUTS.NEW_TASK' },
    { key: '/', descriptionKey: 'SHORTCUTS.FOCUS_SEARCH' },
    { key: '← →', descriptionKey: 'SHORTCUTS.NAV_COLUMNS' },
    { key: '↑ ↓', descriptionKey: 'SHORTCUTS.NAV_TASKS' },
    { key: 'Enter', descriptionKey: 'SHORTCUTS.OPEN_TASK' },
  ];

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.closed.emit();
  }
}
