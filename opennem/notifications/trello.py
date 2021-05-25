"""
OpenNEM Module to add Trello cards to the OpenNEM trello boards


This is used in the feedback API endpoint to automatically create trello cards from
user submissions
"""
import logging
from typing import Optional

from trello import Label as TrelloLabel
from trello import List as TrelloList
from trello import TrelloClient

from opennem.settings import settings

logger = logging.getLogger("opennem.notifications.trello")

FEEDBACK_LABEL_ID = "60abee5feb614882dfd25bcf"


def _get_trello_client() -> TrelloClient:
    tc = TrelloClient(api_key=settings.trello_api_key, api_secret=settings.trello_api_secret)

    return tc


def post_trello_card(subject: str, description: Optional[str] = None) -> bool:
    tc = _get_trello_client()

    feedback_board = tc.get_board(settings.feedback_trello_board_id)

    if not feedback_board:
        logger.error("Could not get trello board id: {}".format(settings.feedback_trello_board_id))
        return False

    website_label_lookup = list(
        filter(lambda x: x.__dict__["id"] == FEEDBACK_LABEL_ID, feedback_board.get_labels())
    )

    if not website_label_lookup:
        logger.error("Could not get website label lookup")
        return False

    website_label: TrelloLabel = website_label_lookup.pop()

    feedback_list_lookup = feedback_board.get_lists("open")

    if not feedback_list_lookup:
        logger.error("Could not get any open lists on the board for trello notification")
        return False

    feedback_list: TrelloList = feedback_list_lookup.pop()

    feedback_list.add_card(subject, desc=description, labels=[website_label])

    return True


# Debug entrypoint
if __name__ == "__main__":
    post_trello_card("test #2", "this is the description\n\nthis *is* _markdown_")
