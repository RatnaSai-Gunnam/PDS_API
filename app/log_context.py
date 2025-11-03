import logging
from flask import g, request

class RequestContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(g, "request_id", "")
        record.path = getattr(request, "path", "")
        record.method = getattr(request, "method", "")
        if not hasattr(record, "extra"):
            record.extra = "{}"
        if not hasattr(record, "status"):
            record.status = ""
        return True
