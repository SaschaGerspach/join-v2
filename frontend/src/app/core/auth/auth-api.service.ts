import { Injectable, inject } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable } from "rxjs";
import type { AuthUser } from "./auth.service";
import { environment } from "../../../environments/environment";

type LoginRequest = {
    email: string;
    password: string;
};

type RegisterRequest = {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
};

export type LoginResponse = AuthUser & { access: string };

@Injectable({providedIn: 'root'})
export class AuthApiService {
    private readonly http = inject(HttpClient);

    private readonly baseUrl = environment.apiUrl;

    register(payload: RegisterRequest): Observable<AuthUser> {
        return this.http.post<AuthUser>(`${this.baseUrl}/auth/register`, payload, {
            withCredentials: true,
        });
    }

    me(): Observable<AuthUser> {
        return this.http.get<AuthUser>(`${this.baseUrl}/auth/me`, {
            withCredentials: true,
        });
    }

    login(payload: LoginRequest): Observable<LoginResponse> {
        return this.http.post<LoginResponse>(`${this.baseUrl}/auth/login`, payload, {
            withCredentials: true,
        });
    }

    refreshToken(): Observable<{ access: string }> {
        return this.http.post<{ access: string }>(`${this.baseUrl}/auth/token/refresh`, null, {
            withCredentials: true,
        });
    }

    logout(): Observable<void> {
        return this.http.post<void>(`${this.baseUrl}/auth/logout`, null, {
            withCredentials: true,
        });
    }

    verifyEmail(uid: string, token: string): Observable<void> {
        return this.http.post<void>(`${this.baseUrl}/auth/verify-email`, { uid, token }, {
            withCredentials: true,
        });
    }

    resendVerification(email: string): Observable<void> {
        return this.http.post<void>(`${this.baseUrl}/auth/resend-verification`, { email }, {
            withCredentials: true,
        });
    }

    passwordResetRequest(email: string): Observable<void> {
        return this.http.post<void>(`${this.baseUrl}/auth/password-reset`, { email }, {
            withCredentials: true,
        });
    }

    passwordResetConfirm(uid: string, token: string, password: string): Observable<void> {
        return this.http.post<void>(`${this.baseUrl}/auth/password-reset/confirm`, { uid, token, password }, {
            withCredentials: true,
        });
    }
}
