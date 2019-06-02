import { inject, TestBed } from '@angular/core/testing';

import { HttpClientTestingModule } from '../../../node_modules/@angular/common/http/testing';
import { AppConfigService } from './app-config.service';

describe('AppConfigService', () => {
    beforeEach(() => {
        TestBed.configureTestingModule({
            providers: [AppConfigService],
            imports: [HttpClientTestingModule]
        });
    });

    it('should be created', inject(
        [AppConfigService],
        (service: AppConfigService) => {
            expect(service).toBeTruthy();
        }
    ));
});
