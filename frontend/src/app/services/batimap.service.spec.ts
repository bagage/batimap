import { TestBed, inject } from '@angular/core/testing';

import { BatimapService } from './batimap.service';
import {HttpClientTestingModule} from '../../../node_modules/@angular/common/http/testing';
import {AppConfigService} from './app-config.service';
import {MockAppConfigService} from './app-config.service.mock';

describe('BatimapService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        BatimapService,
        {provide: AppConfigService, useClass: MockAppConfigService}
      ],
      imports: [HttpClientTestingModule]
    });
  });

  it('should be created', inject([BatimapService], (service: BatimapService) => {
    expect(service).toBeTruthy();
  }));
});
