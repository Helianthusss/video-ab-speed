"""Create an empty local SQLite database from schema.sql."""

import os
import sqlite3
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    data_dir = Path(os.environ.get("AB_DATA_DIR", ROOT / "data")).expanduser().resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    database = data_dir / "survey.sqlite"
    schema = (ROOT / "video_ab" / "schema.sql").read_text(encoding="utf-8")
    with closing(sqlite3.connect(database)) as connection:
        with connection:
            connection.executescript(schema)
    print(database)


if __name__ == "__main__":
    main()
