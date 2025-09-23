import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, Observable, throwError } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class BlogGeneratorService {

  private readonly baseUrl = 'http://localhost:8000/api';

  constructor(private http: HttpClient) { }

  generate(link: string): Observable<{ id: number; content: string; title: string }> {
    return this.http.post<{ id: number; content: string; title: string }>(
      `${this.baseUrl}/generate-blog/`,
      { link },
      {
        headers: { Authorization: `Bearer ${localStorage.getItem('access')}` }
      }
    ).pipe(
      catchError(err => {
        if (err.status === 429) {
          alert('Rate limit reached. Please wait before trying again.');
        }
        return throwError(() => err);
      })
    );
  }

}
