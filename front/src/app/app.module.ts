import { APP_INITIALIZER, NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { MAT_STEPPER_GLOBAL_OPTIONS } from '@angular/cdk/stepper';
import { HttpClientModule } from '@angular/common/http';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { RouterModule, Routes } from '@angular/router';
import { LeafletModule } from '@asymmetrik/ngx-leaflet';
import { MatProgressButtonsModule } from 'mat-progress-buttons';
import { AppComponent } from './app.component';
import { MapComponent } from './pages/map/map.component';
import { PagesModule } from './pages/pages.module';
import { AppConfigService } from './services/app-config.service';
import { JosmService } from './services/josm.service';

const appInitializerFn = (appConfig: AppConfigService) => () => appConfig.loadAppConfig();

const appRoutes: Routes = [{ path: '', component: MapComponent }];

@NgModule({
    declarations: [AppComponent],
    imports: [
        BrowserAnimationsModule,
        BrowserModule,
        HttpClientModule,
        PagesModule,
        LeafletModule.forRoot(),
        MatProgressButtonsModule.forRoot(),
        RouterModule.forRoot(
            appRoutes
            // ,{enableTracing: true}
        )
    ],
    providers: [
        AppConfigService,
        {
            provide: APP_INITIALIZER,
            useFactory: appInitializerFn,
            multi: true,
            deps: [AppConfigService]
        },
        // allow custom icons in howto stepper
        {
            provide: MAT_STEPPER_GLOBAL_OPTIONS,
            useValue: { displayDefaultIndicatorType: false }
        },
        // {provide: MAT_DIALOG_DEFAULT_OPTIONS, useValue: {maxWidth: '700px'}},
        JosmService
    ],
    bootstrap: [AppComponent]
})
export class AppModule {}
