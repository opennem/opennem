import logging


def setup_root_logger() -> None:
    # Setup logging - root logger and handlers
    __root_logger = logging.getLogger()
    __root_logger.setLevel(logging.INFO)
    __root_logger_formatter = logging.Formatter(fmt=" * %(message)s")
    num_handlers = len(__root_logger.handlers)

    if num_handlers == 0:
        __root_logger.addHandler(logging.StreamHandler())

    __root_logger.handlers[0].setFormatter(__root_logger_formatter)
    __root_logger.handlers[0].setFormatter(__root_logger_formatter)
