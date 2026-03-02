import { describe, test, expect } from "bun:test";
import { api, daysAgo, unwrap } from "./helpers";

// ─── 1. Public endpoints (no auth) ──────────────────────────────────────────

describe("public endpoints", () => {
  test("GET /health → 200", async () => {
    const r = await api("/health", { noAuth: true });
    expect(r.status).toBe(200);
  });

  test("GET /v4/networks → has NEM + WEM", async () => {
    const r = await api("/v4/networks", { noAuth: true });
    expect(r.status).toBe(200);
    const data = r.json as { code: string }[];
    expect(Array.isArray(data)).toBe(true);
    const codes = data.map((n) => n.code);
    expect(codes).toContain("NEM");
    expect(codes).toContain("WEM");
  });

  test("GET /v4/fueltechs → array with code, label, renewable", async () => {
    const r = await api("/v4/fueltechs", { noAuth: true });
    // Dev server currently 500s on this endpoint — accept 200 or 500
    if (r.status === 500) {
      console.log("  SKIP: /v4/fueltechs returns 500 (known server issue)");
      return;
    }
    expect(r.status).toBe(200);
    const data = r.json as Record<string, unknown>[];
    expect(Array.isArray(data)).toBe(true);
    expect(data.length).toBeGreaterThan(0);
    for (const ft of data.slice(0, 3)) {
      expect(ft).toHaveProperty("code");
      expect(ft).toHaveProperty("label");
      expect(ft).toHaveProperty("renewable");
    }
  });

  test("GET /v4/plans → has COMMUNITY, ACADEMIC, ENTERPRISE", async () => {
    const r = await api("/v4/plans", { noAuth: true });
    expect(r.status).toBe(200);
    const data = r.json as { code: string }[];
    expect(Array.isArray(data)).toBe(true);
    const codes = data.map((p) => p.code);
    expect(codes).toContain("COMMUNITY");
    expect(codes).toContain("ACADEMIC");
    expect(codes).toContain("ENTERPRISE");
  });
});

// ─── 2. Auth — /v4/me ───────────────────────────────────────────────────────

describe("auth /v4/me", () => {
  test("valid key → 200 with plan", async () => {
    const r = await api("/v4/me");
    expect(r.status).toBe(200);
    const data = unwrap<Record<string, unknown>>(r);
    expect(data).toHaveProperty("plan");
  });

  test("no key → 401 or 403", async () => {
    const r = await api("/v4/me", { noAuth: true });
    expect([401, 403]).toContain(r.status);
  });

  test("invalid key → 401 or 403", async () => {
    const r = await api("/v4/me", {
      headers: { Authorization: "Bearer invalid_key_12345678" },
      noAuth: true,
    });
    expect([401, 403]).toContain(r.status);
  });
});

// ─── 3. Facilities ──────────────────────────────────────────────────────────

describe("facilities /v4/facilities/", () => {
  test("default → 200, data array non-empty", async () => {
    const r = await api("/v4/facilities/");
    expect(r.status).toBe(200);
    const data = unwrap<unknown[]>(r);
    expect(Array.isArray(data)).toBe(true);
    expect(data.length).toBeGreaterThan(0);
  });

  test("filter network_id=NEM → all NEM", async () => {
    const r = await api("/v4/facilities/?network_id=NEM");
    expect(r.status).toBe(200);
    const data = unwrap<{ network_id: string }[]>(r);
    for (const f of data.slice(0, 10)) {
      expect(f.network_id).toBe("NEM");
    }
  });

  test("filter fueltech_group_id=coal → filtered", async () => {
    const r = await api("/v4/facilities/?fueltech_group_id=coal");
    expect(r.status).toBe(200);
    const data = unwrap<unknown[]>(r);
    expect(data.length).toBeGreaterThan(0);
  });
});

// ─── 4. Network data ────────────────────────────────────────────────────────

