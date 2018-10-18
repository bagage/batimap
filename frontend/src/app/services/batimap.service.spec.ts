import { TestBed, inject } from '@angular/core/testing';

import { BatimapService } from './batimap.service';
import {HttpClientTestingModule} from '../../../node_modules/@angular/common/http/testing';
import {AppConfigService} from 'src/app/services/app-config.service';

class MockAppConfigService {
  getConfig() {
    return {
      'backendServerUrl': 'http://localhost:5000/',
      'tilesServerUrl': 'http://localhost:9999/maps/batimap/{z}/{x}/{y}.vector.pbf'
    };
  }
}

describe('BatimapService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [BatimapService, {provide: AppConfigService, useClass: MockAppConfigService}],
      imports: [HttpClientTestingModule]
    });
  });

  it('should be created', inject([BatimapService], (service: BatimapService) => {
    expect(service).toBeTruthy();
  }));
});
