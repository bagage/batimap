import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {LeafletModule} from '@asymmetrik/ngx-leaflet';
import {MapComponent} from './map.component';
import {CitiesListModule} from '../cities-list/cities-list.module';

@NgModule({
  imports: [
    CommonModule,
    LeafletModule,
    CitiesListModule
  ],
  declarations: [MapComponent]
})
export class MapModule { }
