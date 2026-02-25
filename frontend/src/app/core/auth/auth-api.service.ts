import { Injectable, inject } from "@angular/core"; 
import { HttpClient } from "@angular/common/http";
import { Observable } from "rxjs";
import type { AuthUser } from "./auth.service";

type Loginrequest = {
    email: string;
    password: string;
};

@Injectable({providedIn: 'root'})
export class AuthApiService {
    private readonly http = inject(HttpClient);

      // Später ziehst du das in environment.ts, erstmal hart als Platzhalter
    private readonly baseUrl = 'http://localhost:8000';

    me(): Observable<AuthUser> {
        return this.http.get<AuthUser>(`${this.baseUrl}/auth/me`, {
            withCredentials: true,
        });
    }

    login(payload: Loginrequest): Observable<void> {
        return this.http.post<void>(`{this.baseUrl}/auth/login`, payload, {
            withCredentials: true,
        });
    }

    logout(): Observable<void> {
        return this.http.post<void>(`{this.baseUrl}/auth/logouz`, null, {
            withCredentials: true,
        });
    }
}