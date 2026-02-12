from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.core.config import get_database_url

DATABASE_URL = get_database_url()


class Base(DeclarativeBase):
    pass


class CentreModel(Base):
    __tablename__ = "centres"
    __table_args__ = (
        UniqueConstraint("osm_type", "osm_id", name="uq_centre_osm_identity"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    lat: Mapped[float | None] = mapped_column(nullable=True)
    lon: Mapped[float | None] = mapped_column(nullable=True)
    osm_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    osm_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    specialities: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_tags_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    capacity_max: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    capacity_available: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_wait_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    catchment_population: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)


class ReferenceModel(Base):
    __tablename__ = "references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("centres.id"), nullable=False)
    dest_id: Mapped[str] = mapped_column(ForeignKey("centres.id"), nullable=False)
    travel_minutes: Mapped[int] = mapped_column(Integer, nullable=False)


class PatientModel(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    symptoms: Mapped[str] = mapped_column(String(255), nullable=False)


class EpisodeModel(Base):
    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), nullable=False)
    source_id: Mapped[str] = mapped_column(ForeignKey("centres.id"), nullable=False)
    recommended_dest_id: Mapped[str] = mapped_column(ForeignKey("centres.id"), nullable=False)
    reward: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CountryIndicatorModel(Base):
    __tablename__ = "country_indicators"
    __table_args__ = (
        UniqueConstraint(
            "country_code",
            "indicator_code",
            "year",
            name="uq_country_indicator_year",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country_code: Mapped[str] = mapped_column(String(8), nullable=False)
    indicator_code: Mapped[str] = mapped_column(String(64), nullable=False)
    indicator_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    value: Mapped[float] = mapped_column(nullable=False)
    source_file: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)


engine_kwargs: dict = {"future": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    Base.metadata.create_all(engine)
    _ensure_sqlite_schema_updates()


def _ensure_sqlite_schema_updates() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        return

    required_columns = {
        "lat": "REAL",
        "lon": "REAL",
        "osm_type": "TEXT",
        "osm_id": "TEXT",
        "raw_tags_json": "TEXT",
        "capacity_max": "INTEGER NOT NULL DEFAULT 10",
        "catchment_population": "INTEGER DEFAULT 0",
    }

    with engine.begin() as conn:
        rows = conn.execute(text("PRAGMA table_info(centres)")).fetchall()
        existing = {row[1] for row in rows}

        for col, sql_type in required_columns.items():
            if col not in existing:
                conn.execute(text(f"ALTER TABLE centres ADD COLUMN {col} {sql_type}"))

        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_centres_osm_identity "
                "ON centres(osm_type, osm_id)"
            )
        )


def get_session() -> Session:
    return SessionLocal()


if __name__ == "__main__":
    init_db()
    print("SQLite schema initialized: carepath.db")
