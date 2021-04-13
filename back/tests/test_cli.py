from pathlib import Path

import pytest
from batimap.cli.app import initdb_command
from batimap.extensions import db


@pytest.mark.parametrize(
    ("input", "expected_count"),
    ((None, 4), (["01"], 3)),
)
def test_initdb(db_mock_boundaries, app, runner, input, expected_count):
    Path("tiles").mkdir(exist_ok=True)
    file = Path("tiles/initdb_is_done")
    if file.exists():
        file.unlink()

    result = runner.invoke(initdb_command, input)

    assert result.exception is None
    assert result.exit_code == 0
    assert "done\n" == result.output
    assert file.exists()
    with app.app_context():
        assert len(db.get_cities()) == expected_count


def test_initdb_city(db_mock_cities, db_mock_boundaries, app, runner):
    test_initdb(db_mock_boundaries, app, runner, ["01004"], 4)
