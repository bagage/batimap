import { TestBed, inject } from '@angular/core/testing';

import { JosmService } from './josm.service';
import {HttpClientTestingModule} from '../../../node_modules/@angular/common/http/testing';
import {HttpModule} from '@angular/http';
import {AppConfigService} from 'src/app/services/app-config.service';

class MockAppConfigService {
  getConfig() {
    return {
      'backendServerUrl': 'http://localhost:5000/',
      'tilesServerUrl': 'http://localhost:9999/maps/batimap/{z}/{x}/{y}.vector.pbf'
    };
  }
}

describe('JosmService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [JosmService, {provide: AppConfigService, useClass: MockAppConfigService}],
      imports: [HttpModule, HttpClientTestingModule]
    });
  });

  it('should be created', inject([JosmService], (service: JosmService) => {
    expect(service).toBeTruthy();
  }));
});
