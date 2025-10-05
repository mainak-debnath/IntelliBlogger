import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, Observable, throwError } from 'rxjs';
import { BlogResponse } from '../models/blog-response';
import { SaveBlogRequest } from '../models/save-blog-request';
import { SaveBlogResponse } from '../models/save-blog-response';

@Injectable({
  providedIn: 'root'
})
export class BlogGeneratorService {

  private readonly baseUrl = 'http://localhost:8000/api';

  constructor(private http: HttpClient) { }

  generate(link: string, tone: string, length: string): Observable<BlogResponse> {
    return this.http.post<BlogResponse>(
      `${this.baseUrl}/generate-blog/`,
      { link, tone, length },
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

  saveBlog(request: SaveBlogRequest): Observable<SaveBlogResponse> {
    return this.http.post<SaveBlogResponse>(
      `${this.baseUrl}/save-blog/`,
      request,
      {
        headers: { Authorization: `Bearer ${localStorage.getItem('access')}` }
      }
    );
  }

}
