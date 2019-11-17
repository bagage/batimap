# Présentation

Outil de suivi du bâti [OpenStreetMap](https://openstreetmap.org) en France, par rapport au cadastre. Il permet aussi la mise à jour du bâti via l'éditeur [JOSM](https://josm.openstreetmap.de/) et le plugin [Conflation](http://wiki.openstreetmap.org/wiki/JOSM/Plugins/Conflation).

L'état actuel des données peut être visualisé sur https ://cadastre.damsy.net

![Visualisation de l'état du cadastre](https://gitlab.com/bagage/batimap/wikis/uploads/20819cf4464309a987e55caaf1cc58da/Capture_d_%C3%A9cran_de_2018-10-29_18-34-52.png)

# Getting started

```sh
cp .env-example .env
mkdir -p data/postgis data/imposm data/redis data/tiles
docker-compose up
```

# Licence

MIT
