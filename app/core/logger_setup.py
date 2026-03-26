import logging, os
from logging.handlers import RotatingFileHandler 


class AppLoggers:
    db: logging.Logger
    utils: logging.Logger
    bot: logging.Logger

    @classmethod
    def init(cls):
        if not os.path.exists("logs"):
            os.makedirs("logs")

        formatter = logging.Formatter('%(asctime)s - [%(name)s] - %(levelname)s - %(message)s')

        def create_logger(name, filename, level=logging.INFO):
            logger = logging.getLogger(name)
            logger.setLevel(level)

            handler = RotatingFileHandler(
                f"logs/{filename}",
                maxBytes=5*1024*1024,
                backupCount=3,
                encoding='utf-8'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            return logger
        
        cls.db = create_logger("db", 'database.log')
        cls.utils = create_logger("utils", 'utils.log')
        cls.bot = create_logger("bot", 'database.log')
        cls.api = create_logger("api", 'api.log')

AppLoggers.init()
