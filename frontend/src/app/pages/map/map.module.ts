import { NgModule } from "@angular/core";
import { LeafletModule } from "@asymmetrik/ngx-leaflet";
import { MapComponent } from "./map.component";
import { CitiesListModule } from "../cities-list/cities-list.module";

import "leaflet";
import "leaflet.vectorgrid";
import "leaflet-hash";
import "leaflet-geocoder-ban/dist/leaflet-geocoder-ban";
import "leaflet.restoreview";
import { MatLibModule } from "../../mat-lib.module";
import { CommonModule } from "@angular/common";
import { SharedComponentsModule } from "../../components/shared-components.module";

@NgModule({
  imports: [
    CommonModule,
    LeafletModule,
    MatLibModule,
    CitiesListModule,
    SharedComponentsModule
  ],
  declarations: [MapComponent]
})
export class MapModule {}
