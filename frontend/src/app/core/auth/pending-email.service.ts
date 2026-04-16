import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class PendingEmailService {
  private email = '';

  set(email: string): void {
    this.email = email;
  }

  consume(): string {
    const e = this.email;
    this.email = '';
    return e;
  }
}
