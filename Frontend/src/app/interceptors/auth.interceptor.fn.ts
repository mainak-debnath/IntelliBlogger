// src/app/services/auth.interceptor.fn.ts
import { HttpBackend, HttpClient, HttpErrorResponse, HttpEvent, HttpHandlerFn, HttpInterceptorFn, HttpRequest } from '@angular/common/http';
import { inject } from '@angular/core';
import { Observable, catchError, switchMap, throwError } from 'rxjs';

/**
 * Function-based interceptor that:
 *  - attaches access token (from localStorage)
 *  - on 401 attempts a refresh using HttpClient constructed with HttpBackend (bypasses interceptors)
 */
export const authInterceptorFn: HttpInterceptorFn = (req: HttpRequest<unknown>, next: HttpHandlerFn): Observable<HttpEvent<unknown>> => {
  // Attach access token from localStorage (avoid injecting AuthService here to prevent circular deps)
  const access = localStorage.getItem('access');
  const authReq = access ? req.clone({ setHeaders: { Authorization: `Bearer ${access}` } }) : req;

  // Create an HttpClient that bypasses the interceptor chain (so refresh call won't loop)
  const backend = inject(HttpBackend);
  const httpWithoutInterceptors = new HttpClient(backend);

  return next(authReq).pipe(
    catchError((err: HttpErrorResponse) => {
      // if 401 and we have a refresh token, try to refresh and retry the original request
      const refresh = localStorage.getItem('refresh');
      if (err.status === 401 && refresh) {
        return httpWithoutInterceptors.post<{ access: string }>(
          'http://127.0.0.1:8000/api/token/refresh/',
          { refresh }
        ).pipe(
          switchMap(res => {
            // Save new access token and retry original request with it
            localStorage.setItem('access', res.access);
            const newReq = req.clone({ setHeaders: { Authorization: `Bearer ${res.access}` } });
            return next(newReq);
          }),
          catchError(refreshErr => {
            // refresh failed -> clear tokens and forward error
            localStorage.removeItem('access');
            localStorage.removeItem('refresh');
            return throwError(() => refreshErr);
          })
        );
      }
      return throwError(() => err);
    })
  );
};
