"""
GitHub Client
"""
import logging

from github import Github

from opennem.settings import settings

logger = logging.getLogger("opennem.clients.github")


class GithubClientException(Exception):
    pass


def post_github_issue(title: str, body: str | None = None) -> bool:
    """ """

    if not settings.github_feedback_access_token:
        raise GithubClientException("No github access token")

    client = Github(settings.github_feedback_access_token)

    # @NOTE
    repo = client.get_repo("opennem/opennem")

    if not repo:
        raise GithubClientException("Could not get repo")

    label = repo.get_label("feedback")

    if not label:
        raise GithubClientException("Could not get label")

    try:
        repo.create_issue(title=title, labels=[label], assignee="nc9", body=body or "")
    except Exception as e:
        logger.error(e)
        return False

    return True


if __name__ == "__main__":
    post_github_issue(title="test", body="# test body\n\ntest body")