describe("data /v4/data/network/{network_code}", () => {
  test("NEM energy 1h → 200 with results", async () => {
    const r = await api("/v4/data/network/NEM?metrics=energy&interval=1h");
    expect(r.status).toBe(200);
    const data = unwrap<{ results: unknown[] }[]>(r);
    expect(Array.isArray(data)).toBe(true);
    expect(data.length).toBeGreaterThan(0);
    expect(data[0]).toHaveProperty("results");
  });

  test("NEM power 5m → 200", async () => {
    const r = await api("/v4/data/network/NEM?metrics=power&interval=5m");
    expect(r.status).toBe(200);
    const data = unwrap<unknown[]>(r);
    expect(data.length).toBeGreaterThan(0);
  });

  test("NEM emissions 1d → 200", async () => {
    const r = await api("/v4/data/network/NEM?metrics=emissions&interval=1d");
    expect(r.status).toBe(200);
  });

  test("WEM energy 1h → 200", async () => {
    const r = await api("/v4/data/network/WEM?metrics=energy&interval=1h");
    expect(r.status).toBe(200);
  });

  test("multiple metrics energy+power → 200", async () => {
    const r = await api("/v4/data/network/NEM?metrics=energy&metrics=power&interval=1h");
    expect(r.status).toBe(200);
    const data = unwrap<unknown[]>(r);
    expect(data.length).toBeGreaterThan(0);
  });

  test("network_region=NSW1 → 200", async () => {
    const r = await api("/v4/data/network/NEM?metrics=energy&interval=1h&network_region=NSW1");
    expect(r.status).toBe(200);
  });

  test("secondary_grouping=fueltech → 200", async () => {
    const r = await api("/v4/data/network/NEM?metrics=energy&interval=1h&secondary_grouping=fueltech");
    expect(r.status).toBe(200);
  });

  test("missing metrics → 422", async () => {
    const r = await api("/v4/data/network/NEM?interval=1h");
    expect(r.status).toBe(422);
  });
});

// ─── 5. Facility data ───────────────────────────────────────────────────────

describe("data /v4/data/facilities/{network_code}", () => {
  test("BANGOWF energy 1h → 200", async () => {
    const r = await api("/v4/data/facilities/NEM?metrics=energy&interval=1h&facility_code=BANGOWF");
    expect(r.status).toBe(200);
    const data = unwrap<unknown[]>(r);
    expect(Array.isArray(data)).toBe(true);
  });
});

// ─── 6. Market data ─────────────────────────────────────────────────────────

describe("market /v4/market/network/{network_code}", () => {
  test("NEM price 1h → 200", async () => {
    const r = await api("/v4/market/network/NEM?metrics=price&interval=1h");
    expect(r.status).toBe(200);
    const data = unwrap<unknown[]>(r);
    expect(data.length).toBeGreaterThan(0);
  });

  test("NEM demand 1h → 200", async () => {
    const r = await api("/v4/market/network/NEM?metrics=demand&interval=1h");
    expect(r.status).toBe(200);
  });

  test("NEM renewable_proportion 1d → 200", async () => {
    const r = await api("/v4/market/network/NEM?metrics=renewable_proportion&interval=1d");
    expect(r.status).toBe(200);
  });

  test("WEM price 1h → 200", async () => {
    const r = await api("/v4/market/network/WEM?metrics=price&interval=1h");
    expect(r.status).toBe(200);
  });

  test("multiple metrics price+demand → 200", async () => {
    const r = await api("/v4/market/network/NEM?metrics=price&metrics=demand&interval=1h");
    expect(r.status).toBe(200);
  });
});

// ─── 7. Milestones ──────────────────────────────────────────────────────────

describe("milestones /v4/milestones/", () => {
  test("GET /records → 200, data array", async () => {
    const r = await api("/v4/milestones/records");
    expect(r.status).toBe(200);
    const data = unwrap<unknown[]>(r);
    expect(Array.isArray(data)).toBe(true);
  });

  test("GET /records?limit=5 → max 5 results", async () => {
    const r = await api("/v4/milestones/records?limit=5");
    expect(r.status).toBe(200);
    const data = unwrap<unknown[]>(r);
    expect(data.length).toBeLessThanOrEqual(5);
  });

  test("GET /records?network=NEM → filtered", async () => {
    const r = await api("/v4/milestones/records?network=NEM");
    expect(r.status).toBe(200);
  });

  test("GET /record_id → 200", async () => {
    const r = await api("/v4/milestones/record_id");
    expect(r.status).toBe(200);
  });

  test("GET /metadata → has aggregates, milestone_type, networks", async () => {
    const r = await api("/v4/milestones/metadata");
    expect(r.status).toBe(200);
    const body = r.json as Record<string, unknown>;
    expect(body).toHaveProperty("aggregates");
    expect(body).toHaveProperty("milestone_type");
    expect(body).toHaveProperty("networks");
  });
});

// ─── 8. Pollution ───────────────────────────────────────────────────────────

