import os
from pathlib import Path
import runpy
import sqlite3
from contextlib import closing
from tempfile import TemporaryDirectory

import streamlit as st

from src.generate_dataset import SEED, generate


@st.cache_resource
def demo_database():
    folder = TemporaryDirectory(prefix="yottaflex-")
    path = Path(folder.name) / "liquidity.db"
    with closing(sqlite3.connect(path)) as db:
        generate(db, "full", SEED)
    return folder, path


if not os.environ.get("YOTTAFLEX_DB_PATH"):
    _, database_path = demo_database()
    os.environ["YOTTAFLEX_DB_PATH"] = str(database_path)

runpy.run_path(str(Path(__file__).with_name("app.py")), run_name="__main__")
