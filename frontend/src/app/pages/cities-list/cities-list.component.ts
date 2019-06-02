import { Component, Input, OnInit, ViewChild } from '@angular/core';
import { MatSort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import * as L from 'leaflet';
import { Observable } from 'rxjs';
import { CityDTO } from '../../classes/city.dto';
import { Unsubscriber } from '../../classes/unsubscriber';
import { BatimapService } from '../../services/batimap.service';
import { JosmService } from '../../services/josm.service';

@Component({
    selector: 'app-cities-list',
    templateUrl: './cities-list.component.html',
    styleUrls: ['./cities-list.component.css']
})
export class CitiesListComponent extends Unsubscriber implements OnInit {
    @Input() map: L.Map;
    @ViewChild(MatSort, { static: true }) sort: MatSort;

    displayedColumns: Array<string> = [
        'name',
        'insee',
        'date',
        'details',
        'actions'
    ];
    dataSource = new MatTableDataSource<CityDTO>();
    isReady: boolean;
    josmReady$: Observable<boolean>;

    constructor(
        private readonly batimapService: BatimapService,
        public josmService: JosmService
    ) {
        super();
    }

    ngOnInit() {
        this.dataSource.sort = this.sort;
        this.josmReady$ = this.josmService.isStarted();

        this.refreshDataSource();
        this.map.on('moveend', () => {
            this.refreshDataSource();
        });
    }

    private refreshDataSource() {
        this.isReady = false;
        this.autoUnsubscribe(
            this.batimapService
                .citiesInBbox(this.map.getBounds())
                .subscribe((cities: Array<CityDTO>) => {
                    this.dataSource.data = undefined;
                    this.dataSource.data = cities;
                    this.isReady = true;
                })
        );
    }
}
