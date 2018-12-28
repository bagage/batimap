var out = java.lang.System.out;

// 1. We must ensure that we have our required layer "houses-simplifie" and OSM DATA
var housesLayer = null;
var osmLayer = null;
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
    if ((!layerPattern || layer.name.contains(layerPattern)) && layer.name.endsWith("-houses-simplifie.osm")) {
        housesLayer = layer;
    } else if ((!layerPattern || layer.name.contains(layerPattern)) && layer.name.startsWith("Données OSM pour ")) {
        osmLayer = layer;
    }
}

function startTodo() {
    var todoClassloader = org.openstreetmap.josm.plugins.PluginHandler.getPluginClassLoader("todo");
    if (todoClassloader == null) {
        josm.alert("Le plugin Todo ne semble pas installé");
        return;
    }

    var map = org.openstreetmap.josm.gui.MainApplication.map;
    var dialogsField = map.getClass().getDeclaredField('allDialogs');

    var todoDialog = null;
    dialogsField.setAccessible(true);
    var dialogs = dialogsField.get(map);
    for (var dialogIdx = 0; dialogIdx < dialogs.size(); dialogIdx++) {
        var dialog = dialogs.get(dialogIdx);
        if (dialog.getClass().toString() == "class org.openstreetmap.josm.plugins.todo.TodoDialog") {
            todoDialog = dialog;
        }
    }

    if (todoDialog) {
        var actAddField = todoDialog.class.getDeclaredField('actAdd');
        actAddField.setAccessible(true);
        actAddField.get(todoDialog).actionPerformed(null);

        if (!todoDialog.isVisible()) {
            todoDialog.unfurlDialog();
            josm.alert("Veuillez maintenant réaliser la liste des tâches, passer ensuite à la seconde étape B-conflation.js...")
        }
    } else {
        josm.alert("Impossible de trouver l'onglet Todo. Est-ce que le plugin est installé ?")
        return null;
    }
}

function getConflationDialog() {
    var map = org.openstreetmap.josm.gui.MainApplication.map;
    var dialogsField = map.getClass().getDeclaredField('allDialogs');

    dialogsField.setAccessible(true);
    var dialogs = dialogsField.get(map);
    for (var dialogIdx = 0; dialogIdx < dialogs.size(); dialogIdx++) {
        var dialog = dialogs.get(dialogIdx);
        if (dialog.getClass().toString() == "class org.openstreetmap.josm.plugins.conflation.ConflationToggleDialog") {
            return dialog;
        }
    }

    josm.alert("Impossible de trouver l'onglet Conflation. Est-ce que le plugin est installé ?")
    return null;
}

function startConflation(referenceDataSet, subjectDataSet) {
    var conflationClassLoader = org.openstreetmap.josm.plugins.PluginHandler.getPluginClassLoader("conflation");
    if (conflationClassLoader == null) {
        josm.alert("Le plugin Conflation ne semble pas installé : " + e.message);
        return;
    }
    var settingsClass = conflationClassLoader.loadClass("org.openstreetmap.josm.plugins.conflation.SimpleMatchSettings");
    var settings = settingsClass.newInstance();
    settings.subjectLayer = osmLayer;
    settings.subjectDataSet = osmLayer.data;
    settings.subjectSelection = new java.util.ArrayList();
    settings.subjectSelection.addAll(subjectDataSet.getSelected());
    settings.referenceLayer = housesLayer;
    settings.referenceDataSet = housesLayer.data;
    settings.referenceSelection = new java.util.ArrayList();
    settings.referenceSelection.addAll(referenceDataSet.getSelected());

    const prefs = org.openstreetmap.josm.data.Preferences.main();
    conflationClassLoader.loadClass("org.openstreetmap.josm.plugins.conflation.config.MatchingPanel")
        .getConstructor(
            org.openstreetmap.josm.gui.tagging.ac.AutoCompletionList,
            org.openstreetmap.josm.spi.preferences.IPreferences,
            java.lang.Runnable)
        .newInstance(
            null,
            prefs,
            null)
       .fillSettings(settings);
    const mergingPanel = conflationClassLoader.loadClass("org.openstreetmap.josm.plugins.conflation.config.MergingPanel")
        .getConstructor(
            org.openstreetmap.josm.gui.tagging.ac.AutoCompletionList,
            org.openstreetmap.josm.spi.preferences.IPreferences)
        .newInstance(
            null,
            prefs);
    mergingPanel.restoreFromPreferences(prefs);
    mergingPanel.fillSettings(settings);

    var dialog = getConflationDialog();
    if (dialog != null) {
        var s = dialog.getClass().getDeclaredField('settings');
        s.setAccessible(true);
        s.set(dialog, settings);

        var pm = dialog.getClass().getDeclaredMethod('performMatching');
        pm.setAccessible(true);
        pm.invoke(dialog);

        if (!dialog.isVisible()) {
            dialog.unfurlDialog();
            josm.alert("Veuillez maintenant résoudre la conflation, passer enfin à la validation des erreurs potentielles.")
        }
    }
}

