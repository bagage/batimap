import { TestBed, inject } from '@angular/core/testing';

import { BatimapService } from './batimap.service';
import {HttpClientTestingModule} from '../../../node_modules/@angular/common/http/testing';

describe('BatimapService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [BatimapService],
      imports: [HttpClientTestingModule]
    });
  });

  it('should be created', inject([BatimapService], (service: BatimapService) => {
    expect(service).toBeTruthy();
  }));
});
