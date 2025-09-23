import { Routes } from '@angular/router';
import { AuthGuard } from './auth.guard';
import { BlogDetailsComponent } from './components/blog-details/blog-details.component';
import { BlogGeneratorComponent } from './components/blog-generator/blog-generator.component';
import { BlogListComponent } from './components/blog-list/blog-list.component';
import { HomeComponent } from './components/home/home.component';
import { LoginComponent } from './components/login/login.component';
import { SignupComponent } from './components/signup/signup.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'login', component: LoginComponent },
  { path: 'signup', component: SignupComponent },
  { path: 'generator', component: BlogGeneratorComponent, canActivate: [AuthGuard] },
  { path: 'blogDetails', component: BlogDetailsComponent, canActivate: [AuthGuard] },
  { path: 'blogLists', component: BlogListComponent, canActivate: [AuthGuard] },
  { path: 'blog/:id', component: BlogDetailsComponent, canActivate: [AuthGuard] },
  { path: '**', redirectTo: '' }
];