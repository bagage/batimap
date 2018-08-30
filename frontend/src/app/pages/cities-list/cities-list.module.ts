import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {CitiesListComponent} from './cities-list.component';
import {MatSortModule, MatTableModule} from '@angular/material';
import {MatLibModule} from '../mat-lib.module';
import {SharedComponentsModule} from '../../components/shared-components.module';

@NgModule({
  imports: [
    CommonModule,
    MatLibModule,
    SharedComponentsModule
  ],
  declarations: [CitiesListComponent],
  exports: [CitiesListComponent]
})
export class CitiesListModule {
}
