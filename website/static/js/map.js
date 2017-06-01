/**
 * Created by cimo on 16/10/2016.
 */

$(function () {
    var map, bgLayer;
    var json_req;
    var initPosition = [47.651, 2.791];
    initMap = function () {
        console.log('Map is ready.');
        map = L.map('map-view', {
            zoom: 11
        });
        if (!map.restoreView()) {
            map.setView(initPosition, 6);
        }

        bgLayer = L.tileLayer('https://tiles.wmflabs.org/bw-mapnik/{z}/{x}/{y}.png').addTo(map);

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

        map.on('moveend', function(e) { getCitiesInView(map); });

        return map;
    };

    getCitiesInView = function (map) {
        console.log("loading cities…");
        // cancel previous request first
        if (json_req)
            json_req.abort();

        var lonNW = map.getBounds().getWest();
        var latNW = map.getBounds().getNorth();
        var lonSE = map.getBounds().getEast();
        var latSE = map.getBounds().getSouth();
        var colors = [];
        $('#filter-group > input[type="checkbox"]:checked').each(function () {
            colors.push($(this).val());
        });
        if (colors.length == 0) {
            // flush previous layers
            map.eachLayer(function(layer) {
                if (layer !== bgLayer)
                    layer.removeFrom(map);
            });
            return;
        }

        json_req = $.getJSON('/colors/' + lonNW + '/' + latNW + '/' + lonSE + '/' + latSE + '/' + encodeURIComponent(colors.join()), function (geojson) {
            // flush previous layers
            map.eachLayer(function(layer) {
                if (layer !== bgLayer)
                    layer.removeFrom(map);
            });

            L.geoJson(geojson, {
                style: function(feature) {
                    return {color: feature.properties.color};
                },
                onEachFeature: function (feature, layer) {
                    layer.bindPopup(feature.properties.name || 'Unknown');
                }
            }).addTo(map);
            console.log("done. Have loaded ", geojson.features.length);
        });
    };
});
