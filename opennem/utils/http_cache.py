import json
from typing import Any

from fastapi_cache.coder import Coder

from opennem.exporter.encoders import OpenNEMJSONEncoder


class PydanticCoder(Coder):
    @classmethod
    def encode(cls, value: Any) -> str:
        return json.dumps(value, cls=OpenNEMJSONEncoder)

    @classmethod
    def decode(cls, value: Any) -> Any:
        return json.loads(value, cls=OpenNEMJSONEncoder)
