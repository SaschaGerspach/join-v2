import { Component, inject, signal, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Contact, ContactsApiService } from '../../../../core/contacts/contacts-api.service';

type ContactForm = {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
};

@Component({
  selector: 'app-contacts-page',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './contacts-page.component.html',
  styleUrl: './contacts-page.component.scss',
})
export class ContactsPageComponent implements OnInit {
  private readonly api = inject(ContactsApiService);

  contacts = signal<Contact[]>([]);
  selectedContact = signal<Contact | null>(null);
  showForm = signal(false);
  editMode = signal(false);

  form: ContactForm = { first_name: '', last_name: '', email: '', phone: '' };

  ngOnInit(): void {
    this.api.getAll().subscribe(contacts => this.contacts.set(contacts));
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
    this.api.delete(id).subscribe(() => {
      this.contacts.update(c => c.filter(x => x.id !== id));
      if (this.selectedContact()?.id === id) {
        this.selectedContact.set(null);
        this.showForm.set(false);
      }
    });
  }

  initials(contact: Contact): string {
    return (contact.first_name[0] ?? '') + (contact.last_name[0] ?? '');
  }

  fullName(contact: Contact): string {
    return `${contact.first_name} ${contact.last_name}`;
  }
}
