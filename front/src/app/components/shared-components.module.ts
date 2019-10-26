import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { MatLibModule } from '../mat-lib.module';
import { AboutDialogComponent } from './about-dialog/about-dialog.component';
import { CityDetailsDialogComponent } from './city-details-dialog/city-details-dialog.component';
import { HowtoDialogComponent } from './howto-dialog/howto-dialog.component';
import { JosmButtonComponent } from './josm-button/josm-button.component';
import { JosmScriptUpdateDialogComponent } from './josm-script-update-dialog/josm-script-update-dialog.component';
import { LegendButtonComponent } from './legend-button/legend-button.component';
import { LoaderComponent } from './loader/loader.component';
import { MapDateLegendComponent } from './map-date-legend/map-date-legend.component';

@NgModule({
    imports: [CommonModule, MatLibModule],
    declarations: [
        CityDetailsDialogComponent,
        AboutDialogComponent,
        HowtoDialogComponent,
        JosmButtonComponent,
        LoaderComponent,
        MapDateLegendComponent,
        JosmScriptUpdateDialogComponent,
        LegendButtonComponent
    ],
    exports: [
        CityDetailsDialogComponent,
        AboutDialogComponent,
        HowtoDialogComponent,
        JosmButtonComponent,
        LoaderComponent,
        MapDateLegendComponent,
        JosmScriptUpdateDialogComponent,
        LegendButtonComponent
    ],
    entryComponents: [
        AboutDialogComponent,
        CityDetailsDialogComponent,
        HowtoDialogComponent,
        JosmScriptUpdateDialogComponent
    ]
})
export class SharedComponentsModule {}
