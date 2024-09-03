""" """

from arq.worker import Retry


class OpenNEMPipelineRetryTask(Retry):
    """Raise this exception in a task to retry it with a delay of defer_seconds"""

    def __init__(self):
        defer_seconds = 10  # by default we try again in 10 seconds
        super().__init__(defer=defer_seconds)
