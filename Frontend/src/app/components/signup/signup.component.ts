import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { SignupPayload } from '../../models/signup-model';
import { AuthService } from '../../services/auth.service';
import { ThemeService } from '../../services/theme.service';
import { ToastService } from '../../services/toast.service';
import { BackButtonComponent } from '../../shared/back-button/back-button.component';

@Component({
  selector: 'app-signup',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, BackButtonComponent, RouterModule],
  templateUrl: './signup.component.html',
  styleUrls: ['./signup.component.css']
})
export class SignupComponent {
  signupForm: FormGroup;
  passwordVisible = false;
  repeatPasswordVisible = false;

  constructor(
    private fb: FormBuilder,
    public themeService: ThemeService,
    private auth: AuthService,
    private router: Router,
    private toastService: ToastService
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
        this.toastService.error('Passwords do not match');
        return;
      }

      this.auth.signup(payload).subscribe({
        next: res => {
          this.router.navigate(['/generator']);
          this.toastService.success('Account successfully created!');
        },
        error: err => {
          const errorMsg = err.error?.detail || 'Signup failed. Please try again.';
          this.toastService.error("Signup failed! Please try again.", errorMsg);
        }
      });
    }
  }
}
