import {Component, Inject, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA} from '@angular/material';
import {CityDTO} from '../../classes/city.dto';
import {JosmService} from '../../services/josm.service';
import {Observable} from 'rxjs';

@Component({
  templateUrl: './city-details-dialog.component.html',
  styleUrls: ['./city-details-dialog.component.css']
})
export class CityDetailsDialogComponent implements OnInit {
  city: CityDTO;
  josmIsStarted: Observable<boolean>;

  constructor(@Inject(MAT_DIALOG_DATA) private data: CityDTO, public josmService: JosmService) {
    this.city = data;
  }

  ngOnInit(): void {
    this.josmIsStarted = this.josmService.isStarted();
  }
}
