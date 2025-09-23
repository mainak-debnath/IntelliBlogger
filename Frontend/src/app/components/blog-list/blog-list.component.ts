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

  constructor(private blogService: BlogService,
    public themeService: ThemeService,
    private auth: AuthService,
  ) { }

  ngOnInit() {
    this.loadBlogs();
  }

  loadBlogs() {
    this.blogService.getBlogs(this.searchTerm)
      .subscribe({
        next: (data) => this.blogs = data,
        error: (err) => console.error('Error fetching blogs', err)
      });
  }

  onSearch() {
    this.loadBlogs();
  }

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
    this.blogService.deleteBlog(this.blogToDelete.id).subscribe(() => {
      this.blogs = this.blogs.filter(b => b.id !== this.blogToDelete!.id);
      this.closeDeleteModal();
    });
  }

  logout() {
    this.auth.logout();
  }
}
