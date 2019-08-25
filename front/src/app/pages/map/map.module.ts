import { NgModule } from '@angular/core';
import { LeafletModule } from '@asymmetrik/ngx-leaflet';
import { CitiesListModule } from '../cities-list/cities-list.module';
import { MapComponent } from './map.component';

import { CommonModule } from '@angular/common';
import '@bagage/leaflet.restoreview';
import 'leaflet';
import 'leaflet-geocoder-ban/dist/leaflet-geocoder-ban';
import 'leaflet-hash';
import '@bagage/leaflet.vectorgrid';
import { SharedComponentsModule } from '../../components/shared-components.module';
import { MatLibModule } from '../../mat-lib.module';

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
