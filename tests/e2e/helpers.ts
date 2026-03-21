export const API_BASE = process.env.API_BASE_URL ?? "https://api.oedev.org";
export const API_KEY = process.env.API_KEY;

if (!API_KEY) {
  throw new Error("API_KEY env var required. Usage: API_KEY=xxx bun test tests/e2e/");
}

export type ApiResponse = {
  status: number;
  json: unknown;
  headers: Headers;
  path: string;
};

export async function api(path: string, opts?: RequestInit & { noAuth?: boolean }): Promise<ApiResponse> {
  const url = `${API_BASE}${path}`;
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(opts?.headers as Record<string, string>),
  };

  if (!opts?.noAuth && API_KEY) {
    headers.Authorization = `Bearer ${API_KEY}`;
  }

  const res = await fetch(url, { ...opts, headers });

  let json: unknown;
  const ct = res.headers.get("content-type") ?? "";
  if (ct.includes("application/json")) {
    json = await res.json();
  } else {
    json = await res.text();
  }

  console.log(`  ${res.status} ${path}`);
  return { status: res.status, json, headers: res.headers, path };
}

/** YYYY-MM-DD for N days ago */
export function daysAgo(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
}

/** Unwrap standard envelope { data: T } */
export function unwrap<T = unknown>(r: ApiResponse): T {
  const body = r.json as Record<string, unknown>;
  return body.data as T;
}
