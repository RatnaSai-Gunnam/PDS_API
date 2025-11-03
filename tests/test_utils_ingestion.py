import yaml
from app.ingestion.ingest_legislators import parse_date, none_if_blank, yaml_to_rows

def test_none_if_blank():
    assert none_if_blank(None) is None
    assert none_if_blank("") is None
    assert none_if_blank("   ") is None
    assert none_if_blank("x") == "x"

def test_parse_date():
    assert parse_date("2000-01-31").year == 2000
    assert parse_date("bad-date") is None
    assert parse_date(None) is None

def test_yaml_to_rows_filters_and_normalizes(tmp_path):
    sample = [
        {
            "id": {"govtrack": 100},
            "name": {"first": "Jane", "last": "Doe"},
            "bio": {"birthday": "1970-01-01", "gender": "F"},
            "terms": [{"type": "rep", "state": "ca", "party": "Democrat", "url": "https://x"}]
        },
        {
            "id": {"govtrack": 101},
            "name": {"first": "John", "last": "Smith"},
            "bio": {"birthday": "1960-05-05", "gender": "M"},
            "terms": [{"type": "sen", "state": "NY"}]
        },
        {
            "id": {},
            "name": {"first": "No", "last": "ID"},
            "terms": [{"type": "rep", "state": "TX"}]
        },
        {
            "id": {"govtrack": 102},
            "name": {"first": "X", "last": "Y"},
            "terms": [{"type": "rep", "state": "ZZ"}]
        },
    ]
    f = tmp_path / "leg.yaml"
    f.write_text(yaml.safe_dump(sample))
    rows = yaml_to_rows(str(f))
    assert len(rows) == 2
    assert rows[0]["state"] == "CA"
    assert rows[0]["type"] in {"rep", "sen"}
