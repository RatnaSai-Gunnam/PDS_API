
# Political Data Service API
This project provides a RESTful API that exposes structured information about current U.S. legislators, powered by Flask and PostgreSQL.
It supports filtering, pagination, and integrates real-time weather data for each legislator’s state capital.

## Key Features
- Ingests current data for all members of Congress from official repository
- RESTful API built with Flask and PostgreSQL
- Integrates Weather data for each legislator's profile for their state capital through the OpenWeather API
- Includes API documentation with Swagger UI to test endpoints directly in your browser
- Runs on Gunicorn server, containerized with Docker and managed through Docker compose for easy setup
- Includes unit tests, ingestion tests, and endpoint validation

## USAGE
1. Prerequisites
  Before running the project, make sure you have:
  - Docker & Docker Compose installed
  - A valid OpenWeather API key (create one at openweathermap.org/api)

  If you want to run it locally without Docker, install Python 3.11+ and PostgreSQL 16+.

2. Clone this repository 

3. Copy the example environment file and edit it as needed
  - cp .env.example .env

  Set the following inside .env:
  - DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/politicaldb
  - OPENWEATHER_API_KEY=your_api_key_here
  - LOG_LEVEL=INFO

  When running locally (without Docker), change the host from db to localhost.

4. Install dependencies for local runs
  If you prefer to run directly on your machine instead of Docker:

  - python -m venv venv
  - source venv/bin/activate   # (or venv\Scripts\activate on Windows)
  - pip install --upgrade pip
  - pip install -r requirements.txt

  Then start PostgreSQL and create the database:
  - createdb politicaldb

5. Setting up the Database and Schema
  The schema is automatically created from SQLAlchemy models when the API or ingestion script runs.

6. Loading Legislator Data
  The API uses official data legislators-current.yaml from [congress-legislators](https://github.com/unitedstates/congress-legislators) repository. 
  
  Download the dataset: 
    - mkdir -p data
    - curl -L -o data/legislators-current.yaml \
    - https://raw.githubusercontent.com/unitedstates/congress-legislators/refs/heads/master/legislators-current.yaml

  - Run the ingestion script inside the container:
    - docker compose exec api \
    - python -m app.ingestion.ingest_legislators /app/data/legislators-current.yaml

7. Launching the API Server
  Option A – Using Docker 
  - docker compose up -d --build
  This builds the image, runs both Postgres and the Flask API (via Gunicorn), and exposes the API at: http://localhost:5000

  To stop the containers:
  - docker compose down

  Option B – Run locally (without Docker)
  After installing dependencies and creating your database:
  - export FLASK_APP=app/wsgi.py
  - flask run

  The server starts at http://127.0.0.1:5000


## Endpoints

- `GET /api/legislators` — List all legislators (supports state, party, type, pagination)
- `GET /api/legislators/<govtrack_id>` — Get detailed record for one legislator
- `GET /api/stats/party` — Summary counts by political party
- `GET /api/legislators/<govtrack_id>/weather` — Returns legislator info + current weather for their state capital

Swagger documentation is available at `/apidocs`.

## Logging and Caching

Caching: Implemented with Flask-Caching
Default in-memory cache (SimpleCache) with time-to-live values between 120–300 seconds.

Logging: Structured JSON or plain text logs with per-request IDs
Configurable through environment variables in .env.

## Running Tests
All test suites can be executed inside the running container:
- docker compose exec api pytest -v

Covers:
  YAML parsing and validation
  Batch ingestion and upserts
  REST API filtering, pagination, and weather endpoints

## Stopping Services

To stop only the API:
  - docker compose stop api

To stop everything:
  - docker compose down



