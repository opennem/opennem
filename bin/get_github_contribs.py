#!/usr/bin/env python
"""
Get a list of people who have submitted or commented on an issue in the OpenNEM github repository

"""
import json
import logging
import os
from csv import DictWriter
from pathlib import Path

from github import Github
from pydantic import BaseModel

logger = logging.getLogger("opennem.get_github_contribs")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", None)


class OpenNemContributor(BaseModel):
    name: str | None = None
    username: str | None = None
    company: str | None = None
    website: str | None = None
    email: str | None = None
    profile_url: str | None = None


def get_github_issue_contributors() -> list[OpenNemContributor]:
    """get a list of users who have commented on or submitted an issue"""

    if not GITHUB_TOKEN:
        raise Exception("Could not get GitHub token")

    gh = Github(GITHUB_TOKEN)

    gh.get_organization("opennem")

    records: list[OpenNemContributor] = []

    for issue in gh.get_repo("opennem/opennem").get_issues():
        logger.info(f"Reading issue {issue.id}")

        # get issue comments
        for comment in issue.get_comments():
            existing_comment_user = list(filter(lambda x: x.username == comment.user.login, records))

            if existing_comment_user:
                continue

            user_model = OpenNemContributor(
                name=comment.user.name,
                username=comment.user.login,
                company=comment.user.company,
                website=comment.user.url,
                email=comment.user.email,
                profile_url=comment.user.html_url,
            )

            records.append(user_model)

        # check issue author
        existing_user = list(filter(lambda x: x.username == issue.user.login, records))

        if existing_user:
            continue

        user_model = OpenNemContributor(
            name=issue.user.name,
            username=issue.user.login,
            company=issue.user.company,
            website=issue.user.url,
            email=issue.user.email,
            profile_url=issue.user.html_url,
        )

        records.append(user_model)

    return records


if __name__ == "__main__":
    users = get_github_issue_contributors()

    users_as_dicts = [i.model_dump() for i in users]

    logger.info(f"Got {len(users)} users")

    json_path = Path("github_users.json")

    with json_path.open("w+") as fh:
        json.dump(users_as_dicts, fh)

    save_path = Path("github_users.csv")

    with save_path.open("w+") as fh:
        csv = DictWriter(fh, fieldnames=["name", "username", "company", "website", "email", "profile_url"])
        csv.writeheader()
        for u in users:
            csv.writerow(u.model_dump())
