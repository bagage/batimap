import {ChangeDetectionStrategy, ChangeDetectorRef, Component, Input, NgZone, OnInit} from '@angular/core';
import {BatimapService} from '../../services/batimap.service';
import {Observable} from 'rxjs';
import {LegendDTO} from '../../classes/legend.dto';
import {LegendService} from '../../services/legend.service';

@Component({
  selector: 'app-map-date-legend',
  templateUrl: './map-date-legend.component.html',
  styleUrls: ['./map-date-legend.component.css']
})
export class MapDateLegendComponent implements OnInit {
  @Input() map;
  @Input() cadastreLayer;

  legendItems: LegendDTO[] = [];

  constructor(private zone: NgZone, private batimapService: BatimapService, public legendService: LegendService) {
  }

  ngOnInit() {
    this.refreshLegend();
    this.map.on('moveend', () => {
      this.refreshLegend();
    });
  }

  refreshLegend() {
    this.batimapService.legendForBbox(this.map.getBounds()).subscribe(val => {
      this.zone.run(() => {
        this.legendItems = val;
      });
    });
  }

  legendChanges(legend: LegendDTO) {
    this.legendService.setActive(legend, legend.checked);
    this.cadastreLayer.redraw();
  }
}
