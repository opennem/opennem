"""
Tests for the OpenAPI enrichment scaffolding:
- APIV4ResponseSchema generic envelope
- std_error_responses() helper
- code_samples lookup + path normalization
- custom_openapi() x-codeSamples injection

These tests are pure unit tests against the OE schema and OpenAPI helpers —
no DB, no auth, no FastAPI lifecycle setup. They intentionally avoid the
TestClient since the wider api test fixtures depend on services these tests
do not need.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from opennem.api.code_samples import CODE_SAMPLES, _normalize_path, lookup
from opennem.api.openapi_extra import custom_openapi
from opennem.api.schema import APIV4ResponseSchema, std_error_responses

# ---------------------------------------------------------------------------
# APIV4ResponseSchema generic envelope
# ---------------------------------------------------------------------------


class _Item(BaseModel):
    name: str
    value: int


class TestAPIV4ResponseSchemaEnvelope:
    """Round-trip behaviour of the generic envelope."""

    def test_unparametrized_default_is_empty_list(self) -> None:
        """T defaults to list (PEP 696). data defaults to []."""
        r = APIV4ResponseSchema()
        assert r.data == []
        assert r.success is True
        assert r.error is None
        assert r.total_records is None

    def test_unparametrized_accepts_list_payload(self) -> None:
        r = APIV4ResponseSchema(data=[1, 2, 3])
        assert r.data == [1, 2, 3]

    def test_parametrized_typed_payload(self) -> None:
        items = [_Item(name="a", value=1), _Item(name="b", value=2)]
        r = APIV4ResponseSchema[list[_Item]](data=items)
        assert len(r.data) == 2
        assert r.data[0].name == "a"

    def test_parametrized_validates_item_type(self) -> None:
        with pytest.raises(ValidationError):
            APIV4ResponseSchema[list[_Item]](data=[{"name": "a"}])  # missing `value`

    def test_subclass_override_keeps_required_field(self) -> None:
        """Subclass overrides `data` with concrete required type — pre-existing pattern."""

        class UserResp(APIV4ResponseSchema):
            data: _Item  # type: ignore[assignment]  # intentional override

        with pytest.raises(ValidationError):
            UserResp()  # data required, no default
        u = UserResp(data=_Item(name="x", value=1))
        assert u.data.value == 1

    def test_error_state_serialization(self) -> None:
        r = APIV4ResponseSchema(success=False, error="boom", total_records=0)
        dumped = r.model_dump()
        assert dumped["success"] is False
        assert dumped["error"] == "boom"
        assert dumped["data"] == []
        assert dumped["total_records"] == 0


# ---------------------------------------------------------------------------
# std_error_responses() helper
# ---------------------------------------------------------------------------


class TestStdErrorResponses:
    def test_default_includes_all_codes(self) -> None:
        r = std_error_responses()
        assert set(r.keys()) == {400, 401, 404, 429, 500}
        for code in r:
            assert "model" in r[code]
            assert "description" in r[code]
            assert isinstance(r[code]["description"], str)

    def test_exclude_404(self) -> None:
        r = std_error_responses(include_404=False)
        assert 404 not in r
        assert {400, 401, 429, 500} <= set(r.keys())

    def test_exclude_429(self) -> None:
        r = std_error_responses(include_429=False)
        assert 429 not in r

    def test_returns_a_fresh_dict(self) -> None:
        """Mutating the returned dict must not affect future calls."""
        r1 = std_error_responses()
        r1[418] = {"model": None, "description": "tea"}
        r2 = std_error_responses()
        assert 418 not in r2


# ---------------------------------------------------------------------------
# code_samples — _normalize_path + lookup
# ---------------------------------------------------------------------------


class TestNormalizePath:
    def test_strips_v4_prefix(self) -> None:
        assert _normalize_path("/v4/data/network/{network_code}") == "/data/network/{network_code}"

    def test_passes_through_unprefixed(self) -> None:
        assert _normalize_path("/data/network/{network_code}") == "/data/network/{network_code}"

    def test_root_v4_becomes_root(self) -> None:
        assert _normalize_path("/v4") == "/"

    def test_does_not_strip_v40(self) -> None:
        """`/v40/...` must not have `/v4` chopped off the front."""
        # _normalize_path checks for prefix `/v4/` (with trailing slash) — so /v40/x
        # passes through. Verifies the matcher isn't overly greedy.
        assert _normalize_path("/v40/foo") == "/v40/foo"


class TestLookup:
    def test_known_endpoint_v4_path(self) -> None:
        samples = lookup("/v4/data/network/{network_code}", "get")
        assert samples is not None
        assert {s["lang"] for s in samples} == {"typescript", "python"}

    def test_known_endpoint_latest_path(self) -> None:
        """Latest mount (no /v4 prefix) shares the same fixture entry."""
        samples = lookup("/data/network/{network_code}", "get")
        assert samples is not None
        assert len(samples) == 2

    def test_method_is_case_insensitive(self) -> None:
        a = lookup("/v4/me", "GET")
        b = lookup("/v4/me", "get")
        assert a is not None
        assert a == b

    def test_unknown_path_returns_none(self) -> None:
        assert lookup("/v4/no-such-endpoint", "get") is None

    def test_unknown_method_returns_none(self) -> None:
        assert lookup("/v4/data/network/{network_code}", "post") is None

    def test_pollution_endpoint_is_typescript_only(self) -> None:
        """Python SDK doesn't yet wrap /pollution/facilities — TS-only entry."""
        samples = lookup("/v4/pollution/facilities", "get")
        assert samples is not None
        assert {s["lang"] for s in samples} == {"typescript"}

    def test_every_fixture_entry_has_required_keys(self) -> None:
        for (path, method), samples in CODE_SAMPLES.items():
            assert path.startswith("/"), path
            assert method in ("get", "post", "put", "patch", "delete"), method
            assert samples, f"{path} {method}: samples must not be empty"
            for s in samples:
                assert s["lang"] in ("typescript", "python"), s
                assert s["label"], s
                assert s["source"].strip(), s

    def test_no_real_secrets_in_samples(self) -> None:
        """Defense-in-depth — the spec ships these snippets to consumers."""
        forbidden = ("sk_live_", "sk_test_", "pk_live_", "Bearer eyJ", "OE_API_KEY=")
        for samples in CODE_SAMPLES.values():
            for s in samples:
                for needle in forbidden:
                    assert needle not in s["source"], f"{needle} leaked into {s['label']}"


