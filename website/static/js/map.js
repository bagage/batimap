/**
 * Created by cimo on 16/10/2016.
 */

$(function () {
    var map, bgLayer;
    var json_req;
    var initPosition = [47.651, 2.791];
    initMap = function () {
        // console.log('Map is ready.');
        map = L.map('map-view', {
            minZoom: 5,
            zoom: 11
        });
        if (!map.restoreView()) {
            map.setView(initPosition, 6);
        }
        new L.Hash(map); // display url with z/x/y params

        bgLayer = L.tileLayer('https://tiles.wmflabs.org/bw-mapnik/{z}/{x}/{y}.png',
            { attribution: '© Contributeurs OpenStreetMap'}
        ).addTo(map);

        var stylingFunction = function(properties, zoom, type) {
            color = $.trim(properties.color) //fixme: why do we need that? It looks
            // like tegola is adding extra space around this properties… weird

            color_input = $('input[type=checkbox]#color-' + color.replace('#', ''));
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


        var cadastreURL = "http://overpass.damsy.net/tegola/maps/bati/{z}/{x}/{y}.vector.pbf";
        var vectorTileOptions = {
            rendererFactory: L.canvas.tile,
            maxNativeZoom: 20,
            vectorTileLayerStyles: {
                'cities-point': function(properties, zoom) {
                    return stylingFunction(properties, zoom, 'point')
                },

                'cities': function(properties, zoom) {
                    return stylingFunction(properties, zoom, 'polygon')
                },
            },
            interactive: true,  // Make sure that this VectorGrid fires mouse/pointer events
            getFeatureId: function(f) {
                return f.properties.color;
            }
        };
        L.tileLayer('http://tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        var pbfLayer = L.vectorGrid.protobuf(cadastreURL, vectorTileOptions)
            .on('click', function(e) {  // The .on method attaches an event handler
                L.popup()
                    .setContent(e.layer.properties.insee + " - " + e.layer.properties.name)
                    .setLatLng(e.latlng)
                    .openOn(map);
                    L.DomEvent.stop(e);
            })
            .addTo(map);

        // load available colors
        $.getJSON('/colors', function (colors) {
            var filterGroup = document.getElementById('filter-group');
            filterGroup.style.height += 25 * colors.length + 'px';
            for (color in colors) {
                var input = document.createElement('input');
                input.type = 'checkbox';
                input.id = 'color-' + colors[color].replace('#', '');
                input.checked = true;
                input.className += 'filled-in';
                input.value = colors[color];
                filterGroup.appendChild(input);

                var label = document.createElement('label');
                label.setAttribute('for', input.id);
                label.style.color = colors[color];
                label.textContent = colors[color];
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
});
