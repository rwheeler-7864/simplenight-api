import hashlib
import logging


class MessageIDFilter(logging.Filter):
    @staticmethod
    def hash(s):
        if s is None:
            return "foo"

        return hashlib.md5(s.encode("utf-8")).hexdigest()

    def filter(self, record):
        try:
            from api.common.request_context import get_request_context
            request_context = get_request_context()
            record.request_id = request_context.get_request_id()[:8]
        except Exception:
            record.request_id = ""

        record.msg_id = self.hash(record.msg)[:6]
        record.filename_lineno = f"{record.filename}:{record.lineno}".ljust(30, ".")
        return True


class CustomHandler(logging.StreamHandler):
    """Prefix every line of logging"""

    def emit(self, record):
        message = record.msg
        if record.args:
            message = message % record.args

        record.args = None
        for line in message.split("\n"):
            record.msg = line
            super().emit(record)
