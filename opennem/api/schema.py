from datetime import datetime
from typing import Annotated, Any, Generic

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import TypeVar

from opennem.schema.network import NetworkAU, NetworkNEM, NetworkWEM
from opennem.schema.opennem import OpennemErrorSchema
from opennem.utils.dates import get_today_opennem
from opennem.utils.version import get_version

# typing_extensions.TypeVar supports PEP 696 default= on Python <3.13
T = TypeVar("T", default=list)


def std_error_responses(*, include_404: bool = True, include_429: bool = True) -> dict[int | str, dict[str, Any]]:
    """Return the canonical 4xx/5xx response shape for OpenAPI spec generation.

    All error paths return `OpennemErrorSchema`. Routes pass the result of
    this helper to FastAPI's `responses=` decorator argument; merge in
    route-specific overrides as needed.
    """
    out: dict[int | str, dict[str, Any]] = {
        400: {"model": OpennemErrorSchema, "description": "Invalid request — see `error` for details."},
        401: {"model": OpennemErrorSchema, "description": "Missing or invalid API key."},
        500: {"model": OpennemErrorSchema, "description": "Server error while handling the request."},
    }
    if include_404:
        out[404] = {"model": OpennemErrorSchema, "description": "No matching records for the requested filters."}
    if include_429:
        out[429] = {"model": OpennemErrorSchema, "description": "Rate limit exceeded — back off and retry."}
    return out


class ApiBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        use_enum_values=True,
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )


class UpdateResponse(BaseModel):
    success: bool = True
    records: list = []


class FueltechResponse(ApiBase):
    success: bool = True

    # @TODO fix circular references
    # records: List[FueltechSchema]


class APINetworkRegion(ApiBase):
    code: str
    timezone: str | None = None


class APINetworkSchema(ApiBase):
    code: str
    country: str
    label: str

    regions: list[APINetworkRegion] | None = None
    timezone: str | None = Field(None, description="Network timezone")
    interval_size: int = Field(..., description="Size of network interval in minutes")


class APIV4ResponseSchema(ApiBase, Generic[T]):
    version: str = Field(
        default_factory=get_version,
        description="OpenElectricity API version that produced this response.",
        examples=["4.5.0"],
    )
    created_at: datetime = Field(
        default_factory=get_today_opennem,
        description="UTC timestamp when this response was produced.",
        examples=["2024-09-01T00:00:00Z"],
    )
    success: Annotated[
        bool,
        Field(
            description="`true` if the request succeeded. Errors set this to `false` and populate `error`.",
            examples=[True],
        ),
    ] = True
    error: Annotated[
        str | None,
        Field(
            description="Human-readable error message when `success` is `false`. `null` on success.",
            examples=[None],
        ),
    ] = None
    data: T = Field(  # type: ignore[assignment]  # T defaults to list via PEP 696
        default_factory=list,
        description="Response payload. Shape depends on the endpoint — see the endpoint's response schema.",
    )
    total_records: Annotated[
        int | None,
        Field(
            description="Total number of records in `data` when paginated; `null` when not applicable.",
            examples=[42],
        ),
    ] = None


API_SUPPORTED_NETWORKS = {
    "NEM": NetworkNEM,
    "WEM": NetworkWEM,
    "AU": NetworkAU,
}
