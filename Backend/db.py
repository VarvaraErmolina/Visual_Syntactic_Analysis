import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL, echo=False)

metadata = MetaData()


def reflect_db():
    metadata.reflect(bind=engine)
    return metadata
