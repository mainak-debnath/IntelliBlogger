import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { BlogResponse } from '../../models/blog-response';
import { AuthService } from '../../services/auth.service';
import { BlogGeneratorService } from '../../services/blog-generator.service';
import { ThemeService } from '../../services/theme.service';
import { FooterComponent } from '../shared/footer/footer.component';

@Component({
  selector: 'BlogGeneratorComponent',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FooterComponent, RouterModule],
  templateUrl: './blog-generator.component.html',
  styleUrls: ['./blog-generator.component.css']
})
export class BlogGeneratorComponent {
  username = localStorage.getItem('username') || '';
  loading = false;
  blogContent: string | null = null;

  linkForm: FormGroup;

  constructor(
    private fb: FormBuilder,
    private blogGeneratorService: BlogGeneratorService,
    public themeService: ThemeService,
    private auth: AuthService,
    private router: Router
  ) {
    this.linkForm = this.fb.group({
      link: ['']
    });
  }

  toggleTheme() {
    this.themeService.toggleTheme();
  }

  logout() {
    this.auth.logout();
  }

  generateBlog() {
    if (this.linkForm.invalid) return;
    this.loading = true;
    this.blogGeneratorService.generate(this.linkForm.value.link!)
      .subscribe({
        next: (data: BlogResponse) => {
          this.blogContent = data.content;
          this.loading = false;
        },
        error: () => this.loading = false
      });
  }
}
