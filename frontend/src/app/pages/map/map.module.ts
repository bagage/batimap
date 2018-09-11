import {NgModule} from '@angular/core';
import {LeafletModule} from '@asymmetrik/ngx-leaflet';
import {MapComponent} from './map.component';
import {CitiesListModule} from '../cities-list/cities-list.module';

import 'leaflet';
import 'leaflet.vectorgrid';
import 'leaflet.restoreview';
import {MatLibModule} from '../mat-lib.module';
import {CityDetailsDialogModule} from '../city-details-dialog/city-details-dialog.module';
import {CommonModule} from '@angular/common';
import {MapDateLegendComponent} from '../../components/map-date-legend/map-date-legend.component';

@NgModule({
  imports: [
    CommonModule,
    LeafletModule,
    MatLibModule,
    CitiesListModule,
    CityDetailsDialogModule
  ],
  declarations: [MapComponent, MapDateLegendComponent],
})
export class MapModule {
}
