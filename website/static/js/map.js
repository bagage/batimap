/**
 * Created by cimo on 16/10/2016.
 */

$(function () {
    var map, marker, markerRadius;
    var initPosition = [47.651, 2.791];
    initMap = function () {
        console.log('Map is ready.');
        map = L.map('map-view', {
            zoom: 11
        });
        if (!map.restoreView()) {
            map.setView(initPosition, 6);
        }

        // load available colors
        $.getJSON('/colors', function (colors) {
            var filterGroup = document.getElementById('filter-group');
            filterGroup.style.height += 25 * colors.length + 'px';
            for (color in colors) {
                var input = document.createElement('input');
                input.type = 'checkbox';
                input.id = 'color-' + colors[color];
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
                    getCitiesInView(map);
                });
            }
            getCitiesInView(map);
        });


        L.tileLayer('https://tiles.wmflabs.org/bw-mapnik/{z}/{x}/{y}.png').addTo(map);

        marker = L.marker(initPosition, {draggable: true})
            .addTo(map).bindPopup('Drag me around');

        markerRadius = L.circle(initPosition, 2500)
            .addTo(map);
        marker.on('drag', function (event) {
            markerRadius.setLatLng(marker.getLatLng());
        });

        map.on('locationfound', onLocationFound);
        map.on('locationerror', onLocationError);

        map.on('moveend', function(e) { getCitiesInView(map); });

        return map;
    };

    updateMarker = function (radius) {
        markerRadius.setRadius(radius);
    };

    var elemLocation = null;
    locate = function (e) {
        elemLocation = e;
        elemLocation.find('i').text('loop');
        elemLocation.toggleClass('enabled disabled');
        map.locate({setView: true, maxZoom: 16});
    };

    function onLocationFound(e) {
        var radius = e.accuracy / 2;

        L.marker(e.latlng).addTo(map)
            .bindPopup("You're within " + radius + " meters from this point").openPopup();
        L.circle(e.latlng, radius).addTo(map);

        if (elemLocation != null) {
            elemLocation.find('i').text('done');
            elemLocation.toggleClass('enabled disabled');
        }
    }

    function onLocationError(e) {
        alert("Couldn't get your location!");
    }

    var json_req;
    var layers = [];

    getCitiesInView = function (map) {
        console.log("loading cities…");
        // cancel previous request first
        if (json_req)
            json_req.abort();

        // flush previous layers
        for (layer in layers) {
            layers[layer].removeFrom(map);
        }
        layers = []

        var lonNW = map.getBounds().getWest();
        var latNW = map.getBounds().getNorth();
        var lonSE = map.getBounds().getEast();
        var latSE = map.getBounds().getSouth();
        var colors = [];
        $('#filter-group > input[type="checkbox"]:checked').each(function () {
            colors.push($(this).val());
        });
        if (colors.length == 0) return;

        json_req = $.getJSON('/colors/' + lonNW + '/' + latNW + '/' + lonSE + '/' + latSE + '/' + encodeURIComponent(colors.join()), function (geojson) {
            layers.push(L.geoJson(geojson, {
                style: function(feature) {
                    return {color: feature.properties.color};
                },
                onEachFeature: function (feature, layer) {
                    layer.bindPopup(feature.properties.name || 'Unknown');
                }
            }).addTo(map));
            console.log("done. Have loaded ", geojson.features.length);
        });
    };
});
