import { TestBed } from '@angular/core/testing';

import { BlogGeneratorService } from './blog-generator.service';

describe('BlogGeneratorService', () => {
  let service: BlogGeneratorService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(BlogGeneratorService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