function addRelationBuildingsTodo(layer) {
    var ds = layer.data;
    josm.layers.activeLayer = layer;
    ds.selection.clearAll();
    ds.selection.add(ds.query('type:relation building'));
    startTodo();
}

function do_work()  {
    // 2. OSM layer: select all elements within relation by first selecting city, then all inside, then filter buildings
    insee = osmLayer.name.split(" ")[3];
    var ds2 = osmLayer.data;
    var city = ds2.query('"ref:INSEE"=' + insee);
    ds2.selection.clearAll();
    ds2.selection.add(city);

    var utils2Classloader = org.openstreetmap.josm.plugins.PluginHandler.getPluginClassLoader("utilsplugin2");
    if (utils2Classloader == null) {
        josm.alert("Le plugin utilsplugin2 ne semble pas installé");
        return;
    }
    var utils2Plugin = utils2Classloader.loadClass("org.openstreetmap.josm.plugins.utilsplugin2.selection.NodeWayUtils");
    var inside = utils2Plugin.getMethod('selectAllInside', java.util.Collection, org.openstreetmap.josm.data.osm.DataSet).invoke(null, ds2.getSelected(), ds2);
    // var inside = utils2Plugin.selectAllInside(ds2.getSelected(), ds2, true);
    ds2.addSelected(inside);

    var buildings = ds2.query('selected building=* -type:relation');
    ds2.selection.clearAll();
    ds2.selection.add(buildings);
    if (ds2.selectionEmpty()) {
        josm.alert("Il ne semble y avoir aucun bâtiment actuellement dans cette ville. Aucune conflation à réaliser, il suffit d'importer les bâtiments du calque " + housesLayer.name);
        return;
    }

    // 1. Cadastre layer: add wall=yes to everything that has not wall=no and select buildings
    var command = require("josm/command");
    var ds1 = housesLayer.data
    var walls = ds1.query('-wall=no -child');
    command.change(walls, {
       tags: {"wall": "yes"}
    }).applyTo(housesLayer);
    var buildings = ds1.query('building=* -type:relation');
    ds1.selection.clearAll();
    ds1.selection.add(buildings);

    // 4. select work layer
    josm.layers.activeLayer = osmLayer;

    // 5. configure conflation
    startConflation(ds1, ds2);

    // 6. add in todo-list buildings of type relation (multipolygon), because
    //    conflation plugin does not handle them
    addRelationBuildingsTodo(housesLayer);
    addRelationBuildingsTodo(osmLayer);

    // 7. select work layer
    josm.layers.activeLayer = osmLayer;

    // remove wall=yes temporary attribute
    command.change(walls, {
       tags: {"wall": null}
    }).applyTo(housesLayer);
}

if (housesLayer == null) {
    josm.alert("Impossible de trouver le calque de travail (XXX-houses-simplifie.osm)")
} else if (osmLayer == null) {
    josm.alert("Impossible de trouver le calque de travail (Données OSM pour XXX)")
} else {
    do_work();
}
