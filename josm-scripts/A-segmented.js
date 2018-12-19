var out = java.lang.System.out;

// 1. We must ensure that we have our 2 required layers "predictions_segmente" and "houses-simplifie"
var segmentedLayer = null;
var housesLayer = null;
// if a layer is already selected, assume it's on the city we want to work -
// it allows to have multiple cities open at once
var layerPattern = null;
if (josm.layers.activeLayer !== null) {
    var activeLayerName = josm.layers.activeLayer.name;
    var index = activeLayerName.search(/\d{3}[^\d]/);
    if (index !== -1) {
        layerPattern = activeLayerName.substr(index, 3);
    }
}
for (var i = 0; i < josm.layers.length; i++) {
    var layer = josm.layers.get(i);
    if (!segmentedLayer && (!layerPattern || layer.name.contains(layerPattern)) && layer.name.endsWith("-houses-prediction_segmente.osm")) {
        segmentedLayer = layer;
    } else if (!housesLayer && (!layerPattern || layer.name.contains(layerPattern)) && layer.name.endsWith("-houses-simplifie.osm")) {
        housesLayer = layer;
    }
}

function getTodoDialog() {
    var map = org.openstreetmap.josm.gui.MainApplication.map;
    var dialogsField = map.getClass().getDeclaredField('allDialogs');

    dialogsField.setAccessible(true);
    var dialogs = dialogsField.get(map);
    for (var dialogIdx = 0; dialogIdx < dialogs.size(); dialogIdx++) {
        var dialog = dialogs.get(dialogIdx);
        if (dialog.getClass().toString() == "class org.openstreetmap.josm.plugins.todo.TodoDialog") {
            return dialog;
        }
    }

    josm.alert("Impossible de trouver l'onglet Todo. Est-ce que le plugin est installé ?")
    return null;
}

function do_work() {
    // 2. We select segmented items and add them in the todo list plugin.
    // Then we zoom on first item and wait for user to work.
    josm.layers.activeLayer = segmentedLayer;
    var ds = segmentedLayer.data;
    var segmented = ds.query('type:way name="Est-ce que les bâtiments ne sont pas segmentés ici par le cadastre ?"');
    if (segmented.length > 0) {
        // autozoom on first issue
        var autoScaleAction = org.openstreetmap.josm.actions.AutoScaleAction;
        ds.selection.clearAll();
        ds.selection.add(segmented[0]);
        autoScaleAction.zoomToSelection();

        // select in todo
        ds.selection.clearAll();
        ds.selection.add(segmented);

        var todoClassloader = org.openstreetmap.josm.plugins.PluginHandler.getPluginClassLoader("todo");
        if (todoClassloader == null) {
            josm.alert("Le plugin Todo ne semble pas installé");
            return;
        }
        var dialog = getTodoDialog();
        if (dialog != null) {
            var actAddField = dialog.class.getDeclaredField('actAdd');
            actAddField.setAccessible(true);
            actAddField.get(dialog).actionPerformed(null);

            if (!dialog.isVisible()) {
                dialog.unfurlDialog();
                josm.alert("Veuillez maintenant réaliser la liste des tâches, passer ensuite à la seconde étape B-conflation.js...")
            }
        }
    }

    // 3. select work layer
    josm.layers.activeLayer = housesLayer;
}

if (housesLayer == null && segmentedLayer == null) {
    josm.alert("Impossible de trouver les calques de travail (XXX-houses-prediction_segmente.osm et XXX-houses-simplifie.osm)")
} else if (housesLayer == null) {
    josm.alert("Impossible de trouver le calque de travail (XXX-houses-simplifie.osm)")
} else if (segmentedLayer == null) {
    josm.alert("Impossible de trouver le calque de travail (XXX-houses-prediction_segmente.osm)")
// check that insee match
} else if (segmentedLayer.name.split('-')[0] != housesLayer.name.split('-')[0]) {
    josm.alert("Les calques de travail ne correspondent pas à la même commune INSEE")
} else {
    do_work();
}

