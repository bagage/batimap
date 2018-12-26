import { NgModule } from "@angular/core";
import { CommonModule } from "@angular/common";
import { JosmButtonComponent } from "./josm-button/josm-button.component";
import { MatLibModule } from "../mat-lib.module";
import { LoaderComponent } from "./loader/loader.component";
import { AboutDialogComponent } from "./about-dialog/about-dialog.component";
import { HowtoDialogComponent } from "./howto-dialog/howto-dialog.component";
import { MapDateLegendComponent } from "./map-date-legend/map-date-legend.component";
import { CityDetailsDialogComponent } from "./city-details-dialog/city-details-dialog.component";
import { JosmScriptUpdateDialogComponent } from './josm-script-update-dialog/josm-script-update-dialog.component';

@NgModule({
  imports: [CommonModule, MatLibModule],
  declarations: [
    CityDetailsDialogComponent,
    AboutDialogComponent,
    HowtoDialogComponent,
    JosmButtonComponent,
    LoaderComponent,
    MapDateLegendComponent,
    JosmScriptUpdateDialogComponent
  ],
  exports: [
    CityDetailsDialogComponent,
    AboutDialogComponent,
    HowtoDialogComponent,
    JosmButtonComponent,
    LoaderComponent,
    MapDateLegendComponent,
    JosmScriptUpdateDialogComponent
  ],
  entryComponents: [
    AboutDialogComponent,
    CityDetailsDialogComponent,
    HowtoDialogComponent,
    JosmScriptUpdateDialogComponent
  ]
})
export class SharedComponentsModule {}
