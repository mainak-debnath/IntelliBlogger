import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { SignupPayload } from '../../models/signup-model';
import { AuthService } from '../../services/auth.service';
import { ThemeService } from '../../services/theme.service';
import { BackButtonComponent } from '../../shared/back-button/back-button.component';
import { AlertComponent } from '../alert/alert.component';

@Component({
  selector: 'app-signup',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, AlertComponent, BackButtonComponent, RouterModule],
  templateUrl: './signup.component.html',
  styleUrls: ['./signup.component.css']
})
export class SignupComponent {
  signupForm: FormGroup;
  passwordVisible = false;
  repeatPasswordVisible = false;

  errorMessage: string | null = null;
  successMessage: string | null = null;

  constructor(
    private fb: FormBuilder,
    public themeService: ThemeService,
    private auth: AuthService,
    private router: Router
  ) {
    this.signupForm = this.fb.group({
      username: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required],
      repeat_password: ['', Validators.required]
    });
  }

  togglePassword(field: 'password' | 'repeatPassword') {
    if (field === 'password') {
      this.passwordVisible = !this.passwordVisible;
    } else {
      this.repeatPasswordVisible = !this.repeatPasswordVisible;
    }
  }

  toggleTheme() {
    this.themeService.toggleTheme();
  }

  onSubmit() {
    if (this.signupForm.valid) {
      const payload: SignupPayload = this.signupForm.value;

      if (payload.password !== payload.repeat_password) {
        this.errorMessage = 'Passwords do not match';
        this.successMessage = null;
        return;
      }

      this.auth.signup(payload).subscribe({
        next: res => {
          this.successMessage = 'Account created successfully!';
          this.errorMessage = null;
          this.router.navigate(['/generator'])
          //this.signupForm.reset();
        },
        error: err => {
          this.errorMessage = err.error?.error || 'Signup failed';
          this.successMessage = null;
        }
      });
    }
  }
}
