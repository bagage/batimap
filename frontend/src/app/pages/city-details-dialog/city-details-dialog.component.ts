import {Component, Inject, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA} from '@angular/material';
import {CityDTO} from '../../classes/city.dto';
import {JosmService} from '../../services/josm.service';
import {Observable} from 'rxjs';
import {BatimapService} from '../../services/batimap.service';
import {MatProgressButtonOptions} from 'mat-progress-buttons';

@Component({
  templateUrl: './city-details-dialog.component.html',
  styleUrls: ['./city-details-dialog.component.css']
})
export class CityDetailsDialogComponent implements OnInit {
  city: CityDTO;
  josmIsStarted: Observable<boolean>;

  cadastreLayer: any;
  detailsEntry: [string, string][];

  updateButtonOpts: MatProgressButtonOptions = {
    active: false,
    text: 'Rafraîchir',
    buttonColor: 'primary',
    barColor: 'primary',
    raised: true,
    stroked: false,
    mode: 'indeterminate',
    value: 0,
    disabled: false
  };

  constructor(@Inject(MAT_DIALOG_DATA) private data: [CityDTO, any],
              public josmService: JosmService,
              public batimapService: BatimapService) {
    this.city = data[0];
    this.cadastreLayer = data[1];
    this.detailsEntry = Object.entries(this.city.details.dates);
  }

  ngOnInit(): void {
    this.josmIsStarted = this.josmService.isStarted();
  }

  updateCity() {
    this.updateButtonOpts.active = true;
    this.batimapService.updateCity(this.city.insee)
      .subscribe(result => {
          this.updateButtonOpts.active = false;
          this.city = result;
          this.cadastreLayer.redraw();
        },
        () => this.updateButtonOpts.active = false);
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
