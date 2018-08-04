var out = java.lang.System.out;

// 1. We must ensure that we have our required layer "houses-simplifie" and OSM DATA
var housesLayer = null;
var osmLayer = null;
for (var i = 0; i < josm.layers.length; i++) {
    var layer = josm.layers.get(i);
    if (layer.name.endsWith("-houses-simplifie.osm")) {
        housesLayer = layer;
    } else if (layer.name.startsWith("Données OSM pour ")) {
        osmLayer = layer;
    }
}


function do_work()  {
    // 2. Cadastre layer: add wall=yes to everything that has not wall=no and select buildings
    var command = require("josm/command");
    var ds1 = housesLayer.data
    var walls = ds1.query('-wall=no -child');
    command.change(walls, {
       tags: {"wall": "yes"}
    }).applyTo(housesLayer);
    var buildings = ds1.query('building=* -type:relation');
    ds1.selection.clearAll();
    ds1.selection.add(buildings);

    // 3. OSM layer: select all elements within relation by first selecting city, then all inside, then filter buildings
    insee = osmLayer.name.split(" ").splice(-3)[0];
    var ds2 = osmLayer.data;
    var city = ds2.query('"ref:INSEE"=' + insee);
    ds2.selection.clearAll();
    ds2.selection.add(city);

    var utils2Classloader = org.openstreetmap.josm.plugins.PluginHandler.getPluginClassLoader("utilsplugin2");
    if (utils2Classloader == null) {
        josm.alert("Le plugin utilsplugin2 ne semble pas installé : " + e.message);
        return;
    }
    var utils2Plugin = utils2Classloader.loadClass("org.openstreetmap.josm.plugins.utilsplugin2.selection.NodeWayUtils");
    var inside = utils2Plugin.getMethod('selectAllInside', java.util.Collection, org.openstreetmap.josm.data.osm.DataSet).invoke(null, ds2.getSelected(), ds2);
    // var inside = utils2Plugin.selectAllInside(ds2.getSelected(), ds2, true);
    ds2.addSelected(inside);

    var buildings = ds2.query('selected building=* -type:relation');
    ds2.selection.clearAll();
    ds2.selection.add(buildings);

    // 4. select work layer
    josm.layers.activeLayer = osmLayer;

    // 5. configure conflation
    josm.alert("Merci d'ouvrir la fenêtre de configuration de conflation maintenant.\nReference layer : " + housesLayer.name + "\nData layer: " + osmLayer.name);
}

if (housesLayer == null) {
    josm.alert("Impossible de trouver le calque de travail (XXX-houses-simplifie.osm)")
} else if (osmLayer == null) {
    josm.alert("Impossible de trouver le calque de travail (Données OSM pour XXX)")
} else {
    do_work();
}
