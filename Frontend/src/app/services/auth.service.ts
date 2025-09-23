import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, Observable, of, tap } from 'rxjs';
import { SignupPayload } from '../models/signup-model';
import { TokenResponse } from '../models/token-response';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  private baseUrl = 'http://localhost:8000/api';

  constructor(private http: HttpClient, private router: Router) { }

  signup(data: SignupPayload): Observable<any> {
    return this.http.post<TokenResponse>(`${this.baseUrl}/signup/`, data)
      .pipe(tap(res => this.saveTokens(res)));;
  }

  login(username: string, password: string): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${this.baseUrl}/login/`, { username, password })
      .pipe(tap(tokens => this.saveTokens(tokens)));
  }

  refreshToken(): Observable<{ access: string }> {
    const refresh = localStorage.getItem('refresh');
    return this.http.post<{ access: string }>(`${this.baseUrl}/token/refresh/`, { refresh })
      .pipe(tap(res => localStorage.setItem('access', res.access)));
  }

  saveTokens(tokens: TokenResponse) {
    localStorage.setItem('access', tokens.access);
    localStorage.setItem('refresh', tokens.refresh);
    if (tokens.username) {
      localStorage.setItem('username', tokens.username);
    }
  }

  logout() {
    const refresh = localStorage.getItem('refresh');

    // call server to blacklist refresh token
    const req$ = refresh
      ? this.http
        .post(`${this.baseUrl}/logout/`, { refresh })
        .pipe(
          catchError(err => {
            // ignore API errors – still clear client
            console.error('Logout API failed', err);
            return of(null);
          })
        )
      : of(null);

    req$.subscribe(() => {
      localStorage.removeItem('access');
      localStorage.removeItem('refresh');
      localStorage.removeItem('username');
      this.router.navigate(['/login']);
    });
  }

  get accessToken() {
    return localStorage.getItem('access');
  }

  getCurrentUser(): Observable<{ username: string }> {
    return this.http.get<{ username: string }>(`${this.baseUrl}/me/`);
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access');
  }
}
