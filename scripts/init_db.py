"""Create an empty local SQLite database from schema.sql."""
import os
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
data_dir=Path(os.environ.get('AB_DATA_DIR',ROOT/'data')).expanduser().resolve()
data_dir.mkdir(parents=True,exist_ok=True)
database=data_dir/'survey.sqlite'
schema=(ROOT/'schema.sql').read_text(encoding='utf-8')
with sqlite3.connect(database) as connection:
    connection.executescript(schema)
print(database)
