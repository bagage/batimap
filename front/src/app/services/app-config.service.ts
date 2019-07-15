import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

@Injectable()
export class AppConfigService {
    private appConfig;

    constructor(private readonly http: HttpClient) {}

    async loadAppConfig(): Promise<any> {
        return this.http
            .get('/assets/data/appConfig.json')
            .toPromise()
            .then(data => {
                this.appConfig = data;
            });
    }

    getConfig() {
        return this.appConfig;
    }
}
