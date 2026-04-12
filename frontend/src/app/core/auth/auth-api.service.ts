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

    login(payload: LoginRequest): Observable<AuthUser> {
        return this.http.post<AuthUser>(`${this.baseUrl}/auth/login`, payload, {
            withCredentials: true,
        });
    }

    logout(): Observable<void> {
        return this.http.post<void>(`${this.baseUrl}/auth/logout`, null, {
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
