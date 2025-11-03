# app/ingestion/ingest_legislators.py
import os
import sys
import time
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import yaml

# App logging (uses app/logging_config.py)
try:
    from app.logging_config import setup_logging
except Exception:
    def setup_logging():
        logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

load_dotenv()
setup_logging()
logger = logging.getLogger("ingestion")

DATABASE_URL = os.getenv("DATABASE_URL")
BATCH_SIZE = int(os.getenv("INGEST_BATCH_SIZE", "200"))

VALID_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS",
    "KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY",
    "NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV",
    "WI","WY","DC"
}

def parse_date(date_str: str | None):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except Exception:
        return None

def none_if_blank(x):
    if x is None:
        return None
    s = str(x).strip()
    return s if s else None

def yaml_to_rows(yaml_path):
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    rows = []
    for person in data:
        ids = person.get("id", {}) or {}
        name = person.get("name", {}) or {}
        bio  = person.get("bio", {}) or {}
        terms = person.get("terms", []) or []
        current_term = terms[-1] if terms else {}

        if "govtrack" not in ids:
            continue

        govtrack_id = int(ids["govtrack"])
        first_name = none_if_blank(name.get("first"))
        last_name  = none_if_blank(name.get("last"))
        birthday   = parse_date(none_if_blank(bio.get("birthday")))
        gender     = none_if_blank(bio.get("gender"))

        type_ = none_if_blank(current_term.get("type"))
        type_ = type_.lower() if type_ else None
        state = none_if_blank(current_term.get("state"))
        state = state.upper() if state else None
        party = none_if_blank(current_term.get("party"))
        url   = none_if_blank(current_term.get("url"))

        if type_ not in {"sen", "rep"}:
            continue
        if state not in VALID_STATES:
            continue
        if not first_name or not last_name:
            continue

        district_raw = current_term.get("district")
        try:
            district = int(district_raw) if district_raw not in (None, "", "NA") else None
        except Exception:
            district = None

        rows.append({
            "govtrack_id": govtrack_id,
            "first_name": first_name,
            "last_name": last_name,
            "birthday": birthday,
            "gender": gender,
            "type": type_,
            "state": state,
            "district": district,
            "party": party,
            "url": url,
        })
    return rows

def main():
    if len(sys.argv) < 2:
        logger.error("Usage: python -m app.ingestion.ingest_legislators <path_to_legislators-current.yaml>")
        sys.exit(1)

    src_path = sys.argv[1]
    print(f"Loading data from {src_path} ...")
    if not os.path.exists(src_path):
        logger.error("File not found: %s", src_path)
        sys.exit(1)

    if not DATABASE_URL:
        logger.error("DATABASE_URL is not configured")
        sys.exit(1)

    t0 = time.time()
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    # Create schema ONCE via ORM 
    try:
        from app.db.models import Base  
        with engine.begin() as conn:
            Base.metadata.create_all(bind=conn)
    except Exception as e:
        logger.error("Failed to create schema via ORM: %s", e)
        sys.exit(1)

    records = yaml_to_rows(src_path)
    total_source = len(records)
    if not records:
        logger.warning("No valid records found in YAML after normalization/validation.")
        sys.exit(0)

    Session = sessionmaker(bind=engine)

    insert_sql = text("""
        INSERT INTO legislators (govtrack_id, first_name, last_name, birthday, gender, type, state, district, party, url)
        VALUES (:govtrack_id, :first_name, :last_name, :birthday, :gender, :type, :state, :district, :party, :url)
        ON CONFLICT (govtrack_id) DO UPDATE SET
          first_name=EXCLUDED.first_name,
          last_name=EXCLUDED.last_name,
          birthday=EXCLUDED.birthday,
          gender=EXCLUDED.gender,
          type=EXCLUDED.type,
          state=EXCLUDED.state,
          district=EXCLUDED.district,
          party=EXCLUDED.party,
          url=EXCLUDED.url;
    """)

    ok = bad = 0
    batches = 0
    fallbacks = 0
    batch = []

    with Session() as session:
        for rec in records:
            batch.append(rec)
            if len(batch) >= BATCH_SIZE:
                batches += 1
                try:
                    session.execute(insert_sql, batch)
                    session.commit()
                    ok += len(batch)
                except Exception as e:
                    session.rollback()
                    fallbacks += 1
                    logger.warning("Batch upsert failed; falling back per-row: %s", str(e))
                    for row in batch:
                        try:
                            session.execute(insert_sql, row)
                            session.commit()
                            ok += 1
                        except Exception as e_row:
                            session.rollback()
                            bad += 1
                            logger.warning("Row skipped during fallback govtrack_id=%s error=%s",
                                           row.get("govtrack_id"), str(e_row))
                finally:
                    batch.clear()

        if batch:
            batches += 1
            try:
                session.execute(insert_sql, batch)
                session.commit()
                ok += len(batch)
            except Exception as e:
                session.rollback()
                fallbacks += 1
                logger.warning("Final batch upsert failed; falling back per-row: %s", str(e))
                for row in batch:
                    try:
                        session.execute(insert_sql, row)
                        session.commit()
                        ok += 1
                    except Exception as e_row:
                        session.rollback()
                        bad += 1
                        logger.warning("Row skipped during final fallback govtrack_id=%s error=%s",
                                       row.get("govtrack_id"), str(e_row))

    dt = round(time.time() - t0, 3)
    logger.info("Ingestion complete: source_rows=%s inserted_or_updated=%s skipped=%s batches=%s fallbacks=%s duration_sec=%s",
                total_source, ok, bad, batches, fallbacks, dt)

if __name__ == "__main__":
    main()
