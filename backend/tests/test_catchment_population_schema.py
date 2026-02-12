from sqlalchemy import text

from app.db.models import CentreModel, get_session, init_db


def test_catchment_population_column_exists_and_updates() -> None:
    init_db()
    with get_session() as session:
        cols = session.execute(text("PRAGMA table_info(centres)")).fetchall()
        names = {row[1] for row in cols}
        assert "catchment_population" in names

        centre = CentreModel(
            id="CP_TEST",
            name="Catchment Test",
            lat=6.0,
            lon=3.0,
            osm_type="node",
            osm_id="cp_test",
            level="primary",
            specialities="general",
            raw_tags_json="{}",
            capacity_max=10,
            capacity_available=10,
            estimated_wait_minutes=15,
            catchment_population=0,
        )
        session.add(centre)
        session.commit()

        centre.catchment_population = 12345
        session.commit()

        refreshed = session.get(CentreModel, "CP_TEST")
        assert refreshed is not None
        assert refreshed.catchment_population == 12345
