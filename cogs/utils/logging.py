import logging
import sys


def getLogger(name, level=logging.INFO, file=False):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.FileHandler(filename=f"bot.log", encoding="utf-8", mode="w")
    dt_fmt = "%Y-%m-%d %H:%M:%S"
    fmt = logging.Formatter(
        "[{asctime}] [{levelname}] {name}: {message}", dt_fmt, style="{"
    )
    c_handler = logging.StreamHandler(stream=sys.stdout)
    if file:
        c_handler.setLevel(logging.ERROR)
    c_handler.setFormatter(fmt)
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.addHandler(c_handler)
    return logger