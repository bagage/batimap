from batimap.extensions import celery, batimap, db
from batimap.citydto import CityDTO, CityEncoder
from pathlib import Path
from shutil import copyfile

import json
import logging

LOG = logging.getLogger(__name__)

def task_progress(task, current):
    current = int(min(current, 100) * 100) / 100  # round to 2 digits

    if task.request.id:
        task.update_state(state="PROGRESS", meta=json.dumps({"current": current, "total": 100}))
    else:
        LOG.warning(f"Task id not set, cannot update its progress to {current}%")


@celery.task(bind=True)
def task_initdb(self, items):
    migration_base = Path("html/.maintenance.html")
    migration_file = Path("html/maintenance.html")
    initdb_is_done_file = Path("tiles/initdb_is_done")

    if migration_base.exists() and not migration_file.exists():
        copyfile(migration_base, migration_file)

    items_are_cities = len([1 for x in items if len(x) > 3]) > 0
    if items_are_cities:
        departments = list(set([db.get_city_for_insee(insee).department for insee in items]))
        departments = sorted([d for d in departments if d is not None])
        LOG.debug(f"Will run initdb on departments {departments} from cities {items}")
    else:
        departments = items
        LOG.debug(f"Will run initdb on departments {departments}")

    if initdb_is_done_file.exists():
        initdb_is_done_file.unlink()

    # fill table with cities from cadastre website
    p = 25
    for d in batimap.update_departments_raster_state(departments):
        task_progress(self, 0 * p + d / len(departments) * p)
    for d in batimap.fetch_departments_osm_state(departments):
        task_progress(self, 1 * p + d / len(departments) * p)
    for d in batimap.import_city_stats_from_osmplanet(items):
        task_progress(self, 2 * p + d / len(items) * p)
    unknowns = (
        [c for c in items if db.get_city_for_insee(c).import_date == "unknown"]
        if items_are_cities
        else [c.insee for c in db.get_unknown_cities(departments)]
    )
    for (d, total) in batimap.compute_date_for_undated_cities(unknowns):
        task_progress(self, 3 * p + d / total * p)
    db.session.commit()

    initdb_is_done_file.touch()
    if migration_file.exists():
        migration_file.unlink()

    task_progress(self, 100)


@celery.task(bind=True)
def task_josm_data(self, insee):
    task_progress(self, 1)
    c = db.get_city_for_insee(insee)
    # force refreshing cadastre date
    next(batimap.fetch_departments_osm_state([c.department]))
    c = db.get_city_for_insee(insee)
    must_generate_data = not c.is_josm_ready()
    if must_generate_data:
        # first, generate cadastre data for that city
        for d in batimap.fetch_cadastre_data(c):
            task_progress(self, 1 + d / 100 * 79)
        task_progress(self, 80)
        next(batimap.fetch_departments_osm_state([c.department]))
    task_progress(self, 90)
    result = batimap.josm_data(insee)
    task_progress(self, 95)
    # refresh tiles if import date has changed or josm data was generated
    if db.get_city_for_insee(insee).import_date != result["date"] or must_generate_data:
        batimap.clear_tiles(insee)
    task_progress(self, 99)
    return json.dumps(result)


@celery.task(bind=True)
def task_update_insee(self, insee):
    before = db.get_city_for_insee(insee)
    task_progress(self, 50)
    city = next(batimap.stats(names_or_insees=[insee], force=True))
    task_progress(self, 99)

    if city.import_date != before.import_date:
        batimap.clear_tiles(insee)
    task_progress(self, 100)

    return json.dumps(CityDTO(city), cls=CityEncoder)
