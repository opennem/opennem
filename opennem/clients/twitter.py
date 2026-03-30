"""
OpenElectricity Twitter client

Supports two accounts:
- Main (twitter_api_key) — @OpenNem, weekly summaries, general posts
- Records (twitter_records_api_key) — milestone/record posts
"""

import asyncio
import io
import logging

import tweepy
import tweepy.asynchronous

from opennem import settings

logger = logging.getLogger("opennem.clients.twitter")


def _get_credentials(account: str = "main") -> tuple[str | None, str | None, str | None, str | None]:
    """Get Twitter credentials for the specified account."""
    if account == "records":
        return (
            settings.twitter_records_api_key,
            settings.twitter_records_api_key_secret,
            settings.twitter_records_access_token,
            settings.twitter_records_access_token_secret,
        )
    return (
        settings.twitter_api_key,
        settings.twitter_api_key_secret,
        settings.twitter_access_token,
        settings.twitter_access_token_secret,
    )


def _get_client(account: str = "main") -> tweepy.asynchronous.AsyncClient:
    """Get an async Twitter client for the specified account."""
    api_key, api_secret, access_token, access_secret = _get_credentials(account)
    return tweepy.asynchronous.AsyncClient(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret,
    )


async def post_tweet(message: str, account: str = "main") -> None:
    """Post a tweet."""
    client = _get_client(account)
    await client.create_tweet(text=message)


async def post_tweet_with_image(message: str, image: io.BytesIO, filename: str = "summary.png", account: str = "main") -> None:
    """Post a tweet with an image attachment."""
    api_key, api_secret, access_token, access_secret = _get_credentials(account)

    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
    api = tweepy.API(auth)

    image.seek(0)
    media = await asyncio.to_thread(api.media_upload, filename=filename, file=image)

    client = _get_client(account)
    await client.create_tweet(text=message, media_ids=[media.media_id])


if __name__ == "__main__":
    asyncio.run(post_tweet("Test post from OpenElectricity"))
