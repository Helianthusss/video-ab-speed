"""Shared paths and environment configuration."""

import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
DATA_DIR = Path(os.environ.get("AB_DATA_DIR", ROOT / "data")).expanduser().resolve()
OUTPUT_DIR = Path(os.environ.get("AB_OUTPUT_DIR", ROOT / "outputs")).expanduser().resolve()
DEMO_DIR = Path(os.environ.get("AB_DEMO_DIR", ROOT / "demo")).expanduser().resolve()
SCHEMA_PATH = PACKAGE_DIR / "schema.sql"
AUTH_USERNAME = os.environ.get("AB_USERNAME", "")
AUTH_PASSWORD = os.environ.get("AB_PASSWORD", "")
