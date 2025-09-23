import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BlogGeneratorComponent } from './blog-generator.component';

describe('BlogGeneratorComponent', () => {
  let component: BlogGeneratorComponent;
  let fixture: ComponentFixture<BlogGeneratorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BlogGeneratorComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(BlogGeneratorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
