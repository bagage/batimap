# What's in the box

 * [josm-custom.jar](./josm-custom.jar): patched JOSM (fix [#14666](https://josm.openstreetmap.de/ticket/14666), highlights `wall=no`, allow unglueing multiple nodes at once) 
 * [josm-init.jos](./josm-init.jos): automatically opens Strava and BDOrtho IGN on startup when launching JOSM
 * [plugins](./plugins): patched plugins for a better conflation workflow
   * [todo.jar](./plugins/todo.jar): add "Mark as selected" button and multilayers support
   * [conflation.jar](./plugins/conflation.jar): zoom on problem if any
 * [desktop](./desktop): better desktop integration
   * [josm-mime.xml](./desktop/josm-mime.xml): mime types (.jos, .joz, .osm) to be opened with JOSM
   * [icons](./desktop/icons)
     * [josm.png](./desktop/icons/josm.png): .jos and .joz files associated icon
     * [osm.svg](./desktop/icons/osm.svg): .osm files associated icon
   * [josm.desktop.in](./desktop/josm.desktop.in): JOSM desktop entry
 * [tools](./tools)
   * [osm-cadastre-generate-import.sh](./tools/osm-cadastre-generate-import.sh): generate buildings from cadastre for given cities
   * [osm-cadastre-stats.sh](./tools/osm-cadastre-stats.sh): number of buildings imported per year for given cities

# Instructions

Installation de JOSM et des plugins patchés :

```sh
mkdir -p $HOME/.local/share/{applications,mime/packages,icons,JOSM/plugins}

sed "s|PWD|$PWD|g" desktop/josm.desktop.in > $HOME/.local/share/applications/josm.desktop
ln -sr desktop/josm-mime.xml $HOME/.local/share/mime/packages
ln -sr desktop/icons/* $HOME/.local/share/icons

update-mime-database $HOME/.local/share/mime

ln -srf plugins/* $HOME/.local/share/JOSM/plugins
```

# Guide

Supposons que l'on souhaite mettre à jour le cadastre de [Upie, code insee 26358](http://www.openstreetmap.org/relation/83680) :

1. Vérification de l'état du cadastre dans OSM : `./tools/osm-cadastre-stats.sh Upie`

>
    Treatment done! Summary:
    1NSEE   NOM COUNT   DATE    ASSOCIATEDSTREET
    26358   Upie    1805     2017   0

Ici le dernier import date de 2017, donc il est déjà à jour. Supposons qu'il ne le soit pas.

2. Génération du bâti depuis [http://cadastre.openstreetmap.fr/](http://cadastre.openstreetmap.fr/) (cela prend plusieurs minutes, selon la taille de la commune) : `./tools/osm-cadastre-generate-import.sh 26358`

3. Ouverture des fichiers dans nautilus CL358-UPIE-houses-prediction_segmente.osm et CL358-UPIE-houses-simplifie.osm via JOSM.

4. Voir le [guide complet](https://wiki.openstreetmap.org/wiki/WikiProject_France/Cadastre/Import_semi-automatique_des_b%C3%A2timents#Utilisation_du_plugin_.C2.ABConflation.C2.BB_dans_JOSM) pour la suite ou le [guide vidéo](https://www.youtube.com/watch?v=8n34tYJXnEI)…
