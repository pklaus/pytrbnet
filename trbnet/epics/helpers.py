import logging

class SeenBeforeFilter(logging.Filter):
    """
    A filter for the Python logging module rejecting subsequent
    log entries when they have been logged before.
    The optional keyword argument restriction_func can restrict
    the filtering to a subset of messages.
    If present, it will be called with the tuple (module, levelno, msg, args).
    If it evaluates to true, the filtering is done, otherwise not.
    """
    def __init__(self, restriction_func=None):
        self.restriction_func = restriction_func
        self.seen_before = []
        super().__init__()
    def filter(self, record):
        # add other fields if you need more granular comparison, depends on your app
        current_log = (record.module, record.levelno, record.msg, record.args)
        if self.restriction_func:
            if not self.restriction_func(current_log):
                # we do not restrict the filtering to this log entry, 
                # so just log it as usual...
                return True
        if current_log not in self.seen_before:
            self.seen_before.append(current_log)
            return True
        return False

