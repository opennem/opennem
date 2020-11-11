import decimal
import json
from datetime import date, datetime

from geojson import GeoJSONEncoder

from opennem.core.dispatch_type import DispatchType, dispatch_type_string


class OpenNEMJSONEncoder(json.JSONEncoder):
    def default(self, o):
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
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, DispatchType):
            return dispatch_type_string(o)
        return super(OpenNEMGeoJSONEncoder, self).default(o)


def opennem_deserialize(serialized: str) -> any:

    obj_serialized = None

    # try ujson first because it's faster
    # try:
    #     obj_serialized = ujson.loads(serialized)
    # except TypeError:
    #     pass

    # if not obj_serialized:
    obj_serialized = json.loads(serialized, cls=OpenNEMGeoJSONEncoder)

    return obj_serialized


def opennem_serialize(obj: any, indent=None) -> str:
    obj_deserialized = None

    # try ujson first because it's faster
    # try:
    #     obj_deserialized = ujson.dumps(obj, indent=indent)
    # except TypeError:
    #     pass

    if not obj_deserialized:
        obj_deserialized = json.dumps(
            obj, cls=OpenNEMGeoJSONEncoder, indent=indent
        )

    return obj_deserialized
