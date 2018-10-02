import {Component, Inject, Input, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA} from '@angular/material';
import {CityDTO} from '../../classes/city.dto';
import {JosmService} from '../../services/josm.service';
import {Observable} from 'rxjs';
import {BatimapService} from '../../services/batimap.service';

@Component({
  templateUrl: './city-details-dialog.component.html',
  styleUrls: ['./city-details-dialog.component.css']
})
export class CityDetailsDialogComponent implements OnInit {
  city: CityDTO;
  josmIsStarted: Observable<boolean>;
  isUpdating = false;

  cadastreLayer: any;
  Object = Object;

  constructor(@Inject(MAT_DIALOG_DATA) private data: [CityDTO, any], public josmService: JosmService, public batimapService: BatimapService) {
    this.city = data[0];
    this.cadastreLayer = data[1];
  }

  ngOnInit(): void {
    this.josmIsStarted = this.josmService.isStarted();
  }

  updateCity() {
    this.isUpdating = true;
    this.batimapService.updateCity(this.city.insee)
      .subscribe(result => {
        this.isUpdating = false;
        this.city = result;
        this.cadastreLayer.redraw();
      });
  }
}
