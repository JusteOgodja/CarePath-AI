from sqlalchemy import ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.core.config import get_database_url

DATABASE_URL = get_database_url()


class Base(DeclarativeBase):
    pass


class CentreModel(Base):
    __tablename__ = "centres"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    specialities: Mapped[str] = mapped_column(String(255), nullable=False)
    capacity_available: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_wait_minutes: Mapped[int] = mapped_column(Integer, nullable=False)


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


engine_kwargs: dict = {"future": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_session() -> Session:
    return SessionLocal()


if __name__ == "__main__":
    init_db()
    print("SQLite schema initialized: carepath.db")
