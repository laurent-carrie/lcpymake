import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)

file_handler = RotatingFileHandler(
    "logs/lcpymake.log", maxBytes=10240 * 1024, backupCount=10
)
file_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s " "[in %(pathname)s:%(lineno)d]"
    )
)
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

logger.setLevel(logging.INFO)
logger.info("lcpymake startup")


from lcpymake.world import World  # noqa E402
from lcpymake.rule import Rule  # noqa E$02
