import { Injectable, signal, inject } from "@angular/core";
import { catchError, finalize, of, tap} from "rxjs";
import { AuthApiService } from "./auth-api.service";

export type AuthUser = {
    id: string;
    email: string;
};

@Injectable({ providedIn: 'root'})
    export class AuthService {
        private readonly api = inject(AuthApiService);

        private readonly _authChecked = signal(false);
        authChecked = this._authChecked.asReadonly();

        private readonly _user = signal<AuthUser | null>(null);
        user = this._user.asReadonly();

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

        loginMock(): void {
            this._user.set({ id: 'u1', email:'sascha@example.com'});
        }

        logout(): void {
            this._user.set(null);
        }
    }