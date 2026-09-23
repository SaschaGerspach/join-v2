import { ChangeDetectionStrategy, Component, ElementRef, ViewChild, computed, inject, input, model, signal } from '@angular/core';
import { CdkConnectedOverlay, CdkOverlayOrigin, ConnectedPosition, Overlay } from '@angular/cdk/overlay';
import { CdkFixedSizeVirtualScroll, CdkVirtualForOf, CdkVirtualScrollViewport } from '@angular/cdk/scrolling';
import { TranslateModule } from '@ngx-translate/core';
import { Contact } from '../../../../core/contacts/contacts-api.service';
import { UserAvatarComponent } from '../../../../shared/components/user-avatar/user-avatar.component';

let nextId = 0;
const MAX_VISIBLE_OPTIONS = 6;

@Component({
  selector: 'app-assignee-picker',
  imports: [TranslateModule, UserAvatarComponent, CdkConnectedOverlay, CdkOverlayOrigin, CdkVirtualScrollViewport, CdkFixedSizeVirtualScroll, CdkVirtualForOf],
  templateUrl: './assignee-picker.component.html',
  styleUrl: './assignee-picker.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AssigneePickerComponent {
  @ViewChild('searchInput') searchInput?: ElementRef<HTMLInputElement>;
  @ViewChild(CdkVirtualScrollViewport) viewport?: CdkVirtualScrollViewport;

  contacts = input.required<Contact[]>();
  selectedIds = model.required<number[]>();

  query = signal('');
  open = signal(false);
  activeIndex = signal(0);
  listWidth = signal(0);

  readonly listboxId = `assignee-listbox-${nextId++}`;
  readonly optionHeight = 36;

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

  // Only the visible rows are rendered, so large address books stay cheap to filter and open.
  listHeight = computed(() => Math.min(this.suggestions().length, MAX_VISIBLE_OPTIONS) * this.optionHeight);

  optionId(index: number): string {
    return `${this.listboxId}-${index}`;
  }

  trackById(_index: number, contact: Contact): number {
    return contact.id;
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
        if (!this.open()) {
          this.openList();
          this.resetActive();
        } else if (list.length > 0) {
          this.moveActive(Math.min(this.activeIndex() + 1, list.length - 1));
        }
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
      case 'Backspace': {
        // Assignees outside this user's address book have no chip and must not be removed unseen.
        const lastVisible = this.selectedContacts().at(-1);
        if (!this.query() && lastVisible) {
          this.remove(lastVisible.id);
        }
        break;
      }
    }
  }

  // A new result set starts at the top, not at the old scroll offset.
  private resetActive(): void {
    this.activeIndex.set(0);
    this.viewport?.scrollToOffset(0);
  }

  // Rows outside the viewport are not rendered, so scrolling goes through the viewport
  // instead of scrollIntoView; it only moves when the active row would leave the view.
  private moveActive(index: number): void {
    this.activeIndex.set(index);
    const viewport = this.viewport;
    if (!viewport) return;
    const top = index * this.optionHeight;
    const bottom = top + this.optionHeight;
    const scrollTop = viewport.measureScrollOffset('top');
    const height = viewport.getViewportSize();
    if (top < scrollTop) {
      viewport.scrollToOffset(top);
    } else if (bottom > scrollTop + height) {
      viewport.scrollToOffset(bottom - height);
    }
  }
}
