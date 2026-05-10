import { Injectable, NgZone } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { BlogGenerationJob } from '../models/blog-generation-job';

@Injectable({
  providedIn: 'root'
})
export class GenerationJobStreamService {
  private eventSource?: EventSource;
  private jobUpdatesSubject = new Subject<BlogGenerationJob>();
  readonly jobUpdates$: Observable<BlogGenerationJob> = this.jobUpdatesSubject.asObservable();

  constructor(private ngZone: NgZone) { }

  connect(token: string): void {
    if (!token) {
      return;
    }

    if (this.eventSource) {
      return;
    }

    const url = `http://localhost:8000/api/generation-jobs/stream/?token=${encodeURIComponent(token)}`;
    this.eventSource = new EventSource(url);

    this.eventSource.addEventListener('job_update', (event: MessageEvent) => {
      this.ngZone.run(() => {
        const job = JSON.parse(event.data) as BlogGenerationJob;
        this.jobUpdatesSubject.next(job);
      });
    });
  }

  disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = undefined;
    }
  }
}
