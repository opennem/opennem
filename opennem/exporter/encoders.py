"""
OpenNEM custom JSON encoders and decoders.

Supporting both regular JSON and extended GeoJSON. This is used by SQLAlchemy to serialize objects
in the data store as well

:see_also: opennem/db/__init__.py
"""
import dataclasses
import decimal
import json
from datetime import date, datetime
from typing import Any, Optional

from geojson import GeoJSONEncoder

from opennem.core.dispatch_type import DispatchType, dispatch_type_string


class OpenNEMJSONEncoder(json.JSONEncoder):
    """JSON encoder that supports decial, datetime and dates"""

    def default(self, o: Any) -> Any:
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, decimal.Decimal):
            return float(o)
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, date):
            return str(o)
        if isinstance(o, DispatchType):
            return dispatch_type_string(o)
        return super(OpenNEMJSONEncoder, self).default(o)


class OpenNEMGeoJSONEncoder(GeoJSONEncoder, OpenNEMJSONEncoder):
    """JSON encoder that also support geojson using the GeoJSONEncoder"""

    def default(self, o: Any) -> Any:
        if isinstance(o, decimal.Decimal):
            return float(o)
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, DispatchType):
            return dispatch_type_string(o)
        return super(OpenNEMGeoJSONEncoder, self).default(o)


def opennem_deserialize(serialized: str) -> Any:
    """Use custom OpenNEM deserializer which supports custom types and GeoJSON

    @TODO This has fallen back onto the standard json.loads as there are bugs in ujson
    and the GeoJSON decoder
    """
    obj_serialized = None

    obj_serialized = json.loads(serialized)

    return obj_serialized


def opennem_serialize(obj: Any, indent: Optional[int] = None) -> str:
    """Use custom OpenNEM serializer which supports custom types and GeoJSON"""
    obj_deserialized = None

    if not obj_deserialized:
        obj_deserialized = json.dumps(obj, cls=OpenNEMGeoJSONEncoder, indent=indent)

    return obj_deserialized
