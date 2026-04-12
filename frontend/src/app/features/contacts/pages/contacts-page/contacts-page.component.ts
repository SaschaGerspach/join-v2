import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Contact, ContactsApiService } from '../../../../core/contacts/contacts-api.service';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';

type ContactForm = {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
};

@Component({
  selector: 'app-contacts-page',
  standalone: true,
  imports: [FormsModule, LoadingSpinnerComponent, ConfirmDialogComponent],
  templateUrl: './contacts-page.component.html',
  styleUrl: './contacts-page.component.scss',
})
export class ContactsPageComponent implements OnInit {
  private readonly api = inject(ContactsApiService);

  contacts = signal<Contact[]>([]);
  selectedContact = signal<Contact | null>(null);
  showForm = signal(false);
  editMode = signal(false);
  loading = signal(true);
  error = signal('');
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
    this.api.getAll().subscribe({
      next: contacts => { this.contacts.set(contacts); this.loading.set(false); },
      error: () => { this.error.set('Failed to load contacts.'); this.loading.set(false); },
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
      this.api.patch(this.selectedContact()!.id, this.form).subscribe(updated => {
        this.contacts.update(c => c.map(x => x.id === updated.id ? updated : x));
        this.selectedContact.set(updated);
        this.showForm.set(false);
      });
    } else {
      this.api.create(this.form).subscribe(created => {
        this.contacts.update(c => [...c, created]);
        this.selectedContact.set(created);
        this.showForm.set(false);
      });
    }
  }

  deleteContact(id: number): void {
    this.pendingDeleteId.set(id);
  }

  confirmDeleteContact(): void {
    const id = this.pendingDeleteId();
    if (id === null) return;
    this.api.delete(id).subscribe(() => {
      this.contacts.update(c => c.filter(x => x.id !== id));
      if (this.selectedContact()?.id === id) {
        this.selectedContact.set(null);
        this.showForm.set(false);
      }
      this.pendingDeleteId.set(null);
    });
  }

  initials(contact: Contact): string {
    return (contact.first_name[0] ?? '') + (contact.last_name[0] ?? '');
  }

  fullName(contact: Contact): string {
    return `${contact.first_name} ${contact.last_name}`;
  }

  avatarColor(contact: Contact): string {
    const colors = [
      '#6e40c9', '#29abe2', '#e44a76', '#2d8a4e',
      '#d97c0e', '#4a90d9', '#c94040', '#3a7d44',
      '#8b4fc4', '#1a7f8f',
    ];
    const name = contact.first_name + contact.last_name;
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
    }
    return colors[hash % colors.length];
  }
}
