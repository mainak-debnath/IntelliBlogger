import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { ThemeService } from '../../services/theme.service';
import { ToastService } from '../../services/toast.service';
import { BackButtonComponent } from '../../shared/back-button/back-button.component';
import { TiltDirective } from '../../shared/directives/tilt.directive';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TiltDirective, BackButtonComponent, RouterModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  loginForm: FormGroup;
  passwordVisible = false;

  constructor(private fb: FormBuilder,
    public themeService: ThemeService,
    private auth: AuthService,
    private router: Router,
    private toastService: ToastService
  ) {
    this.loginForm = this.fb.group({
      username: ['', Validators.required],
      password: ['', Validators.required]
    });
  }

  togglePassword() {
    this.passwordVisible = !this.passwordVisible;
  }

  toggleTheme() {
    this.themeService.toggleTheme();
  }

  onSubmit() {
    if (this.loginForm.valid) {
      const { username, password } = this.loginForm.value;
      this.auth.login(username, password).subscribe({
        next: () => {
          this.auth.getCurrentUser().subscribe(res => {
            localStorage.setItem('username', res.username);
            this.router.navigate(['/generator']);
            this.toastService.success('Login successful', 'Welcome back!');
          });
        },
        error: err => {
          const errorMsg = err.error?.detail || 'Login failed. Please check your credentials and try again.';
          this.toastService.error('Login failed. Please check your credentials and try again.', errorMsg);
        }
      });
    }
  }
}
