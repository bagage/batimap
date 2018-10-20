import {Component, Input, NgZone, OnInit} from '@angular/core';
import {BatimapService} from '../../services/batimap.service';
import {LegendDTO} from '../../classes/legend.dto';
import {LegendService} from '../../services/legend.service';
import * as L from 'leaflet';
import {Observable} from 'rxjs';

@Component({
  selector: 'app-map-date-legend',
  templateUrl: './map-date-legend.component.html',
  styleUrls: ['./map-date-legend.component.css']
})
export class MapDateLegendComponent implements OnInit {
  @Input() map: L.Map;
  @Input() cadastreLayer;

  legendItems$: Observable<LegendDTO[]>;
  bounds: L.LatLngBounds;

  constructor(private zone: NgZone, private batimapService: BatimapService, public legendService: LegendService) {
  }

  ngOnInit() {
    this.refreshLegend();
    this.map.on('moveend', () => {
      this.refreshLegend();
    });
  }

  refreshLegend() {
    if (!this.bounds || this.bounds.toBBoxString() !== this.map.getBounds().toBBoxString()) {
      this.bounds = this.map.getBounds();
      this.legendItems$ = this.batimapService.legendForBbox(this.bounds);
    }
  }

  legendChanges(legend: LegendDTO) {
    this.legendService.setActive(legend, legend.checked);
    this.cadastreLayer.redraw();
  }
}
