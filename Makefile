.PHONY: up down rebuild ingest logs test

up:
	docker compose up -d --build

down:
	docker compose down

rebuild:
	docker compose down -v
	docker compose up -d --build

ingest:
	docker compose exec api python -m app.ingestion.ingest_legislators /app/data/legislators-current.yaml

logs:
	docker compose logs -f api

test:
	docker compose exec api pytest -v