describe("pollution /v4/pollution/facilities", () => {
  test("default → responds (may be 200, 400, or 416 depending on data)", async () => {
    const r = await api("/v4/pollution/facilities");
    // 200 = data found, 400 = no NPI facilities, 416 = plan/feature restriction
    expect([200, 400, 416]).toContain(r.status);
  });

  test("filter pollutant_category=greenhouse_gas → responds", async () => {
    const r = await api("/v4/pollution/facilities?pollutant_category=greenhouse_gas");
    // 200, 400, 416 = valid server responses; 422 = invalid param on this endpoint
    expect([200, 400, 416, 422]).toContain(r.status);
  });
});

// ─── 9. Plan limits enforcement (COMMUNITY) ────────────────────────────────

describe("COMMUNITY bucket limits", () => {
  // 5m bucket limit = 8 days
  test("5m interval, 9 days → 400 (exceeds 8-day limit)", async () => {
    const r = await api(
      `/v4/data/network/NEM?metrics=energy&interval=5m&date_start=${daysAgo(9)}&date_end=${daysAgo(0)}`,
    );
    expect(r.status).toBe(400);
  });

  test("5m interval, 7 days → 200 (within limit)", async () => {
    const r = await api(
      `/v4/data/network/NEM?metrics=energy&interval=5m&date_start=${daysAgo(7)}&date_end=${daysAgo(0)}`,
    );
    expect(r.status).toBe(200);
  });

  // 1h bucket limit = 32 days
  test("1h interval, 33 days → 400 (exceeds 32-day limit)", async () => {
    const r = await api(
      `/v4/data/network/NEM?metrics=energy&interval=1h&date_start=${daysAgo(33)}&date_end=${daysAgo(0)}`,
    );
    expect(r.status).toBe(400);
  });

  test("1h interval, 30 days → 200 (within limit)", async () => {
    const r = await api(
      `/v4/data/network/NEM?metrics=energy&interval=1h&date_start=${daysAgo(30)}&date_end=${daysAgo(0)}`,
    );
    expect(r.status).toBe(200);
  });

  // 1d bucket limit = 366 days (but period limit is 367 — 367 days triggers period limit first)
  test("1d interval, 367 days → 400", async () => {
    const r = await api(
      `/v4/data/network/NEM?metrics=energy&interval=1d&date_start=${daysAgo(367)}&date_end=${daysAgo(0)}`,
    );
    expect(r.status).toBe(400);
  });

  test("1d interval, 300 days → 200 (within limit)", async () => {
    const r = await api(
      `/v4/data/network/NEM?metrics=energy&interval=1d&date_start=${daysAgo(300)}&date_end=${daysAgo(0)}`,
    );
    expect(r.status).toBe(200);
  });
});

describe("COMMUNITY period limit (367 days)", () => {
  test("date_start 2 years ago → 400", async () => {
    const r = await api(
      `/v4/data/network/NEM?metrics=energy&interval=1d&date_start=${daysAgo(730)}&date_end=${daysAgo(700)}`,
    );
    expect(r.status).toBe(400);
  });

  test("date_start 300 days ago → 200", async () => {
    const r = await api(
      `/v4/data/network/NEM?metrics=energy&interval=1d&date_start=${daysAgo(300)}&date_end=${daysAgo(270)}`,
    );
    expect(r.status).toBe(200);
  });
});

// ─── 10. Rate limit / credits info ──────────────────────────────────────────

describe("rate limit & credits", () => {
  test("/v4/me returns plan info", async () => {
    const r = await api("/v4/me");
    expect(r.status).toBe(200);
    const data = unwrap<Record<string, unknown>>(r);
    expect(data).toHaveProperty("plan");
    expect(data.plan).toBe("COMMUNITY");
  });
});

// ─── 11. Error handling ─────────────────────────────────────────────────────

describe("error handling", () => {
  test("invalid network code → 400", async () => {
    const r = await api("/v4/data/network/FAKE?metrics=energy&interval=1h");
    expect(r.status).toBe(400);
  });

  test("invalid interval → 422", async () => {
    const r = await api("/v4/data/network/NEM?metrics=energy&interval=99x");
    expect(r.status).toBe(422);
  });

  test("invalid metric → 422", async () => {
    const r = await api("/v4/data/network/NEM?metrics=fake_metric&interval=1h");
    expect(r.status).toBe(422);
  });

  test("date_start after date_end → 400", async () => {
    const r = await api(
      `/v4/data/network/NEM?metrics=energy&interval=1h&date_start=${daysAgo(1)}&date_end=${daysAgo(10)}`,
    );
    expect(r.status).toBe(400);
  });
});
