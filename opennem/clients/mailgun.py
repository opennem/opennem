"""Sends email using mailgun"""

import asyncio
import logging

import httpx

from opennem import settings

MAIL_DOMAIN = "mail.opennem.org.au"

logger = logging.getLogger("opennem.clients.mail")


async def send_email_mailgun(to_email: str, subject: str, text: str, from_email: str = "developers@opennem.org.au"):
    # Set the API endpoint URL
    url = f"https://api.mailgun.net/v3/{MAIL_DOMAIN}/messages"

    if not settings.mailgun_api_key:
        raise Exception("mailgun api key not set")

    # Set the authentication credentials
    auth = ("api", settings.mailgun_api_key)

    # Set the request payload
    data = {"from": from_email, "to": to_email, "subject": subject, "text": text}

    async with httpx.AsyncClient() as client:
        # Send the POST request to the Mailgun API
        response = await client.post(url, auth=auth, data=data)

    logger.debug(f"Mailgun response: {response.status_code} {response.text}")

    # Check the response status code
    if response.status_code == 200:
        return True

    raise Exception(f"Error sending email: {response.text}")


async def main():
    r = await send_email_mailgun(to_email="nik@nikcub.me", subject="test opennem", text="test opennem")
    print(r)


if __name__ == "__main__":
    asyncio.run(main())
