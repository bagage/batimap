import { Component, EventEmitter, HostListener, Input, NgZone, OnInit, Output } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { combineLatest, concat, Observable, of, zip } from 'rxjs';
import { catchError, map, switchMap, tap, toArray } from 'rxjs/operators';
import { LegendDTO } from '../../classes/legend.dto';
import { ObsoleteCityDTO } from '../../classes/obsolete-city.dto';
import { Unsubscriber } from '../../classes/unsubscriber';
import { BatimapService } from '../../services/batimap.service';
import { LegendService } from '../../services/legend.service';
import { AboutDialogComponent } from '../about-dialog/about-dialog.component';
import { CityDetailsDialogComponent } from '../city-details-dialog/city-details-dialog.component';
import { MapDateLegendModel } from './map-date-legend.model';

import * as L from 'leaflet';

@Component({
    selector: 'app-map-date-legend',
    templateUrl: './map-date-legend.component.html',
    styleUrls: ['./map-date-legend.component.css'],
})
export class MapDateLegendComponent extends Unsubscriber implements OnInit {
    @Input() map: L.Map;
    @Input() cadastreLayer;
    @Input() hideCheckboxes: boolean;

    @Output() readonly hideLegend = new EventEmitter();

    legendItems$: Observable<MapDateLegendModel[]>;
    bounds: L.LatLngBounds;
    error = false;

    constructor(
        private readonly zone: NgZone,
        private readonly batimapService: BatimapService,
        public legendService: LegendService,
        private readonly matDialog: MatDialog
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
        if (this.bounds && this.bounds.toBBoxString() === bounds.toBBoxString()) {
            return;
        }

        this.bounds = bounds;
        this.error = false;
        this.legendItems$ = this.batimapService.legendForBbox(this.bounds).pipe(
            catchError(err => {
                this.error = true;
                throw err;
            }),
            map(items =>
                items.map(
                    it =>
                        new MapDateLegendModel(
                            it.name,
                            it.checked,
                            it.count,
                            it.percent,
                            this.legendService.date2name(it.name),
                            this.legendService.date2color(it.name)
                        )
                )
            )
        );
        if (this.batimapService.ignoredInsees().length > 0) {
            this.legendItems$ = zip(
                of([
                    new MapDateLegendModel(
                        'ignored',
                        this.legendService.isActive('ignored'),
                        this.batimapService.ignoredInsees().length,
                        undefined,
                        this.legendService.date2name('ignored'),
                        this.legendService.date2color('ignored')
                    ),
                ]),
                this.legendItems$
            ).pipe(map(result => result[0].concat(result[1])));
        }
    }

    legendChanges(legend: LegendDTO) {
        this.legendService.toggleActive(legend, legend.checked);
        this.cadastreLayer.redraw();
    }

    @HostListener('document:keydown.shift.a') openHelp() {
        this.matDialog.open(AboutDialogComponent);
    }

    @HostListener('document:keydown.shift.h') emitHideLegend(): void {
        this.hideLegend.emit();
    }

    @HostListener('document:keydown.shift.c') feelingLucky() {
        this.autoUnsubscribe(
            this.legendItems$
                .pipe(
                    map(items => items.filter(it => !this.legendService.isActive(it)).map(it => it.name)),
                    switchMap(ignored => this.batimapService.obsoleteCity(ignored))
                )
                .subscribe((obsoleteCity: ObsoleteCityDTO) => {
                    this.map.setView(obsoleteCity.position, 10, {
                        animate: false,
                    });
                    setTimeout(() => {
                        this.matDialog.closeAll();
                        const dialog = this.matDialog.open<CityDetailsDialogComponent>(CityDetailsDialogComponent, {
                            data: [obsoleteCity.city, obsoleteCity.osmid, this.cadastreLayer],
                        });
                        dialog.afterOpened().subscribe(() => dialog.componentInstance.updateCity());
                    }, 0);
                })
        );
    }
}
