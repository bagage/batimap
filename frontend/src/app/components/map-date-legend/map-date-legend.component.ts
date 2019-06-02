import { Component, HostListener, Input, NgZone, OnInit } from '@angular/core';
import { BatimapService } from '../../services/batimap.service';
import { LegendDTO } from '../../classes/legend.dto';
import { LegendService } from '../../services/legend.service';
import * as L from 'leaflet';
import { Observable } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';
import { MatDialog } from '@angular/material';
import { AboutDialogComponent } from '../about-dialog/about-dialog.component';
import { CityDetailsDialogComponent } from '../city-details-dialog/city-details-dialog.component';
import { ObsoleteCityDTO } from '../../classes/obsolete-city.dto';
import { Unsubscriber } from '../../classes/unsubscriber';

@Component({
    selector: 'app-map-date-legend',
    templateUrl: './map-date-legend.component.html',
    styleUrls: ['./map-date-legend.component.css']
})
export class MapDateLegendComponent extends Unsubscriber implements OnInit {
    @Input() map: L.Map;
    @Input() cadastreLayer;

    legendItems$: Observable<LegendDTO[]>;
    bounds: L.LatLngBounds;
    error = false;

    constructor(
        private zone: NgZone,
        private batimapService: BatimapService,
        public legendService: LegendService,
        private matDialog: MatDialog
    ) {
        super();
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
        if (
            !this.bounds ||
            this.bounds.toBBoxString() !== bounds.toBBoxString()
        ) {
            this.bounds = bounds;
            this.error = false;
            this.legendItems$ = this.batimapService
                .legendForBbox(this.bounds)
                .pipe(
                    catchError(err => {
                        this.error = true;
                        throw err;
                    })
                );
        }
    }

    legendChanges(legend: LegendDTO) {
        this.legendService.setActive(legend, legend.checked);
        this.cadastreLayer.redraw();
    }

    @HostListener('document:keydown.shift.a')
    openHelp() {
        this.matDialog.open(AboutDialogComponent);
    }

    @HostListener('document:keydown.shift.c')
    feelingLucky() {
        this.autoUnsubscribe(
            this.legendItems$
                .pipe(
                    map(items =>
                        items
                            .filter(it => !this.legendService.isActive(it))
                            .map(it => it.name)
                    ),
                    switchMap(ignored =>
                        this.batimapService.obsoleteCity(ignored)
                    )
                )
                .subscribe((obsoleteCity: ObsoleteCityDTO) => {
                    this.map.setView(obsoleteCity.position, 10, {
                        animate: false
                    });
                    setTimeout(() => {
                        this.matDialog.closeAll();
                        const dialog = this.matDialog.open<
                            CityDetailsDialogComponent
                        >(CityDetailsDialogComponent, {
                            data: [obsoleteCity.city, this.cadastreLayer]
                        });
                        dialog
                            .afterOpened()
                            .subscribe(() =>
                                dialog.componentInstance.updateCity()
                            );
                    }, 0);
                })
        );
    }
}
