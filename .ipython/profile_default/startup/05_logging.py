""" iPython logging conveniance methods """
import logging
from typing import List


def get_loggers() -> List[logging.Logger]:
    """List the loggers"""
    return [logging.getLogger(name) for name in logging.root.manager.loggerDict]  # type: ignore
