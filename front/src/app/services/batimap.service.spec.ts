import { inject, TestBed } from '@angular/core/testing';

import { HttpClientTestingModule } from '@angular/common/http/testing';
import { AppConfigService } from './app-config.service';
import { MockAppConfigService } from './app-config.service.mock';
import { BatimapService } from './batimap.service';

describe('BatimapService', () => {
    beforeEach(() => {
        TestBed.configureTestingModule({
            providers: [BatimapService, { provide: AppConfigService, useClass: MockAppConfigService }],
            imports: [HttpClientTestingModule],
        });
    });

    it('should be created', inject([BatimapService], (service: BatimapService) => {
        expect(service).toBeTruthy();
    }));
});
