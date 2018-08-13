import {Component} from '@angular/core';
import * as L from 'leaflet';
import {latLng, tileLayer} from 'leaflet';
import {MatDialog} from '@angular/material';
import {CityDetailsDialogComponent} from '../city-details-dialog/city-details-dialog.component';

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.css']
})
export class MapComponent {

  options = {
    layers: [
      tileLayer('https://tiles.wmflabs.org/bw-mapnik/{z}/{x}/{y}.png',
        {
          maxZoom: 18,
          attribution: '© Contributeurs OpenStreetMap'
        })
    ],
    zoom: 5,
    center: latLng(46.111, 3.977)
  };

  constructor(private matDialog: MatDialog) {
  }

  onMapReady(map) {
    map.restoreView();
    this.setupVectorTiles(map);
  }

  date2color(yearStr: string): string {
    const currentYear = new Date().getFullYear();
    if (Number.isInteger(+yearStr)) {
      const year = Number.parseInt(yearStr, 10);
      if (year === currentYear) {
        return 'green';
      } else if (year === currentYear - 1) {
        return 'orange';
      } else {
        return 'red';
      }
    } else if (yearStr === 'raster') {
      return 'black';
    } else if (yearStr === 'never') {
      return 'pink';
    } else {
      // unknown
      return 'gray';
    }
  }

  stylingFunction(properties, zoom, type): any {
    const color = properties.color;// fixme: use instead this.date2color(properties.date);
    // const color_input = $('input[type=checkbox]#color-' + color.replace('#', ''));
    // if (color_input.length == 1 && color_input[0].checked !== true) {
    //     // console.log(color, "is unchecked, do not render");
    //     return []; //do not render it
    // }
    return {
      weight: 2,
      color: color,
      opacity: 1,
      fill: true,
      radius: type === 'point' ? zoom / 2 : 1,
      fillOpacity: 0.7
    };
  }

  setupVectorTiles(map) {
    const cadastreURL = 'http://localhost:9999/maps/batimap/{z}/{x}/{y}.vector.pbf';
    const vectorTileOptions = {
      // rendererFactory: canvas.tile,
      maxZoom: 20,
      maxNativeZoom: 13,
      vectorTileLayerStyles: {
        'cities-point': (properties, zoom) => this.stylingFunction(properties, zoom, 'point'),
        'cities': (properties, zoom) => this.stylingFunction(properties, zoom, 'polygon'),
        'departments': (properties, zoom) => this.stylingFunction(properties, zoom, 'polygon'),
      },
      interactive: true,  // Make sure that this VectorGrid fires mouse/pointer events
      getFeatureId: function (f) {
        return f.properties.color;
      }
    };

    const cadastreLayer = L.vectorGrid.protobuf(cadastreURL, vectorTileOptions);
    cadastreLayer.on('click', (e) => {
      this.openPopup(e);
    });
    cadastreLayer.addTo(map);
  }

  openPopup($event) {
    const dialog = this.matDialog.open(CityDetailsDialogComponent, {data: $event.layer.properties});
  }
}
