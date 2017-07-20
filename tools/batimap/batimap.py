#!/usr/bin/env python3

import argparse
import argcomplete
from os import path
import configparser
import datetime
import shutil

from log import Log
from overpassw import Overpassw
from city import City
from josm import Josm
from postgis_db import PostgisDb

import tqdm


def stats(args):
    if args.department:
        cities = []
        for d in args.department:
            cities += my_db.within_department(d.zfill(2))
    else:
        cities = args.cities

    pbar = tqdm.tqdm(cities)
    for city in pbar:
        c = City(my_log.log, my_db, city)

        (date, author) = c.fetch_osm_data(my_overpass, args.force)

        pbar.set_description(
            "{} : {} par {}".format(c, date, author or 'personne'))


def generate(args):
    pbar = tqdm.tqdm(args.cities)
    for city in pbar:
        c = City(my_log.log, my_db, city)
        city_path = city.get_work_path()
        if city_path and not path.exists(city_path):
            c.fetch_cadastre_data()
        pbar.set_description(repr(c))


def work(args):
    pbar = tqdm.tqdm(args.cities)
    for city in pbar:
        c = City(my_log.log, my_db, city)
        date = c.get_last_import_date()
        city_path = c.get_work_path()
        if date == str(datetime.datetime.now().year):
            need_work = input(
                "{} déjà à jour, continuer quand même ? (oui/Non) ".format(c)).lower() == "oui"
        else:
            need_work = city_path is not None

        if need_work:
            if not path.exists(city_path):
                c.fetch_cadastre_data()

            if not Josm.do_work(c):
                return

        if path.exists(city_path):
            my_log.log.debug(
                "Déplacement de {} vers les archives".format(city_path))
            shutil.move(city_path, path.join(
                City.WORKDONE_PATH, path.basename(city_path)))

        pbar.set_description(repr(c))


def batimap():
    parser = argparse.ArgumentParser(
        description="Inspection de l'état du bâti dans OpenStreetMap en France.")
    parser.add_argument("-c", "--config", dest='config_file',
                        default='config.ini', type=str, help="Fichier de configuration")
    parser.add_argument('--verbose', '-v',
                        choices=Log.levels.keys(), help="Niveau de verbosité")
    parser.add_argument('--overpass', choices=Overpassw.endpoints.keys(),
                        help="Adresse du serveur pour les requêtes Overpass")
    parser.add_argument(
        '--database', type=str, help="identifiants pour la base de donnée sous la forme host:port:user:password:database (ex: 'localhost:25432:docker:docker:gis')", required=True)

    subparsers = parser.add_subparsers(
        help="Plusieurs commandes sont disponibles")
    subparsers.required = True
    subparsers.dest = 'command'

    stats_parser = subparsers.add_parser(
        'stats', help="Récupère la date du dernier import du bâti pour une commune ou département")
    stats_parser.add_argument('--force', '-f', action='store_true',
                              help="De ne pas utiliser la valeur en base de donnée et forcer l'execution de la requête Overpass")
    stats_group = stats_parser.add_mutually_exclusive_group(required=True)
    stats_group.add_argument('--department', '-d', type=str,
                             nargs='+', help="département par son numéro")
    stats_group.add_argument('--cities', '-c', type=str,
                             nargs='+', help="communes par numéro INSEE ou nom")
    stats_group.set_defaults(func=stats)

    generate_parser = subparsers.add_parser(
        'generate', help="Génère le bâti depuis le cadastre")
    generate_group = generate_parser.add_mutually_exclusive_group(
        required=True)
    generate_group.add_argument('--cities', '-c', type=str,
                                nargs='+', help="communes par numéro INSEE ou nom")
    generate_parser.set_defaults(func=generate)

    work_parser = subparsers.add_parser(
        'work', help="Met en place JOSM pour effectuer le travail de mise à jour du bâti")
    work_parser.add_argument('--cities', '-c', type=str,
                             nargs='+', help="communes par numéro INSEE ou nom", required=True)
    work_parser.set_defaults(func=work)

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    config = configparser.ConfigParser(
        defaults={'here': path.realpath('.')})
    config.read(args.config_file)

    global my_log, my_overpass, my_db
    my_log = Log(args.verbose)
    my_overpass = Overpassw(my_log.log, args.overpass)
    (host, port, user, password, database) = args.database.split(":")
    my_db = PostgisDb(my_log.log, host, port, user, password, database)
    Josm.log = my_log.log
    try:
        args.func(args)
    except KeyboardInterrupt as e:
        pass


if __name__ == '__main__':
    batimap()
