var out = java.lang.System.out;

// 1. We must ensure that we have our required layer OSM DATA
var osmLayer = null;
for (var i = 0; i < josm.layers.length; i++) {
    var layer = josm.layers.get(i);
    if (layer.name.startsWith("Données OSM pour ")) {
        osmLayer = layer;
    }
}


function do_work()  {
    // 2. Remove wall=yes tag
    var command = require("josm/command");
    var ds1 = osmLayer.data
    var walls = ds1.query('wall=yes');
    command.change(walls, {
       tags: {"wall": null}
    }).applyTo(osmLayer);
}

if (osmLayer == null) {
    josm.alert("Impossible de trouver le calque de travail (Données OSM pour XXX)")
} else {
    do_work();
}
