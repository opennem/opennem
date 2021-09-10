"""
OpenNEM GeoJSON Output Schema

Utiizes the geojson_pydantic package to create the GeoJSON outputs as
pydantic schemas that can be output by the api

Customisation is that our Facility Schemas have optional geometries
rather than required.
"""
from typing import Any, Dict, List, Optional, Sequence, Union

from geojson_pydantic.features import FeatureCollection
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

Geometry = Union[Point, MultiPoint, LineString, MultiLineString, Polygon, MultiPolygon]


class FacilityGeoBase(BaseModel):
    class Config:
        arbitrary_types_allowed = True


class FacilityGeometryCollection(FacilityGeoBase, GeometryCollection):
    geometries: List[Geometry]


class FacilityFeature(BaseModel):
    """
    Update to default to GeometryCollection
    """

    # @TODO - correct schema for GeoJSON that supports both versions
    bbox: Optional[Any]
    properties: Optional[Any]
    geometry: Optional[Geometry]  # type: ignore


class FacilityGeo(FacilityGeoBase, FeatureCollection):
    name: str = "opennem"
    crs: Optional[Dict]
    features: Sequence[FacilityFeature]  # type: ignore
