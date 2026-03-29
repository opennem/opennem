"""
OpenElectricity Twitter client
"""

import asyncio
import io
import logging

import tweepy
import tweepy.asynchronous

from opennem import settings

twitter_client = tweepy.asynchronous.AsyncClient(
    consumer_key=settings.twitter_api_key,
    consumer_secret=settings.twitter_api_key_secret,
    access_token=settings.twitter_access_token,
    access_token_secret=settings.twitter_access_token_secret,
)

logger = logging.getLogger("opennem.clients.twitter")


async def post_tweet(message: str) -> None:
    """Post a tweet"""

    await twitter_client.create_tweet(text=message)


async def post_tweet_with_image(message: str, image: io.BytesIO, filename: str = "summary.png") -> None:
    """Post a tweet with an image attachment."""
    auth = tweepy.OAuth1UserHandler(
        settings.twitter_api_key,
        settings.twitter_api_key_secret,
        settings.twitter_access_token,
        settings.twitter_access_token_secret,
    )
    api = tweepy.API(auth)

    image.seek(0)
    media = await asyncio.to_thread(api.media_upload, filename=filename, file=image)
    await twitter_client.create_tweet(text=message, media_ids=[media.media_id])


if __name__ == "__main__":
    asyncio.run(
        post_tweet(
            "New records set: \n\n https://openelectricity.org.au/records/au.nem.vic1.battery_discharging.power.interval.high?focusDateTime=2025-04-01T06%3A25%3A00%2B10%3A00"
        )
    )
