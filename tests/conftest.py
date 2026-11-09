import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from app import db
from app.v02_store import ensure_v02_schema
from app.v02_extra import ensure_v02_extra_schema

@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    ensure_v02_schema()
    ensure_v02_extra_schema()
    yield
