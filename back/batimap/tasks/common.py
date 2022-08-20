import json
from pathlib import Path

from batimap.app import BatimapEncoder
from batimap.citydto import CityDTO
from batimap.extensions import batimap, celery, db, odcadastre
from batimap.tasks.utils import task_progress
from flask import current_app


class JosmNotReadyException(Exception):
    pass


@celery.task(bind=True)
def task_initdb(self, items):
    """
    Fetch OSM and Cadastre data for given departments/cities.
    """
    flush_all_tiles_path = Path("tiles/flush_all_tiles")

    items_are_cities = len([1 for x in items if len(x) > 3]) > 0
    if items_are_cities:
        departments = list(
            set([db.get_city_for_insee(insee).department for insee in items])
        )
        departments = sorted([d for d in departments if d is not None])
        current_app.logger.debug(
            f"Will run initdb on departments {departments} from cities {items}"
        )
    else:
        departments = items
        current_app.logger.debug(f"Will run initdb on departments {departments}")

    # if few items must be processed we'll clear only these specific tiles,
    # otherwise we flush all France tiles and regenerate all of them
    flush_all_tiles = len(departments) >= 5 or len(items) >= 100

    if flush_all_tiles and flush_all_tiles_path.exists():
        flush_all_tiles_path.unlink()

    # fill table with cities from cadastre website
    p = 20

    current_app.logger.debug(
        f"Will compute cadastre stats on departments {departments}"
    )
    for (idx, d) in enumerate(departments):
        odcadastre.compute_count(d)
        task_progress(self, 0 * p + (idx + 1) / len(departments) * p)
    current_app.logger.debug(f"Will update raster state on departments {departments}")
    for d in batimap.update_departments_raster_state(departments):
        task_progress(self, 1 * p + d / len(departments) * p)
    current_app.logger.debug(f"Will update OSM state on departments {departments}")
    for d in batimap.fetch_departments_osm_state(departments):
        task_progress(self, 2 * p + d / len(departments) * p)
    current_app.logger.debug(f"Will import cities stats on departments {departments}")
    for d in batimap.import_city_stats_from_osmplanet(items):
        task_progress(self, 3 * p + d / len(items) * p)
    current_app.logger.debug(
        f"Will compute unknown cities stats on departments {departments}"
    )
    unknowns = (
        [c for c in items if db.get_city_for_insee(c).import_date == "unknown"]
        if items_are_cities
        else [c.insee for c in db.get_unknown_cities(departments)]
    )
    for (d, total) in batimap.compute_date_for_undated_cities(unknowns):
        task_progress(self, 4 * p + d / total * p)

    current_app.logger.debug(f"Finalizing initdb on departments {departments}")
    db.session.commit()

    if flush_all_tiles:
        flush_all_tiles_path.touch()
    else:
        for insee in items:
            batimap.clear_tiles(insee)

    task_progress(self, 100)


@celery.task(bind=True)
def task_josm_data_fast(self, insee):
    """
    Do not prepare JOSM data - if unready, it will fail
    """
    c = db.get_city_for_insee(insee)
    if not c.is_josm_ready():
        raise JosmNotReadyException("city is not JOSM ready")

    return task_josm_data_internal(self, insee)


@celery.task(bind=True)
def task_josm_data(self, insee):
    return task_josm_data_internal(self, insee)


def task_josm_data_internal(task, insee):
    task_progress(task, 1)
    c = db.get_city_for_insee(insee)
    # force refreshing cadastre date
    next(batimap.fetch_departments_osm_state([c.department]))
    c = db.get_city_for_insee(insee)
    must_generate_data = not c.is_josm_ready()
    if must_generate_data:
        current_app.logger.debug(f"Fetching cadastre data for {c}")
        # first, generate cadastre data for that city
        for d in batimap.fetch_cadastre_data(c):
            task_progress(task, 1 + d / 100 * 79)
        task_progress(task, 80)
        next(batimap.fetch_departments_osm_state([c.department]))
    task_progress(task, 90)
    result = batimap.josm_data(insee)
    task_progress(task, 95)
    # refresh tiles if import date has changed or josm data was generated
    if db.get_city_for_insee(insee).import_date != result["date"] or must_generate_data:
        batimap.clear_tiles(insee)
    task_progress(task, 99)
    return json.dumps(result)


@celery.task(bind=True)
def task_update_insee(self, insee):
    task_progress(self, 1)
    before = db.get_city_for_insee(insee).import_date
    task_progress(self, 50)
    city = next(batimap.stats(names_or_insees=[insee], force=True))
    task_progress(self, 99)

    if city.import_date != before:
        batimap.clear_tiles(insee)
    task_progress(self, 100)

    return json.dumps(CityDTO(city), cls=BatimapEncoder)
