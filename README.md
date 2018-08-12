Ce projet contient plusieurs outils pour simplifier l'import / la mise à jour du bâti sur [OpenStreetMap](https://openstreetmap.org) via l'éditeur [JOSM](https://josm.openstreetmap.de/) et le plugin [Conflation](http://wiki.openstreetmap.org/wiki/JOSM/Plugins/Conflation).

L'état actuel des données peut être visualisé sur http://cadastre.damsy.net (beta).

![Visualisation de l'état du cadastre](https://user-images.githubusercontent.com/1451988/26934158-d6e63858-4c68-11e7-8cd8-534718e6b3f6.png)

# Mise en place

## Configuration JOSM

1. Installer le plugin `Scripting` dans JOSM

2. Activer l'accès aux fichiers locaux dans les préférences du Contrôle à distance, nécessaire pour utiliser le script (voir ci-dessous).

![Activation de l'accès aux fichiers locaux](https://user-images.githubusercontent.com/1451988/26930245-137b43fa-4c5d-11e7-8445-5508278ef958.png)

## Mise à jour d'une commune

Supposons que l'on souhaite mettre à jour le cadastre de [Upie, code insee 26358](http://www.openstreetmap.org/relation/83680) :

1. Vérification de l'état du cadastre dans OSM : `FLASK_APP=backend/app.py flask get-city-stats Upie`.
    Ici le dernier import date de 2017, donc il est déjà à jour. Supposons qu'il ne le soit pas et qu'on veuille effectuer la mise à jour.
> Upie(26358): date=2017 author=GautierPP

2. Mise en place de l'environnement : `FLASK_APP=backend/app.py flask josm Upie`. Cela va générer le bâti depuis le cadastre et ouvrir JOSM dès que c'est prêt.

3. Dans JOSM, ouvrir le menu `Scripting` puis choisir le script `1segmented.js`. La TODO list va se remplir. Chaque élément correspond à un bâtiment qui est possible segmenté, à vous de décider si oui (et alors il faut le fusionner via le menu `Outils -> Joindre les zones superposées`) ou non.

4. Lorsque toute la TODO liste a été traitée, ouvrir le menu `Scripting` puis choisir `2conflation.js`.

5. Configurer et effectuer la conflation.

6. Une fois terminée, ouvrir une derniére fois le menu `Scripting` puis choisir `3cleanup.js`.

7. Finalement valider les erreurs (`Shift+U`) et envoyer les changements.

Voir le [guide complet](https://wiki.openstreetmap.org/wiki/WikiProject_France/Cadastre/Import_semi-automatique_des_b%C3%A2timents#Utilisation_du_plugin_.C2.ABConflation.C2.BB_dans_JOSM) pour plus d'informations ou le [guide vidéo](https://www.youtube.com/watch?v=8n34tYJXnEI)… ⚠ La démarche a évolué depuis la vidéo.

## Complétion (bash, zsh…)

Ce projet utilise [argcomplete](https://github.com/kislyuk/argcomplete). Pour faire fonctionner la complétion :

### Pour Bash

```sh
eval "$(register-python-argcomplete osm-cadastre)"
```

### Pour Zsh

```sh
autoload bashcompinit
bashcompinit
eval "$(register-python-argcomplete osm-cadastre)"
```

## Contribution

Voir CONTRIBUTING.md !

Inspiré de [Matus Cimerman](https://github.com/cimox/python-leaflet-gis).
