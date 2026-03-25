import logging, os

def setup_logging():
    if not os.path.exists("logs"):
        os.makedirs('logs')

    formatter = logging.Formatter('%(asctime)s - [%(name)s] - %(levelname)s - %(message)s')

    db_logger = logging.getLogger("db")
    db_logger.setLevel(logging.INFO)
    db_handler = logging.FileHandler("logs/database.log", encoding='utf-8')
    db_handler.setFormatter(formatter)
    db_logger.addHandler(db_handler)

    utils_logger = logging.getLogger("utils")
    utils_logger.setLevel(logging.INFO)
    utils_handler = logging.FileHandler("logs/utils.log", encoding='utf-8')
    utils_handler.setFormatter(formatter)
    utils_logger.addHandler(utils_handler)


setup_logging()