#!/usr/bin/env python3
import argparse
import configparser
import datetime
import logging
import shutil
import sys
from os import path

import argcomplete
from colorlog import ColoredFormatter

from .city import City
from .josm import Josm


LEVELS = {
    'no': logging.CRITICAL,
    'error': logging.ERROR,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG,
}
LOG = logging.getLogger('batimap')


def stats(db, overpass, department=None, cities=[], force=False):
    if department:
        cities = db.within_departments(
            [d.zfill(2) for d in department])

    for city in cities:
        c = City(db, city)
        print(c)
        (date, author) = c.fetch_osm_data(overpass, force)


def generate(db, cities):
    for city in cities:
        c = City(db, city)
        city_path = c.get_work_path()
        if city_path and not path.exists(city_path):
            c.fetch_cadastre_data()


def work(db, cities):
    for city in cities:
        c = City(db, city)
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
            LOG.debug(
                "Déplacement de {} vers les archives".format(city_path))
            shutil.move(city_path, path.join(
                City.WORKDONE_PATH, path.basename(city_path)))


def configure_logging(verbosity):
    log_level = LEVELS[verbosity] if verbosity in LEVELS else logging.WARNING

    if sys.stdout.isatty():
        formatter = ColoredFormatter(
            '%(asctime)s %(log_color)s%(message)s%(reset)s', "%H:%M:%S")
        stream = logging.StreamHandler()
        stream.setFormatter(formatter)
        LOG.addHandler(stream)
    else:
        logging.basicConfig(
            format='%(asctime)s %(message)s', datefmt="%H:%M:%S")
    LOG.setLevel(log_level)


def batimap():
    parser = argparse.ArgumentParser(
        description="Inspection de l'état du bâti dans OpenStreetMap en France."
    )
    parser.add_argument(
        "-c", "--config",
        dest='config_file',
        default='config.ini',
        type=str,
        help="Fichier de configuration",
    )
    parser.add_argument(
        '-v', '--verbose',
        choices=LEVELS.keys(),
        help="Niveau de verbosité",
    )
    parser.add_argument(
        '--database',
        type=str,
        help="Identifiants pour la base de donnée (host:port:user:password:database)",
        required=True,
    )

    subparsers = parser.add_subparsers(
        help="Plusieurs commandes sont disponibles"
    )
    subparsers.required = True
    subparsers.dest = 'command'

    stats_parser = subparsers.add_parser(
        'stats',
        help="Récupère la date du dernier import du bâti pour une commune ou département",
    )
    stats_parser.add_argument(
        '-f', '--force',
        action='store_true',
        help="Ne pas utiliser la valeur en base de donnée",
    )
    stats_group = stats_parser.add_mutually_exclusive_group(required=True)
    stats_group.add_argument(
        '-d', '--department',
        type=str,
        nargs='+',
        help="département par son numéro",
    )
    stats_group.add_argument(
        '-c', '--cities',
        type=str,
        nargs='+',
        help="communes par numéro INSEE ou nom",
    )
    stats_group.set_defaults(func=stats)

    generate_parser = subparsers.add_parser(
        'generate',
        help="Génère le bâti depuis le cadastre",
    )
    generate_group = generate_parser.add_mutually_exclusive_group(
        required=True,
    )
    generate_group.add_argument(
        '-c', '--cities',
        type=str,
        nargs='+',
        help="communes par numéro INSEE ou nom",
    )
    generate_parser.set_defaults(func=generate)

    work_parser = subparsers.add_parser(
        'work',
        help="Met en place JOSM pour effectuer le travail de mise à jour du bâti",
    )
    work_parser.add_argument(
        '-c', '--cities',
        type=str,
        nargs='+',
        help="communes par numéro INSEE ou nom",
        required=True,
    )
    work_parser.set_defaults(func=work)

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    config = configparser.ConfigParser(
        defaults={
            'here': path.realpath('.'),
        }
    )
    config.read(args.config_file)

    configure_logging(args.verbose)

    try:
        args.func(args)
    except KeyboardInterrupt as e:
        pass


if __name__ == '__main__':
    batimap()
