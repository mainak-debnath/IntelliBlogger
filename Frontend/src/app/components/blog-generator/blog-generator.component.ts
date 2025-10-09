import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { Router, RouterModule } from '@angular/router';
import { take } from 'rxjs';
import { BlogResponse } from '../../models/blog-response';
import { SaveBlogResponse } from '../../models/save-blog-response';
import { AuthService } from '../../services/auth.service';
import { BlogGeneratorService } from '../../services/blog-generator.service';
import { ThemeService } from '../../services/theme.service';
import { ToastService } from '../../services/toast.service';

@Component({
  selector: 'BlogGeneratorComponent',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './blog-generator.component.html',
  styleUrls: ['./blog-generator.component.css']
})
export class BlogGeneratorComponent {
  username = localStorage.getItem('username') || '';
  loading = false;
  blogResponse: BlogResponse | null = null;
  linkForm: FormGroup;
  showAdvanced = false;
  showUpdateConfirmModal = false;
  existingBlogId: number | null = null;
  isMobileMenuOpen = false;

  constructor(
    private fb: FormBuilder,
    private blogGeneratorService: BlogGeneratorService,
    public themeService: ThemeService,
    private auth: AuthService,
    private router: Router,
    private sanitizer: DomSanitizer,
    private toastService: ToastService
  ) {
    this.linkForm = this.fb.group({
      link: ['', [Validators.required, Validators.pattern(/^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+$/)]],
      tone: ['professional'],
      length: ['medium']
    });
  }

  get isAuthenticated(): boolean {
    return this.auth.isAuthenticated();
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
    this.blogResponse = null;

    const { link, tone, length } = this.linkForm.value;

    // Note: You may need to update your service to accept tone and length
    this.blogGeneratorService.generate(link!, tone, length)
      .pipe(take(1))
      .subscribe({
        next: (data) => {
          this.blogResponse = data;
          this.loading = false;
          this.toastService.success('Success!', 'Blog post generated successfully');
        },
        error: (err) => {
          console.error("Error generating blog:", err);
          this.loading = false;
          const errorMessage = err.error?.detail || 'Failed to generate blog. Please try again.';
          this.toastService.error('Generation Failed', errorMessage);
        }
      });
  }

  getSanitizedContent(): SafeHtml {
    return this.sanitizer.bypassSecurityTrustHtml(this.blogResponse?.content || '');
  }

  startOver() {
    this.blogResponse = null;
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

  private stripHtml(html: string): string {
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
  }
}