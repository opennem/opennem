"""
SDK code samples injected into the OpenAPI spec via `x-codeSamples`.

Snippets are keyed by `(path_template_without_v4_prefix, http_method)` so a
single entry covers both the `/v4/...` and latest (`/...`) mounts. Sources
live in the OE TypeScript and Python SDK repos — see the audit notes in
`/Users/n/.claude/plans/enrich-the-opennem-majestic-steele.md` for line
references.
"""

from typing import TypedDict


class CodeSample(TypedDict):
    lang: str
    label: str
    source: str


# `lang` values follow the OpenAPI x-codeSamples convention used by Tangly,
# Mintlify, ReDoc, Stoplight: lowercase common-name (typescript, python).
_TS_INIT = 'import { OpenElectricityClient } from "openelectricity";\nconst client = new OpenElectricityClient();\n\n'

_PY_INIT_SYNC = "from openelectricity import OEClient\n\n"


def _ts(label: str, body: str) -> CodeSample:
    return {"lang": "typescript", "label": label, "source": _TS_INIT + body}


def _py(label: str, body: str) -> CodeSample:
    return {"lang": "python", "label": label, "source": _PY_INIT_SYNC + body}


CODE_SAMPLES: dict[tuple[str, str], list[CodeSample]] = {
    ("/data/network/{network_code}", "get"): [
        _ts(
            "TypeScript SDK",
            'const { datatable } = await client.getNetworkData("NEM", ["energy"], {\n'
            '  interval: "1h",\n'
            '  dateStart: "2024-01-01T00:00:00",\n'
            '  dateEnd: "2024-01-02T00:00:00",\n'
            '  primaryGrouping: "network_region",\n'
            "});\n",
        ),
        _py(
            "Python SDK",
            "from datetime import datetime\n"
            "from openelectricity.types import DataMetric\n\n"
            "with OEClient() as client:\n"
            "    response = client.get_network_data(\n"
            '        network_code="NEM",\n'
            "        metrics=[DataMetric.ENERGY],\n"
            '        interval="1h",\n'
            "        date_start=datetime(2024, 1, 1),\n"
            "        date_end=datetime(2024, 1, 2),\n"
            '        primary_grouping="network_region",\n'
            "    )\n",
        ),
    ],
    ("/data/facilities/{network_code}", "get"): [
        _ts(
            "TypeScript SDK",
            "const { datatable } = await client.getFacilityData(\n"
            '  "NEM",\n'
            '  ["BANGOWF"],\n'
            '  ["energy", "market_value"],\n'
            "  {\n"
            '    interval: "1d",\n'
            '    dateStart: "2024-01-01T00:00:00",\n'
            '    dateEnd: "2024-02-01T00:00:00",\n'
            "  },\n"
            ");\n",
        ),
        _py(
            "Python SDK",
            "from datetime import datetime\n"
            "from openelectricity.types import DataMetric\n\n"
            "with OEClient() as client:\n"
            "    response = client.get_facility_data(\n"
            '        network_code="NEM",\n'
            '        facility_code=["BANGOWF"],\n'
            "        metrics=[DataMetric.ENERGY, DataMetric.MARKET_VALUE],\n"
            '        interval="1d",\n'
            "        date_start=datetime(2024, 1, 1),\n"
            "        date_end=datetime(2024, 2, 1),\n"
            "    )\n",
        ),
    ],
    ("/market/network/{network_code}", "get"): [
        _ts(
            "TypeScript SDK",
            'const { datatable } = await client.getMarket("NEM", ["price", "demand"], {\n'
            '  interval: "1h",\n'
            '  dateStart: "2024-01-01T00:00:00",\n'
            '  dateEnd: "2024-01-02T00:00:00",\n'
            '  primaryGrouping: "network_region",\n'
            "});\n",
        ),
        _py(
            "Python SDK",
            "from datetime import datetime\n"
            "from openelectricity.types import MarketMetric\n\n"
            "with OEClient() as client:\n"
            "    response = client.get_market(\n"
            '        network_code="NEM",\n'
            "        metrics=[MarketMetric.PRICE, MarketMetric.DEMAND],\n"
            '        interval="1h",\n'
            "        date_start=datetime(2024, 1, 1),\n"
            "        date_end=datetime(2024, 1, 2),\n"
            '        primary_grouping="network_region",\n'
            "    )\n",
        ),
    ],
    ("/facilities/", "get"): [
        _ts(
            "TypeScript SDK",
            "const { table } = await client.getFacilities({\n"
            '  status_id: ["operating"],\n'
            '  fueltech_id: ["coal_black", "solar_utility"],\n'
            '  network_id: ["NEM"],\n'
            '  network_region: "NSW1",\n'
            "});\n",
        ),
        _py(
            "Python SDK",
            "from openelectricity.types import UnitFueltechType, UnitStatusType\n\n"
            "with OEClient() as client:\n"
            "    facilities = client.get_facilities(\n"
            '        network_id=["NEM"],\n'
            "        status_id=[UnitStatusType.OPERATING],\n"
            "        fueltech_id=[UnitFueltechType.SOLAR_UTILITY, UnitFueltechType.WIND],\n"
            '        network_region="NSW1",\n'
            "    )\n",
        ),
    ],
    ("/me", "get"): [
        _ts(
            "TypeScript SDK",
            "const user = await client.getCurrentUser();\n",
        ),
        _py(
            "Python SDK",
            "with OEClient() as client:\n    user = client.get_current_user()\n",
        ),
    ],
    ("/pollution/facilities", "get"): [
        _ts(
            "TypeScript SDK",
            "const { datatable } = await client.getFacilityPollution({\n"
            '  facility_code: ["LIDDELL"],\n'
            '  pollutant_code: ["nox", "so2"],\n'
            '  dateStart: "2023-01-01T00:00:00",\n'
            '  dateEnd: "2024-01-01T00:00:00",\n'
            "});\n",
        ),
        # Python SDK does not yet wrap /pollution/facilities — TS only.
    ],
}


def _normalize_path(path: str) -> str:
    """Strip a leading `/v4` so versioned and latest mounts share one fixture entry."""
    if path.startswith("/v4/"):
        return path[3:]
    if path == "/v4":
        return "/"
    return path


def lookup(path: str, method: str) -> list[CodeSample] | None:
    """Return code samples for a given path + HTTP method, or None if unmapped."""
    return CODE_SAMPLES.get((_normalize_path(path), method.lower()))
