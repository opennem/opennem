"""
OpenNEM GeoJSON Output Schema

Utiizes the geojson_pydantic package to create the GeoJSON outputs as
pydantic schemas that can be output by the api

Customisation is that our Facility Schemas have optional geometries
rather than required.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic_geojson import (
    # FeatureCollection,
    LineStringModel,
    MultiLineStringModel,
    MultiPointModel,
    MultiPolygonModel,
    PointModel,
    PolygonModel,
)

Geometry = PointModel | MultiPointModel | LineStringModel | MultiLineStringModel | PolygonModel | MultiPolygonModel


class FacilityGeoBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class FacilityFeature(BaseModel):
    """
    Update to default to GeometryCollection
    """

    # @TODO - correct schema for GeoJSON that supports both versions
    bbox: Any | None = None
    properties: Any | None = None
    geometry: Geometry | None = None  # type: ignore


class FacilityGeo(FacilityGeoBase):
    name: str = "opennem"
    crs: dict | None = None
    features: list[FacilityFeature]  # type: ignore
