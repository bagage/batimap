Ce projet contient plusieurs outils pour simplifier l'import / la mise à jour du bâti sur [OpenStreetMap](https://openstreetmap.org) via l'éditeur [JOSM](https://josm.openstreetmap.de/) et le plugin [Conflation](http://wiki.openstreetmap.org/wiki/JOSM/Plugins/Conflation).

L'état actuel des données peut être visualisé sur http://overpass.damsy.net (beta).

![Visualisation de l'état du cadastre](https://user-images.githubusercontent.com/1451988/26934158-d6e63858-4c68-11e7-8cd8-534718e6b3f6.png)

# Contenu de la boîte

 * [desktop](./desktop): Intégration système pour JOSM
   * [josm-mime.xml](./desktop/josm-mime.xml): types MIME (`.jos`, `.joz`, `.osm`) à ouvrir avec JOSM
   * [icons](./desktop/icons)
     * [josm.png](./desktop/icons/josm.png): icône associée aux fichiers `.jos` et `.joz`
     * [osm.svg](./desktop/icons/osm.svg): icône associée aux fichiers `.osm`
   * [josm.desktop.in](./desktop/josm.desktop.in): Entrée [desktop](https://standards.freedesktop.org/desktop-entry-spec/latest/) pour JOSM
 * [josm-custom.jar](./josm-custom.jar): un JOSM modifié (correction du bug [#14666](https://josm.openstreetmap.de/ticket/14666), coloration des éléments `wall=no`, possibilité de décoller plusieurs éléments d'une seule traite, …)
 * [plugins](./plugins): plugins patchés
   * [conflation.jar](./plugins/conflation.jar): zoom automatique en cas de problème
   * [todo.jar](./plugins/todo.jar): ajout d'un bouton "Mark as selected" et gestion du support multicouches
 * [website](./website): code du site https://overpass.damsy.net
 * [tools](./tools)
   * [osm-cadastre.py](./tools/osm-cadastre.py): script principal (voir plus bas)
 * [josm-scripts](./josm-scripts): scripts à utiliser dans JOSM via le plugin [Scripting](http://wiki.openstreetmap.org/wiki/JOSM/Plugins/Scripting)
   * [1segmented.js](./js/1segmented.js): mise en place initiale
   * [2conflation.js](./js/2conflation.js): mise en place de la conflation
   * [3cleanup.js](./js/3cleanup.js): nettoyage final

# Instructions

1. Installation de JOSM et des plugins patchés :
```bash
mkdir -p $HOME/.local/share/{applications,mime/packages,icons,JOSM/plugins}

sed "s|PWD|$PWD|g" desktop/josm.desktop.in > $HOME/.local/share/applications/josm.desktop
ln -sr desktop/josm-mime.xml $HOME/.local/share/mime/packages
ln -sr desktop/icons/* $HOME/.local/share/icons

update-mime-database $HOME/.local/share/mime

ln -srf plugins/* $HOME/.local/share/JOSM/plugins

josm_config="${XDG_CONFIG_HOME-$HOME/.config}/JOSM/preferences.xml"
test -f "$josm_config" && \
    ! grep -q scripting.RunScriptDialog.file-history "$josm_config" && \
    sed -i '/<\/preferences/d' "$josm_config" \
    echo "
      <list key='scripting.RunScriptDialog.file-history'>
        <entry value='$PWD/josm-scripts/1segmented.js'/>
        <entry value='$PWD/josm-scripts/3cleanup.js'/>
        <entry value='$PWD/josm-scripts/2conflation.js'/>
      </list>
    </preferences>
    " >> "$josm_config"
```

2. Installer le plugin `Scripting` dans JOSM

3. Activer l'accès aux fichiers locaux dans les préférences du Contrôle à distance, nécessaire pour utiliser le script (voir ci-dessous).

![Activation de l'accès aux fichiers locaux](https://user-images.githubusercontent.com/1451988/26930245-137b43fa-4c5d-11e7-8445-5508278ef958.png)

# Description du script osm-cadastre.py

```
usage: osm-cadastre.py [-h] [--verbose {debug,info,warning,error,no}]
                       [--overpass {overpass.de,api.openstreetmap.fr,localhost}]
                       {stats,generate,work} ...

positional arguments:
  {stats,generate,work}

optional arguments:
  -h, --help            show this help message and exit
  --verbose {debug,info,warning,error,no}, -v {debug,info,warning,error,no}
  --overpass {overpass.de,api.openstreetmap.fr,localhost}
```

# Guide

Supposons que l'on souhaite mettre à jour le cadastre de [Upie, code insee 26358](http://www.openstreetmap.org/relation/83680) :

1. Vérification de l'état du cadastre dans OSM : `./tools/osm-cadastre.py stats --name Upie`.
    Ici le dernier import date de 2017, donc il est déjà à jour. Supposons qu'il ne le soit pas et qu'on veuille effectuer la mise à jour.
>
    14:56:05 Fetch INSEE for Upie
    14:56:05 Fetch list of vectorized cities in department 26
    14:56:05 Fetch cities boundary for department 26 (via https://overpass-api.de/api/interpreter)
    14:56:06 100.00% Treated 26358 - Upie (last import: 2017)


2. Mise en place de l'environnement : `./tools/osm-cadastre.py work --name Upie`. Cela va générer le bâti depuis le cadastre et ouvrir JOSM dès que c'est prêt.

3. Dans JOSM, ouvrir le menu `Scripting` puis choisir `1segmented.js`. La TODO list va se remplir. Chaque élément correspond à un bâtiment qui est possible segmenté, à vous de décider si oui (et alors il faut le fusionner via le menu `Outils -> Joindre les zones superposées`) ou non.

4. Lorsque toute la TODO liste a été traitée, ouvrir le menu `Scripting` puis choisir `2conflation.js`.

5. Configurer et effectuer la conflation.

6. Une fois terminée, ouvrir une derniére fois le menu `Scripting` puis choisir `3cleanup.js`.

7. Finalement valider les erreurs (`Shift+U`) et envoyer les changements.

Voir le [guide complet](https://wiki.openstreetmap.org/wiki/WikiProject_France/Cadastre/Import_semi-automatique_des_b%C3%A2timents#Utilisation_du_plugin_.C2.ABConflation.C2.BB_dans_JOSM) pour plus d'informations ou le [guide vidéo](https://www.youtube.com/watch?v=8n34tYJXnEI)… ⚠ La démarche a évolué depuis la vidéo.

# Complétion (bash, zsh…)

Ce projet utilise [argcomplete](https://github.com/kislyuk/argcomplete). Pour faire fonctionner la complétion :

## Pour Bash

```sh
eval "$(register-python-argcomplete osm-cadastre)"
```

## Pour Zsh

```sh
autoload bashcompinit
bashcompinit
eval "$(register-python-argcomplete osm-cadastre)"
```
