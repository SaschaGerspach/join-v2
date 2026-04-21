import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, computed, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { Contact, ContactsApiService } from '../../../../core/contacts/contacts-api.service';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { AVATAR_COLORS } from '../../../../shared/constants/colors';
import { ToastService } from '../../../../shared/services/toast.service';
import { TranslateModule } from '@ngx-translate/core';

type ContactForm = {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
};

@Component({
  selector: 'app-contacts-page',
  standalone: true,
  imports: [FormsModule, LoadingSpinnerComponent, ConfirmDialogComponent, TranslateModule],
  templateUrl: './contacts-page.component.html',
  styleUrl: './contacts-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ContactsPageComponent implements OnInit {
  private readonly api = inject(ContactsApiService);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  contacts = signal<Contact[]>([]);
  selectedContact = signal<Contact | null>(null);
  showForm = signal(false);
  editMode = signal(false);
  loading = signal(true);
  pendingDeleteId = signal<number | null>(null);

  form: ContactForm = { first_name: '', last_name: '', email: '', phone: '' };

  groupedContacts = computed(() => {
    const groups = new Map<string, Contact[]>();
    for (const c of this.contacts()) {
      const letter = (c.last_name[0] ?? c.first_name[0] ?? '#').toUpperCase();
      if (!groups.has(letter)) groups.set(letter, []);
      groups.get(letter)!.push(c);
    }
    return Array.from(groups.entries()).sort(([a], [b]) => a.localeCompare(b));
  });

  ngOnInit(): void {
    this.api.getAll().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: contacts => { this.contacts.set(contacts); this.loading.set(false); },
      error: () => { this.toast.show('Failed to load contacts.', 'error'); this.loading.set(false); },
    });
  }

  openCreate(): void {
    this.form = { first_name: '', last_name: '', email: '', phone: '' };
    this.editMode.set(false);
    this.showForm.set(true);
    this.selectedContact.set(null);
  }

  openEdit(contact: Contact): void {
    this.form = { ...contact };
    this.editMode.set(true);
    this.showForm.set(true);
  }

  selectContact(contact: Contact): void {
    this.selectedContact.set(contact);
    this.showForm.set(false);
  }

  save(): void {
    if (!this.form.first_name.trim() || !this.form.last_name.trim() || !this.form.email.trim()) return;

    if (this.editMode() && this.selectedContact()) {
      this.api.patch(this.selectedContact()!.id, this.form).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
        next: updated => {
          this.contacts.update(c => c.map(x => x.id === updated.id ? updated : x));
          this.selectedContact.set(updated);
          this.showForm.set(false);
        },
        error: () => this.toast.show('Failed to update contact.', 'error'),
      });
    } else {
      this.api.create(this.form).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
        next: created => {
          this.contacts.update(c => [...c, created]);
          this.selectedContact.set(created);
          this.showForm.set(false);
        },
        error: () => this.toast.show('Failed to create contact.', 'error'),
      });
    }
  }

  deleteContact(id: number): void {
    this.pendingDeleteId.set(id);
  }

  confirmDeleteContact(): void {
    const id = this.pendingDeleteId();
    if (id === null) return;
    this.api.delete(id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.contacts.update(c => c.filter(x => x.id !== id));
        if (this.selectedContact()?.id === id) {
          this.selectedContact.set(null);
          this.showForm.set(false);
        }
        this.pendingDeleteId.set(null);
      },
      error: () => {
        this.pendingDeleteId.set(null);
        this.toast.show('Failed to delete contact.', 'error');
      },
    });
  }

  initials(contact: Contact): string {
    return (contact.first_name[0] ?? '') + (contact.last_name[0] ?? '');
  }

  fullName(contact: Contact): string {
    return `${contact.first_name} ${contact.last_name}`;
  }

  avatarColor(contact: Contact): string {
    const colors = AVATAR_COLORS;
    const name = contact.first_name + contact.last_name;
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
    }
    return colors[hash % colors.length];
  }
}
