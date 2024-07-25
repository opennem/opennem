""" "
Use unkey to authenticate users and create users
"""

import logging

from opennem.clients.mailgun import send_email_mailgun
from opennem.clients.unkey import unkey_create_key
from opennem.core.templates import serve_template
from opennem.users.ratelimit import OPENNEM_RATELIMIT_ADMIN, OPENNEM_RATELIMIT_USER
from opennem.users.schema import OpenNEMAPIInvite, OpenNEMRoles, OpenNEMUser

logger = logging.getLogger("opennem.users.controller")


async def create_user(email: str, name: str, roles: list[OpenNEMRoles]) -> None | OpenNEMUser:
    """Create a user with unkey"""
    ratelimit = OPENNEM_RATELIMIT_USER

    if "admin" in roles:
        ratelimit = OPENNEM_RATELIMIT_ADMIN

    user_key = await unkey_create_key(email=email, name=name, roles=roles, ratelimit=ratelimit)

    if not user_key:
        logger.error(f"Failed to create user with key for user {name} at {email}")
        return None

    print(f"Created user with key: {user_key.key} and id {user_key.key_id} for user {name} at {email}")

    access_level = "user"
    access_level = "pro" if OpenNEMRoles.pro in roles else "user"
    access_level = "admin" if OpenNEMRoles.admin in roles else "user"

    invite_limit = 100 if OpenNEMRoles.admin in roles else 100
    limit_interval = "second" if OpenNEMRoles.admin in roles else "day"

    invite = OpenNEMAPIInvite(
        name=name,
        api_key=user_key.key,
        access_level=access_level,
        limit=invite_limit,
        limit_interval=limit_interval,
    )

    email_text = serve_template(template_name="api_invite.md", **{"invite": invite})

    await send_email_mailgun(
        to_email=email,
        subject="OpenNEM API Invitation",
        text=email_text,
    )


def user_role_string_to_role(role: str) -> OpenNEMRoles:
    """Convert a string to a role"""
    return OpenNEMRoles(role)


if __name__ == "__main__":
    import argparse
    import asyncio

    # argparse accept user email name and roles (comma separated) as arguments and run create_user
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--roles", required=True)
    args = parser.parse_args()
    roles = args.roles.split(",")
    roles = [OpenNEMRoles(role) for role in roles]
    asyncio.run(create_user(email=args.email, name=args.name, roles=roles))
