"""
OpenNEM GeoJSON Output Schema

Utiizes the geojson_pydantic package to create the GeoJSON outputs as
pydantic schemas that can be output by the api

Customisation is that our Facility Schemas have optional geometries
rather than required.
"""
from collections.abc import Sequence
from typing import Any

from geojson_pydantic.features import FeatureCollection
from geojson_pydantic.geometries import GeometryCollection, LineString, MultiLineString, MultiPoint, MultiPolygon, Point, Polygon
from pydantic import BaseModel

Geometry = Point | MultiPoint | LineString | MultiLineString | Polygon | MultiPolygon


class FacilityGeoBase(BaseModel):
    class Config:
        arbitrary_types_allowed = True


class FacilityGeometryCollection(FacilityGeoBase, GeometryCollection):
    geometries: list[Geometry]


class FacilityFeature(BaseModel):
    """
    Update to default to GeometryCollection
    """

    # @TODO - correct schema for GeoJSON that supports both versions
    bbox: Any | None
    properties: Any | None
    geometry: Geometry | None  # type: ignore


class FacilityGeo(FacilityGeoBase, FeatureCollection):
    name: str = "opennem"
    crs: dict | None
    features: Sequence[FacilityFeature]  # type: ignore
