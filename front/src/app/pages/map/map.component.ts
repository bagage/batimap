import { Component, HostListener, NgZone, ViewChild } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import {
    classToPlain,
    deserialize,
    plainToClass,
    serialize
} from 'class-transformer';
import { CityDetailsDTO, CityDTO } from '../../classes/city.dto';
import { CityDetailsDialogComponent } from '../../components/city-details-dialog/city-details-dialog.component';
import { MapDateLegendComponent } from '../../components/map-date-legend/map-date-legend.component';
import { AppConfigService } from '../../services/app-config.service';
import { LegendService } from '../../services/legend.service';

import * as L from 'leaflet';

@Component({
    selector: 'app-map',
    templateUrl: './map.component.html',
    styleUrls: ['./map.component.css']
})
export class MapComponent {
    @ViewChild(MapDateLegendComponent, { static: true })
    legend: MapDateLegendComponent;

    options = {
        layers: [
            L.tileLayer('https://tiles.wmflabs.org/bw-mapnik/{z}/{x}/{y}.png', {
                maxZoom: 18,
                attribution: '© Contributeurs OpenStreetMap'
            })
        ],
        zoom: 5,
        maxZoom: 11,
        center: L.latLng(46.111, 3.977)
    };
    map: L.Map;
    cadastreLayer: any;
    displayLegend = true;
    private searchControl: L.Control;

    constructor(
        private readonly matDialog: MatDialog,
        private readonly zone: NgZone,
        private readonly legendService: LegendService,
        private readonly configService: AppConfigService
    ) {}

    onMapReady(map) {
        this.map = map;
        this.legend.map = map;
        L.hash(map);
        map.restoreView();
        this.searchControl = L.geocoderBAN({
            placeholder: 'Rechercher une commune (shift+f)'
        }).addTo(map);
        this.setupVectorTiles(map);
    }

    stylingFunction(properties, zoom, type): any {
        const date =
            this.legendService.city2date.get(properties.insee) ||
            properties.date;
        const color = this.legendService.date2color(date);
        const hidden =
            properties.insee.length > 3 && !this.legendService.isActive(date);

        return {
            weight: 2,
            color,
            opacity: hidden ? 0.08 : 1,
            fill: true,
            radius: type === 'point' ? (zoom === 8 ? 4 : 2) : 1,
            fillOpacity: hidden ? 0.08 : properties.josm_ready ? 0.8 : 0.4
        };
    }

    setupVectorTiles(map) {
        // noinspection JSUnusedGlobalSymbols
        const vectorTileOptions = {
            vectorTileLayerStyles: {
                cities: (properties, zoom) =>
                    this.stylingFunction(properties, zoom, 'polygon'),
                'cities-point': (properties, zoom) =>
                    this.stylingFunction(properties, zoom, 'point'),
                departments: (properties, zoom) =>
                    this.stylingFunction(properties, zoom, 'polygon')
            },
            interactive: true // Make sure that this VectorGrid fires mouse/pointer events
        };

        this.cadastreLayer = L.vectorGrid.protobuf(
            this.configService.getConfig().tilesServerUrl,
            vectorTileOptions
        );
        this.cadastreLayer.on('click', e => {
            this.zone.run(() => {
                // do not open popup when clicking depts
                if (e.layer.properties.insee.length <= 3) {
                    return;
                }
                // do not open popup when clicking hiden cities
                if (e.layer.options.opacity !== 1) {
                    return;
                }
                this.openPopup(e.layer.properties);
            });
        });
        this.cadastreLayer.addTo(map);

        this.legend.cadastreLayer = this.cadastreLayer;
    }

    @HostListener('document:keydown.shift.f', ['$event']) search(event) {
        event.preventDefault();
        (this.searchControl as any).toggle();
    }

    private openPopup(cityJson: string) {
        const city = plainToClass(CityDTO, cityJson);
        city.details = city.details
            ? deserialize(CityDetailsDTO, city.details.toString())
            : undefined;
        this.matDialog.open(CityDetailsDialogComponent, {
            data: [city, this.cadastreLayer]
        });
    }
}
