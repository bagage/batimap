import {Component, HostListener, Input, NgZone, OnInit} from '@angular/core';
import {BatimapService} from '../../services/batimap.service';
import {LegendDTO} from '../../classes/legend.dto';
import {LegendService} from '../../services/legend.service';
import * as L from 'leaflet';
import {Observable} from 'rxjs';
import {catchError} from 'rxjs/operators';
import {MatDialog} from '@angular/material';
import {AboutDialogComponent} from '../about-dialog/about-dialog.component';
import {CityDetailsDialogComponent} from '../city-details-dialog/city-details-dialog.component';
import {ObsoleteCityDTO} from '../../classes/obsolete-city.dto';

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
      this.zone.run(() => {
        this.refreshLegend();
      });
    });
  }

  refreshLegend() {
    const bounds = this.map.getBounds();
    if (!this.bounds || this.bounds.toBBoxString() !== bounds.toBBoxString()) {
      this.bounds = bounds;
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

  @HostListener('document:keydown.a')
  openHelp() {
    this.dialogRef.open(AboutDialogComponent);
  }

  @HostListener('document:keydown.c')
  feelingLucky() {
    this.batimapService.obsoleteCity().subscribe((obsoleteCity: ObsoleteCityDTO) => {
      this.map.setView(obsoleteCity.position, 10);
      this.dialogRef.closeAll();
      const dialog = this.dialogRef.open<CityDetailsDialogComponent>(CityDetailsDialogComponent, {data: [obsoleteCity.city, this.cadastreLayer]});
      // dialog.afterOpened().subscribe(() => dialog.componentInstance.updateCity());
    });
  }
}
