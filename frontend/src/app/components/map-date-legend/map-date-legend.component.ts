import {Component, Input, NgZone, OnInit} from '@angular/core';
import {BatimapService} from '../../services/batimap.service';
import {LegendDTO} from '../../classes/legend.dto';
import {LegendService} from '../../services/legend.service';
import * as L from 'leaflet';
import {Observable} from 'rxjs';
import {catchError} from 'rxjs/operators';
import {MatDialog, MatDialogRef} from '@angular/material';
import {AboutDialogComponent} from '../../pages/about-dialog/about-dialog.component';

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
  error = false;

  constructor(private zone: NgZone, private batimapService: BatimapService, public legendService: LegendService, private dialogRef: MatDialog) {
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
      this.error = false;
      this.legendItems$ = this.batimapService.legendForBbox(this.bounds).pipe(catchError((err) => {
        this.error = true;
        throw err;
      }));
    }
  }

  legendChanges(legend: LegendDTO) {
    this.legendService.setActive(legend, legend.checked);
    this.cadastreLayer.redraw();
  }

  openHelp() {
    this.dialogRef.open(AboutDialogComponent);
  }
}
