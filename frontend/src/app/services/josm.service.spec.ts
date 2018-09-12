import { TestBed, inject } from '@angular/core/testing';

import { JosmService } from './josm.service';
import {HttpClientTestingModule} from '../../../node_modules/@angular/common/http/testing';
import {HttpModule} from '@angular/http';

describe('JosmService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [JosmService],
      imports: [HttpModule, HttpClientTestingModule]
    });
  });

  it('should be created', inject([JosmService], (service: JosmService) => {
    expect(service).toBeTruthy();
  }));
});
