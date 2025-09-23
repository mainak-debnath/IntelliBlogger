import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { ThemeService } from '../../services/theme.service';
import { BackButtonComponent } from '../../shared/back-button/back-button.component';
import { TiltDirective } from '../../shared/directives/tilt.directive';
import { AlertComponent } from '../alert/alert.component';


@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, AlertComponent, TiltDirective, BackButtonComponent, RouterModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  loginForm: FormGroup;
  passwordVisible = false;

  errorMessage: string | null = null;
  successMessage: string | null = null;

  constructor(private fb: FormBuilder,
    public themeService: ThemeService,
    private auth: AuthService,
    private router: Router
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
          });
        },
        error: err => this.errorMessage = 'Invalid credentials'
      });
    }
  }
}
