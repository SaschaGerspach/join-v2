import { ChangeDetectionStrategy, Component, ElementRef, ViewChild, computed, inject, input, model, signal } from '@angular/core';
import { CdkConnectedOverlay, CdkOverlayOrigin, ConnectedPosition, Overlay } from '@angular/cdk/overlay';
import { TranslateModule } from '@ngx-translate/core';
import { Contact } from '../../../../core/contacts/contacts-api.service';
import { UserAvatarComponent } from '../../../../shared/components/user-avatar/user-avatar.component';

let nextId = 0;

@Component({
  selector: 'app-assignee-picker',
  standalone: true,
  imports: [TranslateModule, UserAvatarComponent, CdkConnectedOverlay, CdkOverlayOrigin],
  templateUrl: './assignee-picker.component.html',
  styleUrl: './assignee-picker.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AssigneePickerComponent {
  @ViewChild('searchInput') searchInput?: ElementRef<HTMLInputElement>;

  contacts = input.required<Contact[]>();
  selectedIds = model.required<number[]>();

  query = signal('');
  open = signal(false);
  activeIndex = signal(0);
  listWidth = signal(0);

  readonly listboxId = `assignee-listbox-${nextId++}`;

  readonly positions: ConnectedPosition[] = [
    { originX: 'start', originY: 'bottom', overlayX: 'start', overlayY: 'top', offsetY: 4 },
    { originX: 'start', originY: 'top', overlayX: 'start', overlayY: 'bottom', offsetY: -4 },
  ];

  // The list floats outside the modal; like a native select it closes when the
  // surrounding container scrolls instead of drifting over the modal header/footer.
  readonly scrollStrategy = inject(Overlay).scrollStrategies.close();

  selectedContacts = computed(() => {
    const byId = new Map(this.contacts().map(c => [c.id, c]));
    return this.selectedIds()
      .map(id => byId.get(id))
      .filter((c): c is Contact => c !== undefined);
  });

  suggestions = computed(() => {
    const q = this.query().trim().toLowerCase();
    const selected = new Set(this.selectedIds());
    return this.contacts().filter(c =>
      !selected.has(c.id) && `${c.first_name} ${c.last_name} ${c.email}`.toLowerCase().includes(q),
    );
  });

  optionId(index: number): string {
    return `${this.listboxId}-${index}`;
  }

  openList(): void {
    this.listWidth.set(this.searchInput?.nativeElement.offsetWidth ?? 0);
    this.open.set(true);
  }

  add(contact: Contact): void {
    this.selectedIds.update(ids => [...ids, contact.id]);
    this.query.set('');
    this.resetActive();
  }

  remove(id: number): void {
    this.selectedIds.update(ids => ids.filter(x => x !== id));
  }

  onInput(value: string): void {
    this.query.set(value);
    this.resetActive();
    this.openList();
  }

  onKeydown(event: KeyboardEvent): void {
    const list = this.suggestions();
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        if (!this.open()) this.openList();
        this.moveActive(Math.min(this.activeIndex() + 1, list.length - 1));
        break;
      case 'ArrowUp':
        event.preventDefault();
        this.moveActive(Math.max(this.activeIndex() - 1, 0));
        break;
      case 'Enter':
        if (this.open() && list[this.activeIndex()]) {
          event.preventDefault();
          this.add(list[this.activeIndex()]);
        }
        break;
      case 'Escape':
        // Only close the suggestions; the surrounding modal listens for Escape on document.
        if (this.open()) {
          event.stopPropagation();
          this.open.set(false);
        }
        break;
      case 'Backspace':
        if (!this.query() && this.selectedIds().length > 0) {
          this.selectedIds.update(ids => ids.slice(0, -1));
        }
        break;
    }
  }

  // A new result set starts at the top, not at the old scroll offset.
  private resetActive(): void {
    this.activeIndex.set(0);
    document.getElementById(this.listboxId)?.scrollTo({ top: 0 });
  }

  private moveActive(index: number): void {
    this.activeIndex.set(index);
    document.getElementById(this.optionId(index))?.scrollIntoView({ block: 'nearest' });
  }
}
