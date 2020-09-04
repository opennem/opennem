import decimal
import json
from datetime import datetime

from geojson import GeoJSONEncoder
from opennem.core.dispatch_type import DispatchType, dispatch_type_string


class OpenNEMJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        if isinstance(o, datetime):
            return o.isoformat()
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
