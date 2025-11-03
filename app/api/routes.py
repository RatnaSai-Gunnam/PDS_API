from flask import Blueprint, current_app, jsonify, request, abort
from sqlalchemy import select, func
from ..db.models import Legislator
from ..config import Config
from ..utils.state_capitals import STATE_CAPITALS
from ..cache import cache
import json, requests

bp = Blueprint("api", __name__)

def serialize_legislator(r: Legislator) -> dict:
    return {
        "govtrack_id": r.govtrack_id,
        "first_name": r.first_name,
        "last_name": r.last_name,
        "birthday": r.birthday.isoformat() if r.birthday else None,
        "gender": r.gender,
        "type": r.type,
        "state": r.state,
        "district": r.district,
        "party": r.party,
        "url": r.url
    }

def _log_extra(d: dict) -> str:
    return json.dumps(d, separators=(",", ":"))

@bp.get("/legislators")
@cache.cached(timeout=120, query_string=True)
def get_legislators():
    """
    List legislators with optional filters and pagination.
    Query params: state, party, type, limit, offset
    """
    from urllib.parse import urlencode

    session = current_app.session_factory()
    state = request.args.get("state")
    party = request.args.get("party")
    type_ = request.args.get("type")

    try:
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        current_app.logger.warning("Bad pagination params", extra={"extra": _log_extra({
            "limit": request.args.get("limit"), "offset": request.args.get("offset")
        })})
        abort(400, description="limit and offset must be integers")

    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    q = select(Legislator)
    if state: q = q.where(Legislator.state == state.upper())
    if party: q = q.where(Legislator.party == party)
    if type_: q = q.where(Legislator.type == type_)

    total = session.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    page_q = q.limit(limit).offset(offset)
    rows = session.execute(page_q).scalars().all()

    current_app.logger.info("Legislators list", extra={"extra": _log_extra({
        "state": state, "party": party, "type": type_, "limit": limit, "offset": offset, "total": total
    })})

    base_url = request.base_url
    params = {k: v for k, v in request.args.items() if k not in {"limit", "offset"}}
    def link(off):
        p = params | {"limit": str(limit), "offset": str(off)}
        return f"{base_url}?{urlencode(p)}"
    next_offset = offset + limit
    prev_offset = max(0, offset - limit)
    payload = {
        "items": [serialize_legislator(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
        "links": {
            "self": link(offset),
            "next": link(next_offset) if next_offset < total else None,
            "prev": link(prev_offset) if offset > 0 else None
        }
    }
    return jsonify(payload)

@bp.get("/legislators/<int:govtrack_id>")
@cache.cached(timeout=300)
def get_legislator(govtrack_id: int):
    session = current_app.session_factory()
    row = session.get(Legislator, govtrack_id)
    if not row:
        current_app.logger.info("Legislator not found", extra={"extra": _log_extra({"govtrack_id": govtrack_id})})
        abort(404, description="Legislator not found")
    current_app.logger.info("Legislator detail", extra={"extra": _log_extra({"govtrack_id": govtrack_id})})
    return jsonify(serialize_legislator(row))

@bp.get("/stats/party")
@cache.cached(timeout=300)
def stats_by_party():
    session = current_app.session_factory()
    q = select(Legislator.party, func.count(Legislator.govtrack_id)).group_by(Legislator.party)
    result = dict(session.execute(q).all())
    result = {(k if k else "Unknown"): v for k, v in result.items()}
    current_app.logger.info("Party stats", extra={"extra": _log_extra({"distinct_parties": len(result)})})
    return jsonify(result)

@bp.get("/legislators/<int:govtrack_id>/weather")
@cache.cached(timeout=300)
def legislator_weather(govtrack_id: int):
    session = current_app.session_factory()
    row = session.get(Legislator, govtrack_id)
    if not row:
        current_app.logger.info("Weather: legislator not found", extra={"extra": _log_extra({"govtrack_id": govtrack_id})})
        abort(404, description="Legislator not found")

    state = row.state.upper()
    capital = STATE_CAPITALS.get(state)
    if not capital:
        current_app.logger.warning("Weather: no capital mapping", extra={"extra": _log_extra({"state": state})})
        abort(400, description=f"No capital mapping for state {state}")

    api_key = Config.OPENWEATHER_API_KEY
    if not api_key:
        current_app.logger.error("Weather API key missing")
        abort(500, description="Weather API key not configured")

    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": f"{capital},US", "appid": api_key, "units": Config.OPENWEATHER_UNITS},
            timeout=10,
        )
        r.raise_for_status()
        weather = r.json()
        current_app.logger.info("Weather fetched", extra={"extra": _log_extra({"state": state, "capital": capital})})
    except requests.RequestException as e:
        current_app.logger.error("Weather fetch failed", extra={"extra": _log_extra({"state": state, "capital": capital, "error": str(e)})})
        abort(502, description="Failed to fetch weather")

    return jsonify({
        "legislator": {
            "govtrack_id": row.govtrack_id,
            "name": f"{row.first_name} {row.last_name}",
            "state": row.state,
            "type": row.type,
            "party": row.party
        },
        "capital_city": capital,
        "weather": weather
    })
