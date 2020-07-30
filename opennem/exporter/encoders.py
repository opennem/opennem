import decimal
import json
from datetime import datetime

from geojson import GeoJSONEncoder


class OpenNEMGeoJSONEncoder(GeoJSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super(OpenNEMGeoJSONEncoder, self).default(o)
