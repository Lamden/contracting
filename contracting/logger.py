"""Module for initializing settings related to the built-in contracting logger
Functions:
-get_logger"""

import logging, coloredlogs
import os, sys

VALID_LVLS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
_LOG_LVL = os.getenv('LOG_LEVEL', None)
if _LOG_LVL:
    assert _LOG_LVL in VALID_LVLS, "Log level {} not in valid levels {}".format(_LOG_LVL, VALID_LVLS)
    _LOG_LVL = getattr(logging, _LOG_LVL)
else:
    _LOG_LVL = 1

req_log = logging.getLogger('urllib3')
req_log.setLevel(logging.WARNING)
req_log.propagate = True

def get_main_log_path():
    from contracting import logger
    root = logger.__file__  # resolves to '/Users/davishaba/Developer/contracting/contracting/logger/__init__.py'
    log_path = '/'.join(root.split('/')[:-3]) + '/logs/contracting.log'

    # Create log directory if it does not exist
    log_dir = os.path.dirname(log_path)
    try:
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
    except Exception as e:
        print("Possible error creating log file: {}".format(e))

    return log_path


format = '%(asctime)s.%(msecs)03d %(name)s[%(process)d][%(processName)s] <{}> %(levelname)-2s %(message)s'.format(os.getenv('HOST_NAME', 'Node'))

"""
Custom Log Levels
"""
#   Default levels
# 'CRITICAL': 50,
# 'ERROR': 40,
# 'WARNING': 30,
# 'INFO': 20,
# 'DEBUG' : 10


CUSTOM_LVL = {
    'TEST': 14,
    'DEBUG3': 15,
    'DEBUG2': 16,
    'DEBUG1': 17,
    'DEBUGV': 21,
    'NOTICE': 22,
    'FATAL': 99
    }

DEPRECATED_LEVELS = {
    'SPAM': 1,
    'SOCKET': 23,
    'SUCCESS': 26,
    'SUCCESS2': 27,
    'IMPORTANT': 56,
    'IMPORTANT2': 57,
    'IMPORTANT3': 58,

}

CUSTOM_LEVELS = {**CUSTOM_LVL, **DEPRECATED_LEVELS}

for log_name, log_level in CUSTOM_LEVELS.items():
    logging.addLevelName(log_level, log_name)


def apply_custom_level(log, name: str, level: int):
    def _lvl_func(message, *args, **kws):
        if level >= log.getEffectiveLevel():
            log._log(level, message, args, **kws)

    setattr(log, name.lower(), _lvl_func)


"""
Custom Styling
"""

coloredlogs.DEFAULT_LEVEL_STYLES = {
    'fatal': {'color': 'white', 'bold': True, 'background': 'red', 'underline': True},
    'critical': {'color': 'white', 'bold': True, 'background': 'red'},
    'error': {'color': 'red'},
    'warning': {'color': 'yellow'},
    'notice': {'color': 'magenta'},
    'debugv': {'color': 'blue', 'faint': False},
    'info': {'color': 'white'},
    'debug1': {'color': 'cyan', 'bold': True, 'background': 'magenta'},
    'debug2': {'color': 'magenta', 'bold': True, 'background': 'cyan'},
    'debug3': {'color': 'black', 'bold': True, 'background': 'yellow'},
    'debug': {'color': 'green'},
    'test': {'color': 'magenta'},
    'verbose': {'color': 'blue'},

    #TODO deprecated levels to be cleaned up
    'socket': {'color': 'white', 'background': 'yellow'},
    'important': {'color': 'white', 'background': 'yellow'},
    'important2': {'color': 'white', 'background': 'yellow'},
    'important3': {'color': 'white', 'background': 'yellow'},
    'spam': {'color': 'white', 'background': 'yellow'},
    'success': {'color': 'white', 'background': 'yellow'},
    'success2': {'color': 'white', 'background': 'yellow'}
}
coloredlogs.DEFAULT_FIELD_STYLES = {
    'asctime': {'color': 'green'},
    'hostname': {'color': 'magenta'},
    'levelname': {'color': 'black', 'bright': True},
    'name': {'color': 'blue'},
    'programname': {'color': 'cyan'}
}


class LoggerWriter:
    def __init__(self, level):
        self.level = level
    def write(self, message):
        if message != '\n':
            self.level(message)
    def flush(self):
        return


class ColoredFileHandler(logging.FileHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFormatter(
            coloredlogs.ColoredFormatter(format)
        )


class ColoredStreamHandler(logging.StreamHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFormatter(
            coloredlogs.ColoredFormatter(format)
        )


def _ignore(*args, **kwargs):
    pass

class MockLogger:
    def __getattr__(self, item):
        return _ignore


def get_logger(name=''):
    if _LOG_LVL < 0:
        return MockLogger()

    filedir = "logs/{}".format(os.getenv('TEST_NAME', 'test'))
    filename = "{}/{}.log".format(filedir, os.getenv('HOST_NAME', name))

    try:
        if not os.path.isdir(filedir):
            os.makedirs(filedir, exist_ok=True)
    except Exception as e:
        print("Possible error creating log file: {}".format(e))

    filehandlers = [
        logging.FileHandler(get_main_log_path(), delay=True),
        logging.FileHandler(filename, delay=True),
        ColoredFileHandler('{}_color'.format(filename), delay=True),
        ColoredStreamHandler()
    ]
    logging.basicConfig(
        format=format,
        handlers=filehandlers,
        level=logging.DEBUG
    )

    log = logging.getLogger(name)
    log.setLevel(_LOG_LVL)

    if os.getenv('HOST_IP'):
        sys.stdout = LoggerWriter(log.debug)
        sys.stderr = LoggerWriter(log.error)

    for log_name, log_level in CUSTOM_LEVELS.items():
        apply_custom_level(log, log_name, log_level)

    return log


def overwrite_logger_level(level):
    global _LOG_LVL
    _LOG_LVL = level

    for name in logging.Logger.manager.loggerDict.keys():
        log = logging.getLogger(name)
        log.setLevel(level)
