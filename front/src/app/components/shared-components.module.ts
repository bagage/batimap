import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { NgApexchartsModule } from 'ng-apexcharts';
import { MatLibModule } from '../mat-lib.module';
import { PipesModule } from '../pipes/pipes.module';
import { AboutDialogComponent } from './about-dialog/about-dialog.component';
import { CityDetailsDialogComponent } from './city-details-dialog/city-details-dialog.component';
import { DepartmentDetailsDialogComponent } from './department-details-dialog/department-details-dialog.component';
import { HowtoDialogComponent } from './howto-dialog/howto-dialog.component';
import { JosmButtonComponent } from './josm-button/josm-button.component';
import { JosmScriptUpdateDialogComponent } from './josm-script-update-dialog/josm-script-update-dialog.component';
import { LegendButtonComponent } from './legend-button/legend-button.component';
import { LoaderComponent } from './loader/loader.component';
import { MapDateLegendComponent } from './map-date-legend/map-date-legend.component';

@NgModule({
    imports: [CommonModule, MatLibModule, PipesModule, NgApexchartsModule],
    declarations: [
        CityDetailsDialogComponent,
        AboutDialogComponent,
        HowtoDialogComponent,
        JosmButtonComponent,
        LoaderComponent,
        MapDateLegendComponent,
        JosmScriptUpdateDialogComponent,
        LegendButtonComponent,
        DepartmentDetailsDialogComponent
    ],
    exports: [
        CityDetailsDialogComponent,
        DepartmentDetailsDialogComponent,
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
        DepartmentDetailsDialogComponent,
        HowtoDialogComponent,
        JosmScriptUpdateDialogComponent
    ]
})
export class SharedComponentsModule {}
