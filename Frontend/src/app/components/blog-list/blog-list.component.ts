import { CommonModule } from '@angular/common';
import { Component, HostListener, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { Blog } from '../../models/blog';
import { TruncateHtmlPipe } from '../../pipes/truncate-html.pipe';
import { AuthService } from '../../services/auth.service';
import { BlogService } from '../../services/blog.service';
import { ThemeService } from '../../services/theme.service';

@Component({
  selector: 'app-blog-list',
  imports: [CommonModule, RouterModule, FormsModule, TruncateHtmlPipe],
  templateUrl: './blog-list.component.html',
  styleUrl: './blog-list.component.css',
  standalone: true
})
export class BlogListComponent implements OnInit {
  blogs: Blog[] = [];
  searchTerm = '';
  user = localStorage.getItem('username') || '';
  darkMode = false;
  mobileMenuOpen = false;
  showScrollTop = false;
  blogToDelete?: Blog;

  // New properties for enhanced features
  viewMode: 'grid' | 'list' = 'grid';
  sortBy: string = 'newest';
  currentPage: number = 1;
  itemsPerPage: number = 3;
  totalPages: number = 1;

  constructor(
    private blogService: BlogService,
    public themeService: ThemeService,
    private auth: AuthService,
  ) { }

  ngOnInit() {
    this.loadBlogs();
  }

  loadBlogs() {
    this.blogService.getBlogs(this.searchTerm)
      .subscribe({
        next: (data) => {
          this.blogs = data;
          this.applySorting();
          this.calculatePagination();
        },
        error: (err) => console.error('Error fetching blogs', err)
      });
  }

  onSearch() {
    this.loadBlogs();
  }

  clearSearch() {
    this.searchTerm = '';
    this.onSearch();
  }

  onSortChange() {
    this.applySorting();
  }

  applySorting() {
    if (!this.blogs || this.blogs.length === 0) return;

    switch (this.sortBy) {
      case 'newest':
        // Sort by ID descending (assuming higher ID = newer)
        this.blogs.sort((a, b) => b.id - a.id);
        break;
      case 'oldest':
        // Sort by ID ascending
        this.blogs.sort((a, b) => a.id - b.id);
        break;
      case 'title':
        // Sort alphabetically A-Z
        this.blogs.sort((a, b) =>
          a.youtube_title.localeCompare(b.youtube_title)
        );
        break;
      case 'title-desc':
        // Sort alphabetically Z-A
        this.blogs.sort((a, b) =>
          b.youtube_title.localeCompare(a.youtube_title)
        );
        break;
    }
  }

  // Helper methods for stats and content analysis
  getWordCount(content: string): number {
    if (!content) return 0;
    const text = content.replace(/<[^>]*>/g, '');
    return text.trim().split(/\s+/).filter(word => word.length > 0).length;
  }

  getReadingTime(content: string): number {
    const words = this.getWordCount(content);
    return Math.ceil(words / 200); // 200 words per minute average reading speed
  }

  getTotalReadingTime(): number {
    if (!this.blogs || this.blogs.length === 0) return 0;
    return this.blogs.reduce((total, blog) => {
      return total + this.getReadingTime(blog.generated_content);
    }, 0);
  }

  // Pagination methods
  calculatePagination() {
    this.totalPages = Math.ceil(this.blogs.length / this.itemsPerPage);
    // Reset to page 1 if current page exceeds total pages
    if (this.currentPage > this.totalPages) {
      this.currentPage = 1;
    }
  }

  goToPage(page: number) {
    if (page < 1 || page > this.totalPages) return;
    this.currentPage = page;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  getPageNumbers(): number[] {
    const pages: number[] = [];
    const maxPagesToShow = 5;

    if (this.totalPages <= maxPagesToShow) {
      // Show all pages if total is less than max
      for (let i = 1; i <= this.totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Show pages around current page
      let startPage = Math.max(1, this.currentPage - 2);
      let endPage = Math.min(this.totalPages, this.currentPage + 2);

      if (this.currentPage <= 3) {
        endPage = maxPagesToShow;
      } else if (this.currentPage >= this.totalPages - 2) {
        startPage = this.totalPages - maxPagesToShow + 1;
      }

      for (let i = startPage; i <= endPage; i++) {
        pages.push(i);
      }
    }

    return pages;
  }

  getPaginatedBlogs(): Blog[] {
    const startIndex = (this.currentPage - 1) * this.itemsPerPage;
    const endIndex = startIndex + this.itemsPerPage;
    return this.blogs.slice(startIndex, endIndex);
  }

  // Existing methods
  toggleTheme() {
    this.themeService.toggleTheme();
  }

  @HostListener('window:scroll')
  onWindowScroll() {
    this.showScrollTop = window.pageYOffset > 100;
  }

  scrollToTop(event: Event) {
    event.preventDefault();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  openDeleteModal(blog: Blog) {
    this.blogToDelete = blog;
  }

  closeDeleteModal() {
    this.blogToDelete = undefined;
  }

  deleteBlog() {
    if (!this.blogToDelete) return;
    this.blogService.deleteBlog(this.blogToDelete.id).subscribe({
      next: () => {
        this.blogs = this.blogs.filter(b => b.id !== this.blogToDelete!.id);
        this.calculatePagination();
        // If current page is now empty, go to previous page
        if (this.getPaginatedBlogs().length === 0 && this.currentPage > 1) {
          this.currentPage--;
        }
        this.closeDeleteModal();
      },
      error: (err) => {
        console.error('Error deleting blog', err);
        this.closeDeleteModal();
      }
    });
  }

  logout() {
    this.auth.logout();
  }
}
