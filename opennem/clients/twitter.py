"""
OpenElectricity Twitter client

Supports two accounts:
- Main (twitter_api_key) — @OpenNem, weekly summaries, general posts
- Records (twitter_records_api_key) — milestone/record posts

All publish functions return a dict: {"platform_post_id": str, "permalink": str}
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


def _get_handle(account: str = "main") -> str:
    """Best-effort handle for permalink construction. Configurable via settings."""
    if account == "records":
        return getattr(settings, "twitter_records_handle", None) or "openelectricity"
    return getattr(settings, "twitter_handle", None) or "OpenNem"


def _get_client(account: str = "main") -> tweepy.asynchronous.AsyncClient:
    """Get an async Twitter client for the specified account."""
    api_key, api_secret, access_token, access_secret = _get_credentials(account)
    return tweepy.asynchronous.AsyncClient(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret,
    )


def _build_result(tweet, account: str) -> dict:
    """Pack a tweepy create_tweet response into our standard dict."""
    tweet_id = None
    try:
        tweet_id = tweet.data["id"] if tweet and tweet.data else None
    except Exception:
        tweet_id = None
    handle = _get_handle(account)
    permalink = f"https://x.com/{handle}/status/{tweet_id}" if tweet_id else None
    return {"platform_post_id": str(tweet_id) if tweet_id else None, "permalink": permalink}


async def post_tweet(message: str, account: str = "main") -> dict:
    """Post a tweet. Returns {platform_post_id, permalink}."""
    client = _get_client(account)
    tweet = await client.create_tweet(text=message)
    return _build_result(tweet, account)


async def post_tweet_with_image(message: str, image: io.BytesIO, filename: str = "summary.png", account: str = "main") -> dict:
    """Post a tweet with an image attachment. Returns {platform_post_id, permalink}."""
    api_key, api_secret, access_token, access_secret = _get_credentials(account)

    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
    api = tweepy.API(auth)

    image.seek(0)
    media = await asyncio.to_thread(api.media_upload, filename=filename, file=image)

    client = _get_client(account)
    tweet = await client.create_tweet(text=message, media_ids=[media.media_id])
    return _build_result(tweet, account)


async def post_tweet_reply(message: str, in_reply_to_tweet_id: str, account: str = "main") -> dict:
    """Post a tweet as a reply to another tweet. Returns {platform_post_id, permalink}."""
    client = _get_client(account)
    tweet = await client.create_tweet(text=message, in_reply_to_tweet_id=in_reply_to_tweet_id)
    return _build_result(tweet, account)


if __name__ == "__main__":
    asyncio.run(post_tweet("Test post from OpenElectricity"))
