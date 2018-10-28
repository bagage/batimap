import {Component, Inject, Input, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA} from '@angular/material';
import {CityDTO} from '../../classes/city.dto';
import {JosmService} from '../../services/josm.service';
import {Observable} from 'rxjs';
import {BatimapService} from '../../services/batimap.service';
import {LegendService} from '../../services/legend.service';

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

  constructor(@Inject(MAT_DIALOG_DATA) private data: [CityDTO, any],
              public josmService: JosmService,
              public batimapService: BatimapService,
              private legendService: LegendService) {
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
        },
        () => this.isUpdating = false);
  }

  lastImport(): string {
    const d = this.city.date;
    if (!d || d === 'never') {
      return 'Le bâti n\'a jamais été importé';
    } else if (d === 'raster') {
      return 'Ville raster, pas d\'import possible';
    } else if (Number.isInteger(+d)) {
      return `Dernier import en ${d}.`;
    } else {
      return `Le bâti existant ne semble pas provenir du cadastre.`;
    }
  }
}
