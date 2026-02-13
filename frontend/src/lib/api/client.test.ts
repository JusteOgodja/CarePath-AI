import { afterEach, describe, expect, it, vi } from "vitest";
import { apiFetch, ApiClientError } from "@/lib/api/client";

const SESSION_KEY = "carepath_auth_session";

function setAuthToken(token: string): void {
  window.localStorage.setItem(
    SESSION_KEY,
    JSON.stringify({
      access_token: token,
      token_type: "bearer",
      role: "admin",
      username: "tester",
    })
  );
}

describe("apiFetch", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    window.localStorage.clear();
  });

  it("adds Authorization header when auth session exists", async () => {
    setAuthToken("test-token");

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ ok: true }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await apiFetch<{ ok: boolean }>("/health");

    const [, options] = fetchMock.mock.calls[0];
    const headers = options.headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer test-token");
    expect(headers["Content-Type"]).toBe("application/json");
  });

  it("throws ApiClientError with backend detail on non-OK response", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ detail: "Bad request payload" }),
      text: async () => "Bad request payload",
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(apiFetch("/recommander", { method: "POST", body: "{}" })).rejects.toMatchObject({
      name: "ApiClientError",
      status: 400,
      message: "Bad request payload",
    } satisfies Partial<ApiClientError>);
  });
});

