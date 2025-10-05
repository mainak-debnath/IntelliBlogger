import { CommonModule } from '@angular/common';
import { Component, HostListener, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { QuillModule } from 'ngx-quill';
import { Blog } from '../../models/blog';
import { BlogExportData } from '../../models/blog-export-data';
import { BlogUpdateRequest } from '../../models/blog-update-request';
import { NotificationMessage } from '../../models/notification-message';
import { AuthService } from '../../services/auth.service';
import { BlogService } from '../../services/blog.service';
import { ThemeService } from '../../services/theme.service';
import { ToastService } from '../../services/toast.service';
import { QuillConfiguration } from './quill-configuration';

@Component({
  selector: 'app-blog-details',
  templateUrl: './blog-details.component.html',
  styleUrls: ['./blog-details.component.css'],
  imports: [RouterModule, CommonModule, FormsModule, QuillModule],
  standalone: true
})
export class BlogDetailsComponent implements OnInit {
  blog!: Blog | null;
  username = localStorage.getItem('username') || '';
  mobileMenuOpen = false;
  editableTitle: string = '';
  editableContent: string = '';
  isEditMode: boolean = false;
  isEditingTitle: boolean = false;
  showShareDropdown: boolean = false;
  showDownloadDropdown: boolean = false;
  showAdvancedOptions: boolean = false;

  // Advanced options
  authorName: string = '';
  publishDate: string = '';
  tags: string = '';
  hasUnsavedChanges = false;

  // Notification system
  notification: NotificationMessage = {
    type: 'info',
    message: '',
    show: false
  };

  quillModules = QuillConfiguration;

  private clickOutsideHandler = this.handleClickOutside.bind(this);

  constructor(
    private route: ActivatedRoute,
    private blogService: BlogService,
    public themeService: ThemeService,
    private auth: AuthService,
    private sanitizer: DomSanitizer,
    private toastService: ToastService
  ) { }

  ngOnInit(): void {
    this.getBlogDetails();
    this.publishDate = new Date().toISOString().split('T')[0];
    //document.addEventListener('click', this.clickOutsideHandler);
  }

  // ngOnDestroy() {
  //   document.removeEventListener('click', this.clickOutsideHandler);
  // }


  onContentChanged(event: any) {
    this.hasUnsavedChanges = true;
    this.editableContent = event.html; // Keep HTML content
    //this.autoSave();
  }

  toggleTheme() {
    this.themeService.toggleTheme();
  }

  logout() {
    this.auth.logout();
  }

  getBlogDetails() {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.blogService.getBlogDetails(id)
        .subscribe({
          next: (blog) => {
            this.blog = blog;
            // Initialize editable content AFTER blog is loaded
            this.editableTitle = this.blog?.youtube_title || '';
            this.editableContent = this.blog?.generated_content || '';
          },
          error: (err) => console.error('Error fetching blog details', err)
        });
    }
  }

  // Editor methods
  toggleEditMode() {
    this.isEditMode = !this.isEditMode;
    this.closeAllDropdowns();

    if (this.isEditMode) {
      this.showNotification('info', 'Edit mode activated');
    } else {
      this.showNotification('success', 'Changes saved in preview');
    }
  }

  getSafeHtml(content: string): SafeHtml {
    return this.sanitizer.bypassSecurityTrustHtml(content);
  }

  // Statistics methods
  getWordCount(): number {
    const text = this.stripHtml(this.editableContent);
    return text.trim().split(/\s+/).filter(word => word.length > 0).length;
  }

  getCharCount(): number {
    return this.stripHtml(this.editableContent).length;
  }

  getReadingTime(): number {
    const wordsPerMinute = 200;
    const wordCount = this.getWordCount();
    return Math.ceil(wordCount / wordsPerMinute);
  }

  // Export data helper
  private getBlogExportData(): BlogExportData {
    return {
      title: this.editableTitle || 'Untitled Blog',
      content: this.editableContent,
      sourceUrl: this.blog?.youtube_link,
      author: this.authorName || this.username,
      publishDate: this.publishDate ? new Date(this.publishDate) : new Date()
    };
  }

  // Copy functionality
  async copyText() {
    try {
      const success = await this.blogService.copyToClipboard(this.getBlogExportData());
      if (success) {
        this.showNotification('success', 'Content copied to clipboard!');
      } else {
        this.showNotification('error', 'Failed to copy content');
      }
    } catch (error) {
      this.showNotification('error', 'Failed to copy content');
    }
  }

  // Download methods
  toggleDownloadDropdown() {
    this.showDownloadDropdown = !this.showDownloadDropdown;
    this.showShareDropdown = false;
  }

  downloadPDF() {
    this.blogService.generateAdvancedPDF(this.getBlogExportData());
    this.showDownloadDropdown = false;
    this.showNotification('success', 'PDF download started!');
  }

  downloadHTML() {
    this.blogService.downloadAsHTML(this.getBlogExportData());
    this.showDownloadDropdown = false;
    this.showNotification('success', 'HTML file downloaded!');
  }

  downloadMarkdown() {
    this.blogService.downloadAsMarkdown(this.getBlogExportData());
    this.showDownloadDropdown = false;
    this.showNotification('success', 'Markdown file downloaded!');
  }

  // Share methods (uncommented and fixed)
  toggleShareDropdown() {
    this.showShareDropdown = !this.showShareDropdown;
    this.showDownloadDropdown = false;
  }

  shareToLinkedIn() {
    this.blogService.shareToLinkedIn(this.getBlogExportData(), window.location.href);
    this.showShareDropdown = false;
    this.showNotification('info', 'Opening LinkedIn share dialog...');
  }

  shareToTwitter() {
    this.blogService.shareToTwitter(this.getBlogExportData(), window.location.href);
    this.showShareDropdown = false;
    this.showNotification('info', 'Opening Twitter share dialog...');
  }

  shareViaEmail() {
    this.blogService.shareViaEmail(this.getBlogExportData());
    this.showShareDropdown = false;
    this.showNotification('info', 'Opening email client...');
  }

  // Additional sharing methods
  shareToWhatsApp() {
    this.blogService.shareToWhatsApp(this.getBlogExportData(), window.location.href);
    this.showShareDropdown = false;
    this.showNotification('info', 'Opening WhatsApp...');
  }

  shareToFacebook() {
    this.blogService.shareToFacebook(window.location.href);
    this.showShareDropdown = false;
    this.showNotification('info', 'Opening Facebook...');
  }

  async copyLink() {
    const success = await this.blogService.copyLink(window.location.href);
    if (success) {
      this.showNotification('success', 'Link copied to clipboard!');
    } else {
      this.showNotification('error', 'Failed to copy link');
    }
    this.showShareDropdown = false;
  }

  // private autoSaveTimeout: any;
  // private autoSave() {
  //   clearTimeout(this.autoSaveTimeout);
  //   this.autoSaveTimeout = setTimeout(() => {
  //     this.saveBlogData();
  //   }, 2000); // Auto-save after 2 seconds of inactivity
  // }

  public async saveBlogData() {
    try {
      if (!this.blog?.id) return;

      const updatedData: BlogUpdateRequest = {
        youtube_title: this.editableTitle,
        generated_content: this.editableContent
      };

      await this.blogService.updateBlog(this.blog.id, updatedData).toPromise();
      this.hasUnsavedChanges = false;
      this.toastService.success('Your changes have been saved successfully.');
    } catch (error) {
      this.toastService.error('Save Failed', 'Could not save your changes.');
    }
  }

  // Manual save method
  async saveBlog() {
    try {
      await this.saveBlogData();
      this.showNotification('success', 'Blog saved successfully!');
    } catch (error) {
      this.showNotification('error', 'Failed to save blog');
    }
  }

  // Utility methods
  closeAllDropdowns() {
    this.showShareDropdown = false;
    this.showDownloadDropdown = false;
  }

  private handleClickOutside(event: Event) {
    const target = event.target as HTMLElement;
    if (!target.closest('.action-dropdown')) {
      this.closeAllDropdowns();
    }
  }

  private showNotification(type: 'success' | 'error' | 'info', message: string) {
    this.notification = { type, message, show: true };
    setTimeout(() => {
      this.notification.show = false;
    }, 3000);
  }

  private stripHtml(html: string): string {
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
  }

  // Keyboard shortcuts
  @HostListener('document:keydown', ['$event'])
  handleKeyDown(event: KeyboardEvent) {
    if (!this.isEditMode) return;

    // Ctrl/Cmd + S for save
    if ((event.ctrlKey || event.metaKey) && event.key === 's') {
      event.preventDefault();
      this.saveBlog();
    }

    // Ctrl/Cmd + P for preview toggle
    if ((event.ctrlKey || event.metaKey) && event.key === 'p') {
      event.preventDefault();
      this.toggleEditMode();
    }
  }

  // Check if native sharing is supported (for mobile devices)
  isNativeShareSupported(): boolean {
    return 'share' in navigator;
  }

  // Native share method (for mobile)
  async shareNative() {
    const blogData = this.getBlogExportData();

    if (navigator.share) {
      try {
        await navigator.share({
          title: blogData.title,
          text: this.stripHtml(blogData.content).substring(0, 200) + '...',
          url: window.location.href,
        });
        this.showNotification('success', 'Shared successfully!');
      } catch (error) {
        console.log('Error sharing:', error);
        // Fallback to copy link
        this.copyLink();
      }
    } else {
      // Fallback for browsers that don't support native sharing
      this.copyLink();
    }
    this.showShareDropdown = false;
  }
}
