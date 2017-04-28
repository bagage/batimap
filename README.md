# Instructions

Installation de JOSM et des plugins patchés :

```sh
mkdir -p $HOME/.local/share/{applications,mime/packages,icons,JOSM/plugins}

sed "s|PWD|$PWD|g" desktop/josm.desktop.in > $HOME/.local/share/applications/josm.desktop
ln -sr desktop/josm-mime.xml $HOME/.local/share/mime/packages
ln -sr desktop/icons/* $HOME/.local/share/icons

update-mime-database $HOME/.local/share/mime

ln -srf plugins/{utilsplugin2,conflation,todo}.jar $HOME/.local/share/JOSM/plugins
```

# Guide

Supposons que l'on souhaite mettre à jour le cadastre de [Upie, code insee 26358](http://www.openstreetmap.org/relation/83680) :

1. Vérification de l'état du cadastre dans OSM : `./tools/osm-cadastre-stats.sh Upie`

>
    Treatment done! Summary:
    1NSEE   NOM COUNT   DATE    ASSOCIATEDSTREET
    26358   Upie    1805     2017   0

Ici le dernier import date de 2017, donc il est déjà à jour. Supposons qu'il ne le soit pas.

2. Génération du bâti depuis [http://cadastre.openstreetmap.fr/](http://cadastre.openstreetmap.fr/) (cela prend plusieurs minutes, selon la taille de la commune) : `./tools/osm-cadastre-generate-import.sh Upie`

3. Ouverture des fichiers dans nautilus CL358-UPIE-houses-prediction_segmente.osm et CL358-UPIE-houses-simplifie.osm via JOSM.

4. Voir le [guide complet](https://wiki.openstreetmap.org/wiki/WikiProject_France/Cadastre/Import_semi-automatique_des_b%C3%A2timents#Utilisation_du_plugin_.C2.ABConflation.C2.BB_dans_JOSM) pour la suite ou le [guide vidéo](https://www.youtube.com/watch?v=8n34tYJXnEI)…
