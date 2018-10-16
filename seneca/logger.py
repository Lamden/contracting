import logging


class SenecaLogger:
    """
    A thin wrapper around Python's base logging class. This class exists so that Seneca can utilize Cilantro's logging
    modules while at the same time have the ability to log stuff when run as a standalone. If the class that uses the
    logger tries to call a log level that only exists in Cilantro (and not Python's core logger), such as log.important,
    it will default to log.info.
    """
    def __init__(self, name):
        self.log = logging.Logger(name)

    def __getattr__(self, item):
        if not hasattr(self.log, item):
            return self.log.info
        else:
            return getattr(self.log, item)


