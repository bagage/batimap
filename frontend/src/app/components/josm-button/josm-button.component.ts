import {ChangeDetectionStrategy, ChangeDetectorRef, Component, Input} from '@angular/core';
import {CityDTO} from '../../classes/city.dto';
import {JosmService} from '../../services/josm.service';
import {BatimapService} from '../../services/batimap.service';
import {ConflateCityDTO} from '../../classes/conflate-city.dto';
import {MatProgressButtonOptions} from 'mat-progress-buttons';
import {Observable} from 'rxjs';
import {tap} from 'rxjs/operators';

@Component({
  selector: 'app-josm-button',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './josm-button.component.html',
  styleUrls: ['./josm-button.component.css']
})
export class JosmButtonComponent {
  private _city: CityDTO;

  @Input()
  set city(value: CityDTO) {
    this._city = value;
    if (value.josm_ready) {
      this.options.tooltip = 'Ouvre JOSM avec les calques préconfigurés pour la commune sélectionnée. ' +
        'Si le bouton n\'est pas actif, JOSM n\'est probablement pas démarré';
      this.options.text = 'JOSM';
      this.options.barColor = this.options.buttonColor = 'primary';
    } else {
      this.options.tooltip = 'Prépare les données pour pouvoir être ensuite éditer avec JOSM';
      this.options.text = 'Préparer';
      this.options.barColor = this.options.buttonColor = 'secondary';
    }
  }

  @Input()
  set josmReady(value: boolean) {
    this.options.disabled = this._city.josm_ready && !value;
  }

  options = {
    active: false,
    text: '',
    buttonColor: 'primary',
    barColor: 'primary',
    raised: true,
    stroked: false,
    mode: 'indeterminate',
    value: 0,
    disabled: false,
    tooltip: ''
  };

  constructor(private josmService: JosmService,
              private batimapService: BatimapService,
              private changeDetector: ChangeDetectorRef) {
  }


  onClick() {
    this.options.active = true;
    const obs = this._city.josm_ready ? this.conflateCity() : this.prepareCity();
    obs.subscribe(null, null, () => {
      this.options.active = false;
      this.changeDetector.detectChanges();
    });
  }

  conflateCity(): Observable<any> {
    return this.josmService.conflateCity(this._city);
  }

  prepareCity(): Observable<any> {
    return this.batimapService.cityData(this._city.insee).pipe(tap((conflateDTO: ConflateCityDTO) => {
      if (conflateDTO.buildingsUrl) {
        this._city.josm_ready = true;
      }
    }));
  }
}
