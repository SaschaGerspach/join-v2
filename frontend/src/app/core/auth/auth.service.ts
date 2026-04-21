import { Injectable, signal, inject } from "@angular/core";
import { catchError, finalize, of, tap } from "rxjs";
import { AuthApiService } from "./auth-api.service";

export type AuthUser = {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
    is_staff: boolean;
    totp_enabled: boolean;
};

@Injectable({ providedIn: 'root'})
export class AuthService {
    private readonly api = inject(AuthApiService);

    private readonly _authChecked = signal(false);
    authChecked = this._authChecked.asReadonly();

    private readonly _user = signal<AuthUser | null>(null);
    user = this._user.asReadonly();

    private accessToken: string | null = null;

    init(): void {
        this._authChecked.set(false);

        this.api
            .me()
            .pipe(
                tap((u) => this._user.set(u)),
                catchError(() => {
                    this._user.set(null);
                    return of(null);
                }),
                finalize(() => this._authChecked.set(true))
            )
            .subscribe();
    }

    isLoggedIn(): boolean {
        return this._user() !== null;
    }

    login(email: string, password: string, totpCode?: string) {
        return this.api.login({ email, password, totp_code: totpCode }).pipe(
            tap((res) => {
                const { access, ...user } = res;
                this.accessToken = access;
                this._user.set(user as AuthUser);
            })
        );
    }

    clearUser(): void {
        this._user.set(null);
        this.accessToken = null;
    }

    logout(): void {
        this.api.logout().pipe(catchError(() => of(null))).subscribe();
        this._user.set(null);
        this.accessToken = null;
    }

    getAccessToken(): string | null {
        return this.accessToken;
    }

    setAccessToken(token: string | null): void {
        this.accessToken = token;
    }
}
