import { ChangeDetectionStrategy, Component, inject, signal, OnInit } from '@angular/core';
import { FormsModule, NgForm } from '@angular/forms';
import { RouterModule, ActivatedRoute, Router } from '@angular/router';
import { AuthApiService } from '../../../../core/auth/auth-api.service';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { LanguageService } from '../../../../shared/services/language.service';

@Component({
  selector: 'app-reset-password-page',
  standalone: true,
  imports: [FormsModule, RouterModule, TranslateModule],
  template: `
    <div class="auth-page">
      <div class="auth-logo"><span>Join</span></div>
      <div class="auth-card">
        <select class="auth-lang-select" [ngModel]="lang.currentLang()" (ngModelChange)="lang.setLanguage($event)">
          <option value="en">EN</option>
          <option value="de">DE</option>
        </select>
        <h1>{{ 'AUTH.SET_NEW_PASSWORD' | translate }}</h1>
        <div class="auth-divider"></div>

        @if (done()) {
          <p class="info-message">{{ 'AUTH.PASSWORD_UPDATED' | translate }}</p>
          <div class="auth-actions">
            <a routerLink="/login" class="btn-primary">{{ 'AUTH.GO_TO_LOGIN' | translate }}</a>
          </div>
        } @else {
          <form #f="ngForm" (ngSubmit)="submit(f)">
            <div class="form-group">
              <input
                class="form-input"
                type="password"
                [(ngModel)]="password"
                name="password"
                [placeholder]="'AUTH.NEW_PASSWORD' | translate"
                required
                minlength="8"
                #pwField="ngModel"
                [class.input-error]="pwField.invalid && (pwField.touched || f.submitted)"
              />
              @if (pwField.invalid && (pwField.touched || f.submitted)) {
                <span class="field-error">{{ 'AUTH.PASSWORD_MIN' | translate }}</span>
              }
            </div>
            <div class="form-group">
              <input
                class="form-input"
                type="password"
                [(ngModel)]="confirm"
                name="confirm"
                [placeholder]="'AUTH.CONFIRM_PASSWORD' | translate"
                required
                #confirmField="ngModel"
                [class.input-error]="confirmField.invalid && (confirmField.touched || f.submitted)"
              />
            </div>
            @if (error()) {
              <p class="error-message">{{ error() }}</p>
            }
            <div class="auth-actions">
              <button type="submit" class="btn-primary" [disabled]="submitting()">
                {{ submitting() ? ('AUTH.SAVING' | translate) : ('AUTH.SET_PASSWORD' | translate) }}
              </button>
            </div>
          </form>
        }
      </div>
    </div>
  `,
  styleUrls: ['../login-page/login-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ResetPasswordPageComponent implements OnInit {
  private readonly authApi = inject(AuthApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly translate = inject(TranslateService);
  readonly lang = inject(LanguageService);

  password = '';
  confirm = '';
  submitting = signal(false);
  done = signal(false);
  error = signal<string | null>(null);

  private uid = '';
  private token = '';

  ngOnInit(): void {
    this.uid = this.route.snapshot.paramMap.get('uid') ?? '';
    this.token = this.route.snapshot.paramMap.get('token') ?? '';
  }

  submit(form: NgForm): void {
    if (form.invalid) return;
    if (this.password !== this.confirm) {
      this.error.set(this.translate.instant('AUTH.PASSWORDS_NO_MATCH'));
      return;
    }
    this.error.set(null);
    this.submitting.set(true);
    this.authApi.passwordResetConfirm(this.uid, this.token, this.password).subscribe({
      next: () => { this.done.set(true); this.submitting.set(false); },
      error: (err) => {
        this.error.set(err?.error?.detail ?? this.translate.instant('AUTH.INVALID_LINK'));
        this.submitting.set(false);
      },
    });
  }
}
