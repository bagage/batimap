var out = java.lang.System.out;

function overpass(query)
{
    var OverpassDownloadReader = org.openstreetmap.josm.io.OverpassDownloadReader
    var NullProgressMonitor = org.openstreetmap.josm.gui.progress.NullProgressMonitor;
    var Bounds = org.openstreetmap.josm.data.Bounds;
    var LatLon = org.openstreetmap.josm.data.coor.LatLon;
    var OverpassServerPreference = org.openstreetmap.josm.gui.preferences.server.OverpassServerPreference;

    var minLat = 4;
    var minLon = 45;
    var maxLat = 6;
    var maxLon = 46;
    var min = LatLon(minLat, minLon);
    var max = LatLon(maxLat, maxLon);
    var area = Bounds(min, max);

    var reader = new OverpassDownloadReader(area, OverpassServerPreference.getOverpassServer(), query);
    var dataset = reader.parseOsm(NullProgressMonitor.INSTANCE);

    // var ds2 = new org.openstreetmap.josm.data.osm.DataSet();
    // rel = dataset.relations.iterator().next();
    // dataset.remove(rel);
    // ds2.add(rel);
    // josm.alert(ds2.getDataSourceBoundingBox());

    josm.alert(dataset.getDataSourceBoundingBox());
    return  dataset.relations.iterator().next().id;
}

// 1. We must ensure that we have our required layer "houses-simplifie"
var housesLayer = null;
for (var i = 0; i < josm.layers.length; i++) {
    var layer = josm.layers.get(i);
    if (layer.name.endsWith("-houses-simplifie.osm")) {
        housesLayer = layer;
    }
}

// var insee = housesLayer.name.substring(0, 5);
// var query = 'relation [boundary="administrative"][admin_level="8"]["ref:INSEE"~"^_ID_$"]; out meta;'
// query = query.replace("_ID_", insee);
// josm.alert(query);
// var insee_id = overpass(query);


// 2. We must download the data from OSM for the city
var api = require("josm/api").Api;
var bbox = housesLayer.data.getDataSourceBoundingBox();
out.println(housesLayer.getBBox());
// out.println(bbox.getMin().east());
var lat1 = bbox.getMin().east()
var lon1 = bbox.getMin().north();
var lat2 = bbox.getMax().east();
var lon2 = bbox.getMax().north();
out.println("" + lat1 + ", " + lon1);
out.println("" + lat2 + ", " + lon2);
// var dataset = api.downloadArea({
//     min: {lat: lat1, lon: lon1},
//     max: {lat: lat2, lon: lon2}
// });

// josm.layers.addDataLayer({ds: dataset});


