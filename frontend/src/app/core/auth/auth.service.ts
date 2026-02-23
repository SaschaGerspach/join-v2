import { Injectable, signal } from "@angular/core";

export type AuthUser = {
    id: string;
    email: string;
};

@Injectable({ providedIn: 'root'})
    export class AuthService {
        private readonly _user = signal<AuthUser | null>(null);

        user = this._user.asReadonly();

        isLoggedIn(): boolean {
            return this._user() !== null;
        }

        init(): void {
            
        }

        loginMock(): void {
            this._user.set({ id: 'u1', email:'sascha@example.com'});
        }

        logout(): void {
            this._user.set(null);
        }
    }