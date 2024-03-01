"""Utility functions for encoding and decoding data."""

import dataclasses
import json

from pydantic import BaseModel


class EnhancedJSONEncoder(json.JSONEncoder):
    """Json Encoder that can handle dataclasses and pydantic models"""

    def default(self, o: object) -> dict:
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)  # type: ignore

        if isinstance(o, BaseModel):
            return dict(o)

        return super().default(o)
