import { TestBed, inject } from '@angular/core/testing';

import { BatimapService } from './batimap.service';

describe('BatimapService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [BatimapService]
    });
  });

  it('should be created', inject([BatimapService], (service: BatimapService) => {
    expect(service).toBeTruthy();
  }));
});
