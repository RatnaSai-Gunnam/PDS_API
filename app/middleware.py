
import uuid
from flask import g, request
REQUEST_ID_HEADER = "X-Request-ID"
def request_id_middleware(app):
    @app.before_request
    def _assign_request_id():
        rid = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        g.request_id = rid
    @app.after_request
    def _attach_request_id(resp):
        rid = getattr(g, "request_id", None)
        if rid:
            resp.headers[REQUEST_ID_HEADER] = rid
        return resp