# ---------------------------------------------------------------------------
# custom_openapi() injection
# ---------------------------------------------------------------------------


class TestCustomOpenAPI:
    """End-to-end: build the spec from the live app and assert injections."""

    @pytest.fixture(scope="class")
    def spec(self) -> dict:
        # Reset the cache so the test sees a fresh build.
        from opennem.api.app import app

        app.openapi_schema = None
        return custom_openapi(app)

    def test_spec_has_paths(self, spec: dict) -> None:
        assert "paths" in spec
        assert len(spec["paths"]) > 0

    def test_injects_x_code_samples_on_known_endpoint(self, spec: dict) -> None:
        op = spec["paths"]["/v4/data/network/{network_code}"]["get"]
        assert "x-codeSamples" in op
        langs = {s["lang"] for s in op["x-codeSamples"]}
        assert langs == {"typescript", "python"}

    def test_skips_unknown_endpoints(self, spec: dict) -> None:
        # `/health` is a tiny route that has no samples — must not be injected.
        if "/health" in spec["paths"]:
            assert "x-codeSamples" not in spec["paths"]["/health"].get("get", {})

    def test_caches_on_app(self) -> None:
        from opennem.api.app import app

        app.openapi_schema = None
        first = custom_openapi(app)
        second = custom_openapi(app)
        assert first is second  # same dict instance — cache hit

    def test_envelope_schema_present_in_components(self, spec: dict) -> None:
        # The generic envelope renders as `APIV4ResponseSchema_list_<X>__` per
        # parametrization — verify at least one parametrized form exists.
        schemas = spec.get("components", {}).get("schemas", {})
        parametrized = [n for n in schemas if n.startswith("APIV4ResponseSchema")]
        assert parametrized, "expected at least one APIV4ResponseSchema variant in components"
