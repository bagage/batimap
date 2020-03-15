import { inject, TestBed } from '@angular/core/testing';

import { HttpClientTestingModule } from '@angular/common/http/testing';
import { AppConfigService } from './app-config.service';
import { MockAppConfigService } from './app-config.service.mock';
import { JosmService } from './josm.service';

describe('JosmService', () => {
    beforeEach(() => {
        TestBed.configureTestingModule({
            providers: [JosmService, { provide: AppConfigService, useClass: MockAppConfigService }],
            imports: [HttpClientTestingModule]
        });
    });

    it('should be created', inject([JosmService], (service: JosmService) => {
        expect(service).toBeTruthy();
    }));
});
