from typing import Dict, List, Optional, Union

from geojson_pydantic.features import Feature, FeatureCollection
from geojson_pydantic.geometries import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)
from pydantic import BaseModel

Geometry = Union[
    Point, MultiPoint, LineString, MultiLineString, Polygon, MultiPolygon
]


class FacilityGeoBase(BaseModel):
    class Config:
        arbitrary_types_allowed = True


class FacilityGeometryCollection(FacilityGeoBase, GeometryCollection):
    geometries: Optional[List[Geometry]]


class FacilityFeature(Feature):
    """
        Update to default to GeometryCollection
    """

    geometry: Optional[Geometry]


class FacilityGeo(FacilityGeoBase, FeatureCollection):
    name: str = "opennem"
    crs: Optional[Dict]
    features: List[FacilityFeature]

