import os, sys, yaml
from sqlalchemy import create_engine, text
from app.ingestion import ingest_legislators as ingest

def test_batched_upsert_sqlite(monkeypatch, tmp_path, test_db_url):
    data = [
        {"id": {"govtrack": 9001}, "name": {"first": "Test", "last": "One"},
         "bio": {"birthday": "1980-01-01"}, "terms": [{"type": "rep", "state": "TX", "party": "Alpha"}]},
        {"id": {"govtrack": 9001}, "name": {"first": "Test", "last": "One"},
         "bio": {"birthday": "1980-01-01"}, "terms": [{"type": "rep", "state": "TX", "party": "Beta"}]},
    ]
    ypath = tmp_path / "ingest.yaml"
    ypath.write_text(yaml.safe_dump(data))

    monkeypatch.setenv("DATABASE_URL", test_db_url)
    monkeypatch.setenv("INGEST_BATCH_SIZE", "1")

    sys.argv = ["ingest", str(ypath)]
    ingest.main()

    eng = create_engine(test_db_url)
    total = eng.execute(text("SELECT COUNT(*) FROM legislators")).scalar()
    party = eng.execute(text("SELECT party FROM legislators WHERE govtrack_id=9001")).scalar()
    assert total == 1
    assert party == "Beta"
