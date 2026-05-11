import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { Subscription, finalize, switchMap, take, tap } from 'rxjs';
import { BlogGenerationJob } from '../../models/blog-generation-job';
import { BlogResponse } from '../../models/blog-response';
import { SaveBlogResponse } from '../../models/save-blog-response';
import { AuthService } from '../../services/auth.service';
import { BlogGeneratorService } from '../../services/blog-generator.service';
import { GenerationJobStreamService } from '../../services/generation-job-stream.service';
import { ThemeService } from '../../services/theme.service';
import { ToastService } from '../../services/toast.service';

@Component({
  selector: 'BlogGeneratorComponent',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './blog-generator.component.html',
  styleUrls: ['./blog-generator.component.css']
})
export class BlogGeneratorComponent implements OnInit, OnDestroy {
  private readonly activeJobsStorageKey = 'intelliblogger_active_generation_job_ids';
  username = localStorage.getItem('username') || '';
  loading = false;
  loadingMessage = 'Analyzing video and generating your blog post...';
  blogResponse: BlogResponse | null = null;
  generationJobs: BlogGenerationJob[] = [];
  activeJobId: number | null = null;
  linkForm: FormGroup;
  showAdvanced = false;
  showUpdateConfirmModal = false;
  existingBlogId: number | null = null;
  isMobileMenuOpen = false;
  private streamSubscription?: Subscription;

  constructor(
    private fb: FormBuilder,
    private blogGeneratorService: BlogGeneratorService,
    public themeService: ThemeService,
    private auth: AuthService,
    private router: Router,
    private toastService: ToastService,
    private generationJobStreamService: GenerationJobStreamService
  ) {
    this.linkForm = this.fb.group({
      link: ['', [Validators.required, Validators.pattern(/^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+$/)]],
      tone: ['professional'],
      length: ['medium']
    });
  }

  ngOnInit(): void {
    this.loadGenerationJobs();
    this.startJobStream();
  }

  ngOnDestroy(): void {
    this.streamSubscription?.unsubscribe();
    this.generationJobStreamService.disconnect();
  }

  get isAuthenticated(): boolean {
    return this.auth.isAuthenticated();
  }

  get activeJobs(): BlogGenerationJob[] {
    return this.generationJobs.filter(job => this.isActiveStatus(job.status));
  }

  get recentCompletedJobs(): BlogGenerationJob[] {
    return this.generationJobs.filter(job => job.status === 'completed').slice(0, 5);
  }

  toggleTheme() {
    this.themeService.toggleTheme();
  }

  toggleMobileMenu(): void {
    this.isMobileMenuOpen = !this.isMobileMenuOpen;
  }

  closeMobileMenu(): void {
    this.isMobileMenuOpen = false;
  }

  logout() {
    this.auth.logout();
  }

  generateBlog() {
    if (this.linkForm.invalid) {
      this.linkForm.markAllAsTouched();
      return;
    }
    this.loading = true;
    this.loadingMessage = 'Queueing your blog generation job...';
    this.blogResponse = null;

    const { link, tone, length } = this.linkForm.value;

    this.blogGeneratorService.createGenerationJob(link!, tone, length)
      .pipe(
        take(1),
        tap((job) => {
          this.upsertJob(job);
          this.trackJob(job.id);
          this.setActiveJob(job.id);

          if (this.isProcessableStatus(job.status)) {
            this.loadingMessage = 'Processing the video and generating your article...';
          } else if (job.status === 'processing') {
            this.loadingMessage = 'Resuming your existing generation job...';
          } else if (job.status === 'completed') {
            this.loadingMessage = 'Loading your generated article...';
          }
        }),
        switchMap((job) => {
          if (job.status === 'completed') {
            return this.blogGeneratorService.getGenerationJob(job.id);
          }

          if (this.isProcessableStatus(job.status)) {
            return this.blogGeneratorService.processGenerationJob(job.id);
          }

          return this.blogGeneratorService.getGenerationJob(job.id);
        }),
        finalize(() => {
          this.loading = false;
        })
      )
      .subscribe({
        next: (job) => {
          this.handleJobUpdate(job, true);
        },
        error: (err) => {
          console.error("Error generating blog:", err);
          const errorMessage = err.error?.detail || 'Failed to generate blog. Please try again.';
          this.toastService.error('Generation Failed', errorMessage);
        }
      });
  }

