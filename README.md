# Présentation

Outil de suivi du bâti [OpenStreetMap](https://openstreetmap.org) en France, par rapport au cadastre. Il permet aussi la mise à jour du bâti via l'éditeur [JOSM](https://josm.openstreetmap.de/) et le plugin [Conflation](http://wiki.openstreetmap.org/wiki/JOSM/Plugins/Conflation).

L'état actuel des données peut être visualisé sur [l'instance officiel](https://cadastre.damsy.net).

![Visualisation de l'état du cadastre](https://gitlab.com/bagage/batimap/uploads/fd5a17c60c3f26bc01564edbc0e77283/Capture_d_écran_de_2020-08-02_23-09-41.png)

# Getting started

```sh
cp .env-example .env
docker-compose up # this might take 5-15minutes… App is ready when you see "Batimap initialization done, starting now..."
```

You can then open http://localhost:4200 in a browser.

# Licence

![MIT](./LICENSE)
