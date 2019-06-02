import { inject, TestBed } from '@angular/core/testing';

import { HttpModule } from '@angular/http';
import { HttpClientTestingModule } from '../../../node_modules/@angular/common/http/testing';
import { AppConfigService } from './app-config.service';
import { MockAppConfigService } from './app-config.service.mock';
import { JosmService } from './josm.service';

describe('JosmService', () => {
    beforeEach(() => {
        TestBed.configureTestingModule({
            providers: [
                JosmService,
                { provide: AppConfigService, useClass: MockAppConfigService }
            ],
            imports: [HttpModule, HttpClientTestingModule]
        });
    });

    it('should be created', inject([JosmService], (service: JosmService) => {
        expect(service).toBeTruthy();
    }));
});
