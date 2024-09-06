"""Clients for AI services"""

import openai

from opennem import settings

if not settings.openai_api_key:
    raise ValueError("OpenAI API key not set")

openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)


def get_openai_client() -> openai.AsyncOpenAI:
    """Get the OpenAI client"""
    return openai_client
