import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {CityDTO} from '../../classes/city.dto';
import {JosmService} from '../../services/josm.service';

@Component({
  selector: 'app-josm-button',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './josm-button.component.html',
  styleUrls: ['./josm-button.component.css']
})
export class JosmButtonComponent {
  @Input() city: CityDTO;
  @Input() josmReady: boolean;

  constructor(private josmService: JosmService) { }

  conflateCity() {
    this.josmService.conflateCity(this.city);
  }
}
