import {Component, OnInit} from '@angular/core';
import {canvas, latLng, tileLayer} from 'leaflet';

declare var L: any;

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.css']
})
export class MapComponent implements OnInit {

  options = {
    layers: [
      tileLayer('https://tiles.wmflabs.org/bw-mapnik/{z}/{x}/{y}.png', {maxZoom: 18, attribution: '...'})
    ],
    zoom: 5,
    center: latLng(46.879966, -121.726909)
  };


  initVectorTiles() {
    const stylingFunction = function (properties, zoom, type) {
      const color = properties.color;
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
    };

    const cadastreURL = 'http://localhost:9999/maps/batimap/{z}/{x}/{y}.vector.pbf';
    const vectorTileOptions = {
      rendererFactory: canvas.tile,
      maxZoom: 20,
      maxNativeZoom: 13,
      vectorTileLayerStyles: {
        'cities-point': function (properties, zoom) {
          return stylingFunction(properties, zoom, 'point');
        },

        'cities': function (properties, zoom) {
          return stylingFunction(properties, zoom, 'polygon');
        },
        'departments': function (properties, zoom) {
          return stylingFunction(properties, zoom, 'polygon');
        },
      },
      interactive: true,  // Make sure that this VectorGrid fires mouse/pointer events
      getFeatureId: function (f) {
        return f.properties.color;
      }
    };

    var pbfLayer = L.vectorGrid.protobuf(cadastreURL, vectorTileOptions);
  }

  constructor() {
  }

  ngOnInit() {
  }

}
