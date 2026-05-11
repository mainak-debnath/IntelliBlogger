import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, Observable, throwError } from 'rxjs';
import { environment } from '../../environments/environment';
import { BlogGenerationJob } from '../models/blog-generation-job';
import { BlogResponse } from '../models/blog-response';
import { SaveBlogRequest } from '../models/save-blog-request';
import { SaveBlogResponse } from '../models/save-blog-response';

@Injectable({
  providedIn: 'root'
})
export class BlogGeneratorService {

  private readonly baseUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) { }

  createGenerationJob(link: string, tone: string, length: string): Observable<BlogGenerationJob> {
    return this.http.post<BlogGenerationJob>(
      `${this.baseUrl}/generation-jobs/`,
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

  processGenerationJob(jobId: number): Observable<BlogGenerationJob> {
    return this.http.post<BlogGenerationJob>(
      `${this.baseUrl}/generation-jobs/${jobId}/process/`,
      {},
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

  getGenerationJob(jobId: number): Observable<BlogGenerationJob> {
    return this.http.get<BlogGenerationJob>(
      `${this.baseUrl}/generation-jobs/${jobId}/`,
      {
        headers: { Authorization: `Bearer ${localStorage.getItem('access')}` }
      }
    );
  }

  listGenerationJobs(): Observable<BlogGenerationJob[]> {
    return this.http.get<BlogGenerationJob[]>(
      `${this.baseUrl}/generation-jobs/list/`,
      {
        headers: { Authorization: `Bearer ${localStorage.getItem('access')}` }
      }
    );
  }

  toBlogResponse(job: BlogGenerationJob): BlogResponse {
    return {
      id: job.id,
      title: job.title,
      content: job.generated_content,
      tone: job.tone,
      length: job.length
    };
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
