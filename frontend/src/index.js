import L from 'leaflet';
import 'leaflet.restoreview';
import 'leaflet-hash';
import 'leaflet/dist/leaflet.css';
import 'leaflet-geocoder-mapzen';
import 'leaflet.locatecontrol';
import 'leaflet.vectorgrid';

import './css/style.css';
import 'materialize-css/dist/css/materialize.css';
import 'leaflet-geocoder-mapzen/dist/leaflet-geocoder-mapzen.css';
import 'leaflet.locatecontrol/dist/L.Control.Locate.css';
import '../node_modules/github-fork-ribbon-css/gh-fork-ribbon.css';
import '../node_modules/font-awesome/css/font-awesome.css';

import circleX from './assets/circle-x-6x.png';
import circleCheck from './assets/circle-check-6x.png';

import {APISERVER, RASTERTILESERVER, VECTORTILESERVER} from '../config.json';

/**
 * Created by cimo on 16/10/2016.
 */
$(function () {
    var map, bgLayer;
    var json_req;
    var initPosition = [47.651, 2.791];
    var initMap = function () {
        // console.log('Map is ready.');
        map = L.map('map-view', {
            zoom: 11
        });
        if (!map.restoreView()) {
            map.setView(initPosition, 6);
        }
        new L.Hash(map); // display url with z/x/y params

        L.control.geocoder('mapzen-xxEvJ8R').addTo(map);
        L.control.locate({locateOptions: {enableHighAccuracy: true}}).addTo(map);

        bgLayer = L.tileLayer(RASTERTILESERVER + '/{z}/{x}/{y}.png', {
            attribution: '© Contributeurs OpenStreetMap',
            maxNativeZoom: 18
        }
        ).addTo(map);

        var stylingFunction = function(properties, zoom, type) {
            var color = properties.color
            var color_input = $('input[type=checkbox]#color-' + color.replace('#', ''));
            if (color_input.length == 1 && color_input[0].checked !== true) {
                // console.log(color, "is unchecked, do not render");
                return []; //do not render it
            }
            return {
                weight: 2,
                color: color,
                opacity: 1,
                fill: true,
                radius: type === 'point' ? zoom / 2 : 1,
                fillOpacity: 0.7
            }
        }

        var cadastreURL = VECTORTILESERVER + "/{z}/{x}/{y}.vector.pbf";
        var vectorTileOptions = {
            rendererFactory: L.canvas.tile,
            maxZoom: 20,
            maxNativeZoom: 13,
            vectorTileLayerStyles: {
                'cities-point': function(properties, zoom) {
                    return stylingFunction(properties, zoom, 'point')
                },

                'cities': function(properties, zoom) {
                    return stylingFunction(properties, zoom, 'polygon')
                },
                'departments': function(properties, zoom) {
                    return stylingFunction(properties, zoom, 'polygon')
                },
            },
            interactive: true,  // Make sure that this VectorGrid fires mouse/pointer events
            getFeatureId: function(f) {
                return f.properties.color;
            }
        };
        var pbfLayer = L.vectorGrid.protobuf(cadastreURL, vectorTileOptions)
            .on('click', function(e) {  // The .on method attaches an event handler
                var container = L.DomUtil.create('div');
                var text_container = L.DomUtil.create('div','',container);
                var text = L.DomUtil.create('p', '', text_container );
                    text.innerHTML = e.layer.properties.insee + " - " + e.layer.properties.name;
                var button_container = L.DomUtil.create('div','',container);
                var btn = L.DomUtil.create('button', '', button_container);
                    btn.setAttribute('type', 'button');
                    btn.setAttribute('value', e.layer.properties.insee );
                    btn.innerHTML = "Update this city";

                L.DomEvent.on(btn, 'click', e => {
                    $.ajax({
                        type: "POST",
                        url: APISERVER + "/update/" + btn.value,
                        beforeSend: function() {
                            btn.setAttribute( "style", "visibility:hidden" );
                        },
                        complete: function() {
                            pbfLayer.redraw();
                        },
                        success: function(badges) {
                            var ok = L.DomUtil.create('img', '', btn.parentNode);
                            ok.setAttribute('src', circleCheck);
                            ok.setAttribute('height', '24');
                            ok.setAttribute('width', '24');
                        },
                        error: function(badges) {
                            var nok = L.DomUtil.create('img', '', btn.parentNode);
                            nok.setAttribute('src', circleX);
                            nok.setAttribute('height', '24');
                            nok.setAttribute('width', '24');
                        }
                    });
                });

                L.popup()
                    .setContent( container )
                    .setLatLng(e.latlng)
                    .openOn(map);
                    L.DomEvent.stop(e);
            })
            .addTo(map);

        // load available colors
        $.getJSON(APISERVER + '/colors', function (colors) {
            var total = 0
            for (var c in colors) {
                total += colors[c][1];
            }
            var filterGroup = document.getElementById('filter-group');
            filterGroup.style.height += 25 * colors.length + 'px';
            for (c in colors) {
                var color = colors[c][0];
                var percentage = colors[c][1] * 100 / total;

                var input = document.createElement('input');
                input.type = 'checkbox';
                input.id = 'color-' + color.replace('#', '');
                input.checked = true;
                input.className += 'filled-in';
                input.value = color;
                filterGroup.appendChild(input);

                var label = document.createElement('label');
                label.setAttribute('for', input.id);
                label.style.color = color;
                label.textContent = color + ' (' + percentage.toFixed(2) + '%)';
                filterGroup.appendChild(label);

                input.addEventListener('change', function(e) {
                    // todo: could be done better by reappling style
                    // but couldn't make it work
                    pbfLayer.redraw();
                });
            }
        });

        return map;
    };

    initMap();
});
