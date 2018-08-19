import {Component, Inject, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA} from '@angular/material';
import {City} from '../../classes/city';
import {JosmService} from '../../services/josm.service';
import {Observable} from 'rxjs';

@Component({
  templateUrl: './city-details-dialog.component.html',
  styleUrls: ['./city-details-dialog.component.css']
})
export class CityDetailsDialogComponent implements OnInit {
  city: City;
  josmIsStarted: Observable<boolean>;

  constructor(@Inject(MAT_DIALOG_DATA) private data: City, public josmService: JosmService) {
    this.city = data;
  }

  ngOnInit(): void {
    this.josmIsStarted = this.josmService.isStarted();
  }

  conflateCity() {
    this.josmService.conflateCity(this.city).subscribe();
  }
}
