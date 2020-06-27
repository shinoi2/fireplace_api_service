import logging


def get_logger(name, level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(level)

        formatter = logging.Formatter(
            "[%(name)s.%(module)s:%(lineno)d]: %(message)s",
            datefmt="%H:%M:%M:%S"
        )
        ch.setFormatter(formatter)

        logger.addHandler(ch)

    return logger


log = get_logger('fireplace')
INFO = log.info
WARN = log.warn
ERROR = log.error
DEBUG = log.debug
