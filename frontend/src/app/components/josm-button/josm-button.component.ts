import {ChangeDetectionStrategy, ChangeDetectorRef, Component, Input} from '@angular/core';
import {CityDTO} from '../../classes/city.dto';
import {JosmService} from '../../services/josm.service';
import {BatimapService} from '../../services/batimap.service';
import {ConflateCityDTO} from '../../classes/conflate-city.dto';

@Component({
  selector: 'app-josm-button',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './josm-button.component.html',
  styleUrls: ['./josm-button.component.css']
})
export class JosmButtonComponent {
  @Input() city: CityDTO;
  @Input() josmReady: boolean;

  isLoading = false;

  constructor(private josmService: JosmService,
              private batimapService: BatimapService,
              private changeDetector: ChangeDetectorRef) {
  }

  conflateCity() {
    this.isLoading = true;
    this.josmService.conflateCity(this.city).subscribe(null, null, () => {
      this.isLoading = false;
      this.changeDetector.detectChanges();
    });
  }

  prepareCity() {
    this.isLoading = true;
    this.batimapService.cityData(this.city.insee).subscribe((conflateDTO: ConflateCityDTO) => {
      if (conflateDTO.buildingsUrl && conflateDTO.segmententationPredictionssUrl) {
        this.city.josm_ready = true;
      }
    }, null, () => {
      this.isLoading = false;
      this.changeDetector.detectChanges();
    });
  }
}
