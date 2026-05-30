import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
DB_SCHEMA = os.getenv("DB_SCHEMA", "corpus")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL, echo=False)

metadata = MetaData()


def reflect_db():
    metadata.clear()
    metadata.reflect(bind=engine, schema=DB_SCHEMA)
    return metadata


def get_table(name: str):
    key = f"{DB_SCHEMA}.{name}"

    if key not in metadata.tables:
        available = ", ".join(metadata.tables.keys())
        raise RuntimeError(
            f"Table {key!r} was not found. Available tables: {available}"
        )

    return metadata.tables[key]