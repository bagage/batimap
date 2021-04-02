import { APP_INITIALIZER, NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { STEPPER_GLOBAL_OPTIONS } from '@angular/cdk/stepper';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { RouterModule, Routes } from '@angular/router';
import { LeafletModule } from '@asymmetrik/ngx-leaflet';
import { MatProgressButtonsModule } from 'mat-progress-buttons';
import { AppComponent } from './app.component';
import { MapComponent } from './pages/map/map.component';
import { PagesModule } from './pages/pages.module';
import { TasksComponent } from './pages/tasks/tasks.component';
import { AppConfigService } from './services/app-config.service';
import { HttpErrorInterceptor } from './services/http-error.interceptor';
import { JosmService } from './services/josm.service';

const appInitializerFn = (appConfig: AppConfigService) => () => appConfig.loadAppConfig();

const appRoutes: Routes = [
    { path: 'tasks', component: TasksComponent },
    { path: '**', component: MapComponent },
];

@NgModule({
    declarations: [AppComponent],
    imports: [
        BrowserAnimationsModule,
        BrowserModule,
        HttpClientModule,
        PagesModule,
        LeafletModule,
        MatProgressButtonsModule.forRoot(),
        RouterModule.forRoot(
            appRoutes,
            // ,{enableTracing: true}
            { relativeLinkResolution: 'legacy' }
        ),
    ],
    providers: [
        AppConfigService,
        {
            provide: APP_INITIALIZER,
            useFactory: appInitializerFn,
            multi: true,
            deps: [AppConfigService],
        },
        {
            provide: HTTP_INTERCEPTORS,
            useClass: HttpErrorInterceptor,
            multi: true,
        },
        // allow custom icons in how to stepper
        {
            provide: STEPPER_GLOBAL_OPTIONS,
            useValue: { displayDefaultIndicatorType: false },
        },
        // {provide: MAT_DIALOG_DEFAULT_OPTIONS, useValue: {maxWidth: '700px'}},
        JosmService,
    ],
    bootstrap: [AppComponent],
})
export class AppModule {}
