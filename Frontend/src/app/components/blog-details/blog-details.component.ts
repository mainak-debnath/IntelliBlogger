//import { Clipboard } from '@angular/cdk/clipboard';
import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { Blog } from '../../models/blog';
import { AuthService } from '../../services/auth.service';
import { BlogService } from '../../services/blog.service';
import { ThemeService } from '../../services/theme.service';

@Component({
  selector: 'app-blog-details',
  templateUrl: './blog-details.component.html',
  styleUrls: ['./blog-details.component.css'],
  imports: [RouterModule, CommonModule],
  standalone: true
})
export class BlogDetailsComponent implements OnInit {
  blog!: Blog | null;
  username = localStorage.getItem('username') || '';
  mobileMenuOpen = false;
  showFull = false;
  truncatedContent: string = '';
  remainingContent: string = '';

  constructor(
    private route: ActivatedRoute,
    private blogService: BlogService,
    public themeService: ThemeService,
    //private clipboard: Clipboard,
    private auth: AuthService
  ) { }

  ngOnInit(): void {
    this.getBlogDetails();

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
          next: (b) => {
            this.blog = b
            this.splitContent(this.blog.generated_content || '')
          },
          error: (err) => console.error('Error fetching blog details', err)
        });
    }
  }

  copyText() {
    const text = `${this.truncatedContent || ''} ${this.showFull ? this.remainingContent || '' : ''}`;
    //this.clipboard.copy(text);
  }

  scrollTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  toggleReadMore(): void {
    this.showFull = !this.showFull;
  }

  splitContent(content: string): void {
    const limit = 300;
    if (content.length > limit) {
      this.truncatedContent = content.slice(0, limit);
      this.remainingContent = content.slice(limit);
    } else {
      this.truncatedContent = content;
      this.remainingContent = '';
    }
  }
}
