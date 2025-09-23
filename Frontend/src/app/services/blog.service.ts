import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Blog } from '../models/blog';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class BlogService {
  private readonly baseUrl = 'http://localhost:8000/api';
  constructor(private http: HttpClient) { }

  getBlogs(q: string) {
    let params = new HttpParams();
    if (q) {
      params = params.set('q', q);
    }
    return this.http.get<Blog[]>(`${this.baseUrl}/blogs`, { params });
  }

  deleteBlog(id: number) {
    return this.http.delete(`${this.baseUrl}/blogs/${id}`);
  }

  getBlogDetails(id: string | number): Observable<Blog> {
    return this.http.get<Blog>(`${this.baseUrl}/blogs/${id}/`);
  }
}
