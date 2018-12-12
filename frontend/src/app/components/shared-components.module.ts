import { NgModule } from "@angular/core";
import { CommonModule } from "@angular/common";
import { JosmButtonComponent } from "./josm-button/josm-button.component";
import { MatLibModule } from "../mat-lib.module";
import { LoaderComponent } from "./loader/loader.component";
import { AboutDialogComponent } from "./about-dialog/about-dialog.component";
import { HowtoDialogComponent } from "./howto-dialog/howto-dialog.component";
import { MapDateLegendComponent } from "./map-date-legend/map-date-legend.component";
import { CityDetailsDialogComponent } from "./city-details-dialog/city-details-dialog.component";

@NgModule({
  imports: [CommonModule, MatLibModule],
  declarations: [
    CityDetailsDialogComponent,
    AboutDialogComponent,
    HowtoDialogComponent,
    JosmButtonComponent,
    LoaderComponent,
    MapDateLegendComponent
  ],
  exports: [
    CityDetailsDialogComponent,
    AboutDialogComponent,
    HowtoDialogComponent,
    JosmButtonComponent,
    LoaderComponent,
    MapDateLegendComponent
  ],
  entryComponents: [
    AboutDialogComponent,
    CityDetailsDialogComponent,
    HowtoDialogComponent
  ]
})
export class SharedComponentsModule {}
