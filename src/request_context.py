from queue import Queue
import contextvars


class RequestContext:
    def __init__(self):
        self.prompt = ""
        self.message_queue = Queue()
        self.timezone = ""


context_var = contextvars.ContextVar("request_context")
