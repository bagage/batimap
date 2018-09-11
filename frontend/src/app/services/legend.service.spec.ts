import { TestBed, inject } from '@angular/core/testing';

import { LegendService } from './legend.service';

describe('LegendService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [LegendService]
    });
  });

  it('should be created', inject([LegendService], (service: LegendService) => {
    expect(service).toBeTruthy();
  }));
});
