import { ComponentType } from '@angular/cdk/overlay';
import { AfterViewInit, Component, HostListener, NgZone, ViewChild } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute, Router } from '@angular/router';
import { deserialize, plainToClass } from 'class-transformer';
import { forkJoin, Observable, of } from 'rxjs';
import { CityDTO, StatsDetailsDTO } from '../../classes/city.dto';
import { DepartmentDTO } from '../../classes/department.dto';
import { CityDetailsDialogComponent } from '../../components/city-details-dialog/city-details-dialog.component';
import { DepartmentDetailsDialogComponent } from '../../components/department-details-dialog/department-details-dialog.component';
import { MapDateLegendComponent } from '../../components/map-date-legend/map-date-legend.component';
import { AppConfigService } from '../../services/app-config.service';
import { BatimapService } from '../../services/batimap.service';
import { LegendService } from '../../services/legend.service';

import * as L from 'leaflet';

@Component({
    selector: 'app-map',
    templateUrl: './map.component.html',
    styleUrls: ['./map.component.css'],
})
export class MapComponent implements AfterViewInit {
    @ViewChild(MapDateLegendComponent, { static: true })
    legend: MapDateLegendComponent;

    options = {
        layers: [
            L.tileLayer('https://tiles.wmflabs.org/bw-mapnik/{z}/{x}/{y}.png', {
                maxZoom: 18,
                attribution: '© Contributeurs OpenStreetMap',
            }),
        ],
        zoom: 5,
        maxZoom: 11,
        center: L.latLng(46.111, 3.977),
    };
    map: L.Map;
    cadastreLayer: any;
    displayLegend = true;
    displayTasks = false;
    private searchControl: L.Control;

    constructor(
        private readonly matDialog: MatDialog,
        private readonly zone: NgZone,
        private readonly legendService: LegendService,
        private readonly configService: AppConfigService,
        private readonly route: ActivatedRoute,
        private readonly router: Router,
        private readonly batimapService: BatimapService
    ) {}

    ngAfterViewInit(): void {
        if (this.route.snapshot.queryParams.insee) {
            this.openPopup(this.route.snapshot.queryParams.insee);
        }
    }

    onMapReady(map) {
        this.map = map;
        this.legend.map = map;
        this.displayTasks = localStorage.getItem('displayTasks') === 'true';
        const hash = L.hash(map);
        hash.formatHash = (m: any) => {
            const center = m.getCenter();
            const zoom = m.getZoom();
            const precision = Math.max(0, Math.ceil(Math.log(zoom) / Math.LN2));

            return `${location.search}#${[zoom, center.lat.toFixed(precision), center.lng.toFixed(precision)].join(
                '/'
            )}`;
        };

        map.restoreView();
        this.searchControl = L.geocoderBAN({
            placeholder: 'Rechercher une commune (shift+f)',
        }).addTo(map);
        this.setupVectorTiles(map);
    }

    stylingFunction(properties, zoom, type): any {
        const isIgnored = this.batimapService.ignoredInsees().indexOf(properties.insee) !== -1;
        const date = isIgnored ? 'ignored' : this.legendService.city2date.get(properties.insee) || properties.date;
        const color = this.legendService.date2color(date);
        // tslint:disable
        const visible = properties.insee.length <= 3 || this.legendService.isActive(date);
        return {
            weight: 2,
            color,
            opacity: visible ? 1 : 0.08,
            fill: true,
            interactive: visible,
            radius: type === 'point' ? (zoom === 8 ? 4 : 2) : 1,
            fillOpacity: visible ? (properties.josm_ready ? 0.8 : 0.4) : 0.08,
        };
    }

    setupVectorTiles(map) {
        // noinspection JSUnusedGlobalSymbols
        const vectorTileOptions = {
            vectorTileLayerStyles: {
                cities: (properties, zoom) => this.stylingFunction(properties, zoom, 'polygon'),
                'cities-point': (properties, zoom) => this.stylingFunction(properties, zoom, 'point'),
                departments: (properties, zoom) => this.stylingFunction(properties, zoom, 'polygon'),
            },
            getFeatureId: feat => feat.properties.insee,
            interactive: true, // Make sure that this VectorGrid fires mouse/pointer events
        };

        this.cadastreLayer = L.vectorGrid.protobuf(this.configService.getConfig().tilesServerUrl, vectorTileOptions);
        this.cadastreLayer.on('click', e => {
            this.zone.run(() => {
                // do not open popup when clicking hidden cities
                if (e.layer.options.opacity !== 1) {
                    return;
                }
                this.openPopup(e.layer.properties.insee, e.layer.properties);
            });
        });
        this.cadastreLayer.addTo(map);

        this.legend.cadastreLayer = this.cadastreLayer;
    }

    @HostListener('document:keydown.shift.f', ['$event']) search(event) {
        event.preventDefault();
        (this.searchControl as any).toggle();
    }

    private openPopup(insee: string, properties?: any) {
        let data$: Observable<any>[];
        let dialogType: ComponentType<DepartmentDetailsDialogComponent | CityDetailsDialogComponent>;

        this.router.navigate(['.'], { relativeTo: this.route, preserveFragment: true, queryParams: { insee: insee } });

        if (insee.length <= 3) {
            dialogType = DepartmentDetailsDialogComponent;
            if (properties) {
                data$ = [of(plainToClass(DepartmentDTO, properties)), of(properties.osmid)];
            } else {
                const insee$ = this.batimapService.department(insee);
                const osmid$ = this.batimapService.osmid(insee);
                data$ = [insee$, osmid$];
            }
        } else {
            dialogType = CityDetailsDialogComponent;
            if (properties) {
                const city = plainToClass(CityDTO, properties);
                city.details = city.details ? deserialize(StatsDetailsDTO, city.details.toString()) : undefined;
                data$ = [of(city), of(properties.osmid), of(this.cadastreLayer)];
            } else {
                const city$ = this.batimapService.city(insee);
                const osmid$ = this.batimapService.osmid(insee);
                data$ = [city$, osmid$, of(this.cadastreLayer)];
            }
        }

        forkJoin(data$).subscribe(data => {
            const ref = this.matDialog.open(dialogType, {
                data: data,
            });
            ref.afterClosed().subscribe(() => {
                this.router.navigate(['.'], { relativeTo: this.route, preserveFragment: true });
            });
        });
    }
}
