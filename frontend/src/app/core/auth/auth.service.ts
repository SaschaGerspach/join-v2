import { Injectable, signal, inject } from "@angular/core";
import { Observable, catchError, finalize, map, of, shareReplay, take, tap, throwError } from "rxjs";
import { AuthApiService } from "./auth-api.service";

export type AuthUser = {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
    is_staff: boolean;
    totp_enabled: boolean;
    avatar_url: string | null;
};

@Injectable({ providedIn: 'root'})
export class AuthService {
    private readonly api = inject(AuthApiService);

    private readonly _authChecked = signal(false);
    authChecked = this._authChecked.asReadonly();

    private readonly _user = signal<AuthUser | null>(null);
    user = this._user.asReadonly();

    private accessToken: string | null = null;
    private refresh$: Observable<string> | null = null;

    init(): void {
        this._authChecked.set(false);

        this.api
            .me()
            .pipe(
                take(1),
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

    // Single refresh path for every caller (HTTP interceptor and WebSocket
    // reconnect): concurrent callers share the in-flight request.
    refreshAccessToken(): Observable<string> {
        if (!this.refresh$) {
            this.refresh$ = this.api.refreshToken().pipe(
                map((res) => res.access),
                tap((access) => this.setAccessToken(access)),
                catchError((err) => {
                    this.clearUser();
                    return throwError(() => err);
                }),
                shareReplay(1),
            );
            this.refresh$.subscribe({
                complete: () => (this.refresh$ = null),
                error: () => (this.refresh$ = null),
            });
        }
        return this.refresh$;
    }

    // The access token only lives 5 minutes, so treat it as due for renewal a
    // little early rather than letting a reconnect race the expiry.
    isAccessTokenExpiring(skewSeconds = 30): boolean {
        const exp = this.accessTokenExp();
        if (exp === null) return true;
        return exp - Date.now() / 1000 <= skewSeconds;
    }

    private accessTokenExp(): number | null {
        const payload = this.accessToken?.split('.')[1];
        if (!payload) return null;
        try {
            const decoded: unknown = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
            const exp = (decoded as Record<string, unknown>)?.['exp'];
            return typeof exp === 'number' ? exp : null;
        } catch {
            return null;
        }
    }
}
