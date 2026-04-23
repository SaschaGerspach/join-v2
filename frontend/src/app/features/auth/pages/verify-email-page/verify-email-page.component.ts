import { ChangeDetectionStrategy, Component, inject, signal, OnInit } from '@angular/core';
import { RouterModule, ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthApiService } from '../../../../core/auth/auth-api.service';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { LanguageService } from '../../../../shared/services/language.service';

@Component({
  selector: 'app-verify-email-page',
  standalone: true,
  imports: [RouterModule, FormsModule, TranslateModule],
  template: `
    <div class="auth-page">
      <div class="auth-logo"><span>Join</span></div>
      <div class="auth-card">
        <select class="auth-lang-select" [ngModel]="lang.currentLang()" (ngModelChange)="lang.setLanguage($event)">
          <option value="en">EN</option>
          <option value="de">DE</option>
        </select>
        @if (loading()) {
          <p class="info-message">{{ 'AUTH.VERIFYING' | translate }}</p>
        } @else if (success()) {
          <h1>{{ 'AUTH.EMAIL_VERIFIED' | translate }}</h1>
          <div class="auth-divider"></div>
          <p class="info-message">{{ 'AUTH.ACCOUNT_ACTIVE' | translate }}</p>
          <div class="auth-actions">
            <a routerLink="/login" class="btn-primary">{{ 'AUTH.GO_TO_LOGIN' | translate }}</a>
          </div>
        } @else {
          <h1>{{ 'AUTH.VERIFICATION_FAILED' | translate }}</h1>
          <div class="auth-divider"></div>
          <p class="error-message">{{ error() }}</p>
          <div class="auth-actions">
            <a routerLink="/login" class="btn-secondary">{{ 'AUTH.BACK_TO_LOGIN' | translate }}</a>
          </div>
        }
      </div>
    </div>
  `,
  styleUrls: ['../login-page/login-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class VerifyEmailPageComponent implements OnInit {
  private readonly authApi = inject(AuthApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly translate = inject(TranslateService);
  readonly lang = inject(LanguageService);

  loading = signal(true);
  success = signal(false);
  error = signal('');

  ngOnInit(): void {
    const uid = this.route.snapshot.paramMap.get('uid') ?? '';
    const token = this.route.snapshot.paramMap.get('token') ?? '';
    this.authApi.verifyEmail(uid, token).subscribe({
      next: () => { this.success.set(true); this.loading.set(false); },
      error: (err) => { this.error.set(err?.error?.detail ?? this.translate.instant('AUTH.INVALID_LINK')); this.loading.set(false); },
    });
  }
}
