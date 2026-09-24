import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';
import { BoardStateService } from '../../services/board-state.service';

@Component({
  selector: 'app-board-filter-bar',
  imports: [FormsModule, TranslateModule],
  templateUrl: './board-filter-bar.component.html',
  styleUrl: './board-filter-bar.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardFilterBarComponent {
  protected readonly state = inject(BoardStateService);

  showFilterNameInput = signal(false);
  filterNameInput = signal('');

  inputValue(event: Event): string {
    return (event.target as HTMLInputElement).value;
  }

  saveFilter(): void {
    this.filterNameInput.set('');
    this.showFilterNameInput.set(true);
  }

  confirmSaveFilter(): void {
    const name = this.filterNameInput().trim();
    if (name) {
      this.state.saveCurrentFilter(name);
    }
    this.showFilterNameInput.set(false);
  }

  applySavedFilter(event: Event): void {
    const name = (event.target as HTMLSelectElement).value;
    if (!name) return;
    const filter = this.state.savedFilters().find(f => f.name === name);
    if (filter) this.state.applySavedFilter(filter);
    (event.target as HTMLSelectElement).value = '';
  }
}
