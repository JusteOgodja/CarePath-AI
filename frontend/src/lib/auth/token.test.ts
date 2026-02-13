import { afterEach, describe, expect, it } from "vitest";
import { getAuthToken } from "@/lib/auth";

const SESSION_KEY = "carepath_auth_session";

describe("getAuthToken", () => {
  afterEach(() => {
    window.localStorage.clear();
  });

  it("returns token from stored session", () => {
    window.localStorage.setItem(
      SESSION_KEY,
      JSON.stringify({
        access_token: "abc123",
        token_type: "bearer",
        role: "viewer",
        username: "viewer",
      })
    );

    expect(getAuthToken()).toBe("abc123");
  });

  it("returns null and clears invalid session JSON", () => {
    window.localStorage.setItem(SESSION_KEY, "{invalid-json");
    expect(getAuthToken()).toBeNull();
    expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
  });
});

