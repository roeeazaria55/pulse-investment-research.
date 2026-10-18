// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";
import { copyText } from "../src/research/prompt";
afterEach(() => vi.restoreAllMocks());
describe("clipboard reliability", () => {
  it("uses the secure clipboard API", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(window, "isSecureContext", {
      value: true,
      configurable: true,
    });
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText },
      configurable: true,
    });
    expect(await copyText("Hebrew prompt")).toBe(true);
    expect(writeText).toHaveBeenCalledWith("Hebrew prompt");
  });
  it("falls back to selection and cleans up when clipboard is denied", async () => {
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: vi.fn().mockRejectedValue(Error("denied")) },
      configurable: true,
    });
    const execCommand = vi.fn().mockReturnValue(true);
    Object.defineProperty(document, "execCommand", {
      value: execCommand,
      configurable: true,
    });
    expect(await copyText("Fallback")).toBe(true);
    expect(execCommand).toHaveBeenCalledWith("copy");
    expect(document.querySelector("textarea")).toBeNull();
  });
  it("reports failure so the UI can offer manual copying", async () => {
    Object.defineProperty(navigator, "clipboard", {
      value: undefined,
      configurable: true,
    });
    Object.defineProperty(document, "execCommand", {
      value: vi.fn().mockReturnValue(false),
      configurable: true,
    });
    expect(await copyText("Manual")).toBe(false);
    expect(document.querySelector("textarea")).toBeNull();
  });
});
