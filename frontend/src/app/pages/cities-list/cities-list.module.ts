import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {CitiesListComponent} from './cities-list.component';
import {MatSortModule, MatTableModule} from '@angular/material';

@NgModule({
  imports: [
    CommonModule,
    MatTableModule,
    MatSortModule
  ],
  declarations: [CitiesListComponent],
  exports: [CitiesListComponent]
})
export class CitiesListModule {
}
