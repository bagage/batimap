import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {MapModule} from './map/map.module';
import {CitiesListModule} from './cities-list/cities-list.module';

@NgModule({
  imports: [
    CommonModule,
    MapModule,
    CitiesListModule
  ]
})
export class PagesModule { }