  getSanitizedContent(): string {
    return this.blogResponse?.content || '';
  }

  startOver() {
    this.blogResponse = null;
    this.activeJobId = null;
    this.loadingMessage = 'Analyzing video and generating your blog post...';
    this.linkForm.reset({
      link: '',
      tone: 'professional',
      length: 'medium'
    });
  }

  saveBlog(forceUpdate: boolean = false): void {
    if (!this.blogResponse) {
      this.toastService.error('Error', 'No blog to save');
      return;
    }
    const payload = {
      title: this.blogResponse.title,
      content: this.blogResponse.content,
      link: this.linkForm.get('link')?.value,
      tone: this.linkForm.get('tone')?.value,
      length: this.linkForm.get('length')?.value,
      force_update: forceUpdate
    };

    this.blogGeneratorService.saveBlog(payload).subscribe({
      next: (response: SaveBlogResponse) => {
        switch (response.status) {
          case 'created':
          case 'updated':
            this.blogResponse!.id = response.id;
            this.toastService.success(response.status === 'created' ? 'Saved!' : 'Updated!', response.message);
            break;

          case 'exists':
            // Instead of confirm(), show the custom modal
            this.existingBlogId = response.id;
            this.showUpdateConfirmModal = true;
            break;
        }
      },
      error: (error) => {
        const errorMessage = error.error?.detail || 'Failed to save blog';
        this.toastService.error('Save Failed', errorMessage);
      }
    });
  }

  confirmUpdate(): void {
    this.saveBlog(true);
    this.showUpdateConfirmModal = false;
  }

  closeConfirmModal(): void {
    this.showUpdateConfirmModal = false;
    this.existingBlogId = null;
    this.toastService.info('Save Canceled', 'The existing blog was not modified.');
  }

  copyContent(): void {
    if (!this.blogResponse?.content) {
      this.toastService.error('Error', 'No content to copy');
      return;
    }

    const plainText = this.stripHtml(this.blogResponse.content);

    navigator.clipboard.writeText(plainText).then(() => {
      this.toastService.success('Copied!', 'Blog content copied to clipboard');
    }).catch(err => {
      console.error('Failed to copy text:', err);
      this.toastService.error('Copy Failed', 'Could not copy to clipboard');
    });
  }

  openJob(job: BlogGenerationJob): void {
    this.setActiveJob(job.id);
    this.handleJobUpdate(job, false);
  }

  resumeJob(job: BlogGenerationJob): void {
    this.loading = true;
    this.loadingMessage = job.status === 'failed'
      ? 'Retrying your generation job...'
      : 'Resuming your generation job...';
    this.setActiveJob(job.id);

    this.blogGeneratorService.processGenerationJob(job.id)
      .pipe(
        take(1),
        finalize(() => {
          this.loading = false;
        })
      )
      .subscribe({
        next: (updatedJob) => {
          this.handleJobUpdate(updatedJob, true);
        },
        error: (err) => {
          const errorMessage = err.error?.detail || 'Failed to resume blog generation. Please try again.';
          this.toastService.error('Generation Failed', errorMessage);
        }
      });
  }

  trackByJobId(_: number, job: BlogGenerationJob): number {
    return job.id;
  }

  private loadGenerationJobs(): void {
    this.blogGeneratorService.listGenerationJobs()
      .pipe(take(1))
      .subscribe({
        next: (jobs) => {
          this.generationJobs = jobs;
          this.restoreTrackedJobs();
          this.resumeTrackedJobsIfNeeded();
          this.restoreActiveJobResult();
        },
        error: (err) => {
          console.error('Error loading generation jobs', err);
        }
      });
  }

