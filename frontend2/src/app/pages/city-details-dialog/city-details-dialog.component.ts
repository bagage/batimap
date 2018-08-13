import {Component, Inject} from '@angular/core';
import {MAT_DIALOG_DATA} from '@angular/material';

@Component({
  templateUrl: './city-details-dialog.component.html',
  styleUrls: ['./city-details-dialog.component.css']
})
export class CityDetailsDialogComponent {
  constructor(@Inject(MAT_DIALOG_DATA) public data: any) {
  }
}
