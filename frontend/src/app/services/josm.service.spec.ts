import { TestBed, inject } from '@angular/core/testing';

import { JosmService } from './josm.service';

describe('JosmService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [JosmService]
    });
  });

  it('should be created', inject([JosmService], (service: JosmService) => {
    expect(service).toBeTruthy();
  }));
});