  private startJobStream(): void {
    const token = this.auth.accessToken;
    if (!token) {
      return;
    }

    this.generationJobStreamService.connect(token);
    this.streamSubscription = this.generationJobStreamService.jobUpdates$.subscribe({
      next: (job) => {
        this.handleJobUpdate(job, job.status === 'completed' || job.status === 'failed');
        this.restoreTrackedJobs();
        this.restoreActiveJobResult();
      },
      error: (err) => {
        console.error('Error streaming generation jobs', err);
      }
    });
  }

  private restoreActiveJobResult(): void {
    const activeJob = this.getCurrentActiveJob();
    if (!activeJob) {
      return;
    }

    if (activeJob.status === 'completed') {
      this.blogResponse = this.blogGeneratorService.toBlogResponse(activeJob);
      this.untrackJob(activeJob.id);
    } else if (activeJob.status === 'failed') {
      this.untrackJob(activeJob.id);
    }
  }

  private resumeTrackedJobsIfNeeded(): void {
    const trackedJobIds = this.getTrackedJobIds();
    trackedJobIds.forEach((jobId) => {
      const job = this.generationJobs.find(item => item.id === jobId);
      if (job && job.status === 'queued') {
        this.resumeJob(job);
      }
    });
  }

  private handleJobUpdate(job: BlogGenerationJob, notify: boolean): void {
    this.upsertJob(job);
    this.restoreFormFromJob(job);

    if (job.status === 'failed') {
      this.untrackJob(job.id);
      if (notify) {
        this.toastService.error('Generation Failed', job.error_message || 'Failed to generate blog. Please try again.');
      }
      return;
    }

    if (job.status === 'completed') {
      this.blogResponse = this.blogGeneratorService.toBlogResponse(job);
      this.untrackJob(job.id);
      if (notify) {
        this.toastService.success('Success!', 'Blog post generated successfully');
      }
      return;
    }

    this.trackJob(job.id);
    if (notify && job.status === 'processing') {
      this.toastService.info('Generation in progress', 'Your blog job is processing. You can leave this page and come back later.');
    }
  }

  private upsertJob(job: BlogGenerationJob): void {
    const index = this.generationJobs.findIndex(existingJob => existingJob.id === job.id);
    if (index >= 0) {
      this.generationJobs[index] = job;
      this.generationJobs = [...this.generationJobs];
      return;
    }

    this.generationJobs = [job, ...this.generationJobs];
  }

  private setActiveJob(jobId: number): void {
    this.activeJobId = jobId;
  }

  private restoreFormFromJob(job: BlogGenerationJob): void {
    this.linkForm.patchValue({
      link: job.youtube_link,
      tone: job.tone,
      length: job.length
    }, { emitEvent: false });
  }

  private getCurrentActiveJob(): BlogGenerationJob | undefined {
    return this.generationJobs.find(job => job.id === this.activeJobId);
  }

  private isActiveStatus(status: BlogGenerationJob['status']): boolean {
    return status === 'queued' || status === 'processing';
  }

  private isProcessableStatus(status: BlogGenerationJob['status']): boolean {
    return status === 'queued' || status === 'failed';
  }

  private getTrackedJobIds(): number[] {
    const raw = localStorage.getItem(this.activeJobsStorageKey);
    if (!raw) {
      return [];
    }

    try {
      return JSON.parse(raw) as number[];
    } catch {
      return [];
    }
  }

  private persistTrackedJobs(jobIds: number[]): void {
    localStorage.setItem(this.activeJobsStorageKey, JSON.stringify(jobIds));
  }

  private trackJob(jobId: number): void {
    const trackedJobIds = this.getTrackedJobIds();
    if (!trackedJobIds.includes(jobId)) {
      this.persistTrackedJobs([...trackedJobIds, jobId]);
    }
  }

  private untrackJob(jobId: number): void {
    const trackedJobIds = this.getTrackedJobIds().filter(id => id !== jobId);
    this.persistTrackedJobs(trackedJobIds);
  }

  private restoreTrackedJobs(): void {
    const trackedJobs = this.getTrackedJobIds().filter((jobId) =>
      this.generationJobs.some(job => job.id === jobId && this.isActiveStatus(job.status))
    );
    this.persistTrackedJobs(trackedJobs);
  }

  private stripHtml(html: string): string {
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
  }
}
