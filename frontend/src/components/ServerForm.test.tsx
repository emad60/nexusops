import { describe, expect, it, vi } from "vitest";
import {
  buildServerPayload,
  EMPTY_SERVER_FORM,
  ServerFormFields,
  validateServerForm,
} from "./ServerForm";
import { render, screen, fireEvent } from "@testing-library/react";

function renderForm(props: Parameters<typeof ServerFormFields>[0]) {
  return render(<ServerFormFields {...props} />);
}

describe("validateServerForm", () => {
  it("flags missing name and hostname", () => {
    const errors = validateServerForm(EMPTY_SERVER_FORM);
    expect(errors.name).toBe("Name is required.");
    expect(errors.hostname).toBe("Hostname is required.");
    expect(errors.heartbeat_interval_seconds).toBeUndefined();
    expect(errors.offline_after_seconds).toBeUndefined();
  });

  it("accepts a valid heartbeat interval at the bounds", () => {
    expect(
      validateServerForm({ ...EMPTY_SERVER_FORM, name: "a", hostname: "b", heartbeat_interval_seconds: "5" })
        .heartbeat_interval_seconds,
    ).toBeUndefined();
    expect(
      validateServerForm({
        ...EMPTY_SERVER_FORM,
        name: "a",
        hostname: "b",
        heartbeat_interval_seconds: "3600",
      }).heartbeat_interval_seconds,
    ).toBeUndefined();
  });

  it("rejects out-of-range and non-numeric heartbeat intervals", () => {
    for (const bad of ["4", "3601", "abc"]) {
      const errors = validateServerForm({
        ...EMPTY_SERVER_FORM,
        name: "a",
        hostname: "b",
        heartbeat_interval_seconds: bad,
      });
      expect(errors.heartbeat_interval_seconds).toMatch(/between 5 and 3600/);
    }
  });

  it("rejects a non-positive offline threshold", () => {
    const errors = validateServerForm({
      ...EMPTY_SERVER_FORM,
      name: "a",
      hostname: "b",
      offline_after_seconds: "0",
    });
    expect(errors.offline_after_seconds).toMatch(/positive number of seconds/);
  });
});

describe("buildServerPayload", () => {
  it("trims strings, splits tags and defaults the interval", () => {
    const payload = buildServerPayload({
      ...EMPTY_SERVER_FORM,
      name: "  edge-01  ",
      hostname: "edge01.example.net",
      ip_address: " 10.0.0.14 ",
      environment: "  ",
      tags: " edge, gpu , , db ",
      heartbeat_interval_seconds: "",
      offline_after_seconds: "",
    });
    expect(payload).toEqual({
      name: "edge-01",
      hostname: "edge01.example.net",
      ip_address: "10.0.0.14",
      os_name: "",
      os_version: "",
      arch: "",
      environment: "production",
      location: "",
      description: "",
      heartbeat_interval_seconds: 30,
      offline_after_seconds: null,
      tags: ["edge", "gpu", "db"],
      simulated: false,
    });
  });

  it("parses numeric fields and coerces empty offline_after to null", () => {
    const payload = buildServerPayload({
      ...EMPTY_SERVER_FORM,
      name: "a",
      hostname: "b",
      heartbeat_interval_seconds: "15",
      offline_after_seconds: "120",
    });
    expect(payload.heartbeat_interval_seconds).toBe(15);
    expect(payload.offline_after_seconds).toBe(120);
  });
});

describe("ServerFormFields", () => {
  it("renders every field with its label and shows per-field validation errors", () => {
    renderForm({
      values: EMPTY_SERVER_FORM,
      onChange: () => {},
      errors: { name: "Name is required.", heartbeat_interval_seconds: "Between 5 and 3600." },
    });

    expect(screen.getByLabelText("Name *")).toBeInTheDocument();
    expect(screen.getByLabelText("Hostname *")).toBeInTheDocument();
    expect(screen.getByLabelText("Environment")).toBeInTheDocument();
    expect(screen.getByLabelText("Heartbeat interval (seconds)")).toBeInTheDocument();
    expect(screen.getByLabelText("Offline after (seconds, optional)")).toBeInTheDocument();
    expect(screen.getByText("Name is required.")).toBeInTheDocument();
    expect(screen.getByText("Between 5 and 3600.")).toBeInTheDocument();
  });

  it("routes edits back through onChange", () => {
    const onChange = vi.fn();
    renderForm({ values: EMPTY_SERVER_FORM, onChange });

    fireEvent.change(screen.getByLabelText("Name *"), { target: { value: "edge-01" } });
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ name: "edge-01" }));

    fireEvent.click(screen.getByLabelText("Simulated server (demo data)"));
    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ simulated: true }));
  });
});
