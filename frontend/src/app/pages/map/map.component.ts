import { Component, HostListener, NgZone, ViewChild } from "@angular/core";
import { AppConfigService } from "../../services/app-config.service";
import { MatDialog } from "@angular/material";
import { CityDetailsDialogComponent } from "../../components/city-details-dialog/city-details-dialog.component";
import { CityDTO } from "../../classes/city.dto";
import { plainToClass } from "class-transformer";
import { MapDateLegendComponent } from "../../components/map-date-legend/map-date-legend.component";
import { LegendService } from "../../services/legend.service";

import * as L from "leaflet";

@Component({
  selector: "app-map",
  templateUrl: "./map.component.html",
  styleUrls: ["./map.component.css"]
})
export class MapComponent {
  @ViewChild(MapDateLegendComponent) legend: MapDateLegendComponent;

  options = {
    layers: [
      L.tileLayer("https://tiles.wmflabs.org/bw-mapnik/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution: "© Contributeurs OpenStreetMap"
      })
    ],
    zoom: 5,
    maxZoom: 13,
    center: L.latLng(46.111, 3.977)
  };
  map: L.Map;
  cadastreLayer: any;
  private searchControl: L.Control;

  constructor(
    private matDialog: MatDialog,
    private zone: NgZone,
    private legendService: LegendService,
    private configService: AppConfigService
  ) {}

  onMapReady(map) {
    this.map = map;
    map.restoreView();
    L.hash(map);
    this.searchControl = L.geocoderBAN({
      placeholder: "Rechercher une commune (shift+f)"
    }).addTo(map);
    this.setupVectorTiles(map);
  }

  stylingFunction(properties, zoom, type): any {
    const date =
      this.legendService.city2date.get(properties.insee) || properties.date;
    const color = this.legendService.date2color(date);
    const moreHidden = (properties.insee.length > 3 && !this.legendService.isActive(date));
    return {
      weight: 2,
      color: color,
      opacity: moreHidden ? 0.08 : 1,
      fill: true,
      radius: type === "point" ? zoom / 2 : 1,
      fillOpacity: moreHidden ? 0.08 : 0.7
    };
  }

  setupVectorTiles(map) {
    // noinspection JSUnusedGlobalSymbols
    const vectorTileOptions = {
      vectorTileLayerStyles: {
        cities: (properties, zoom) =>
          this.stylingFunction(properties, zoom, "polygon"),
        "cities-point": (properties, zoom) =>
          this.stylingFunction(properties, zoom, "point"),
        departments: (properties, zoom) =>
          this.stylingFunction(properties, zoom, "polygon")
      },
      interactive: true, // Make sure that this VectorGrid fires mouse/pointer events
      getFeatureId: function(f) {
        return f.properties.insee;
      }
    };

    this.cadastreLayer = L.vectorGrid.protobuf(
      this.configService.getConfig().tilesServerUrl,
      vectorTileOptions
    );
    this.cadastreLayer.on("click", e => {
      this.zone.run(() => {
        // do not open popup when clicking depts
        if (e.layer.properties.insee.length > 3) {
          this.openPopup(e.layer.properties);
        }
      });
    });
    this.cadastreLayer.addTo(map);

    this.legend.cadastreLayer = this.cadastreLayer;
  }

  openPopup(cityJson: any) {
    const city = plainToClass<CityDTO, object>(CityDTO, cityJson);
    this.matDialog.open(CityDetailsDialogComponent, {
      data: [city, this.cadastreLayer]
    });
  }

  @HostListener("document:keydown.shift.f", ["$event"])
  search(event) {
    event.preventDefault();
    (<any>this.searchControl).toggle();
  }
}
