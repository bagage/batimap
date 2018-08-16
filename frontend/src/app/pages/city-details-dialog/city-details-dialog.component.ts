import {Component, Inject} from '@angular/core';
import {MAT_DIALOG_DATA} from '@angular/material';
import {City} from '../../classes/city';

@Component({
  templateUrl: './city-details-dialog.component.html',
  styleUrls: ['./city-details-dialog.component.css']
})
export class CityDetailsDialogComponent {
  public city: City;

  constructor(@Inject(MAT_DIALOG_DATA) private data: City) {
    this.city = data;
  }

  openJOSM() {

  }
}
