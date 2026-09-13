/**
 * Shared server create/edit form.
 *
 * ServerListPage (create) and ServerDetailPage (edit) previously carried two
 * ~150-line copies of the same fields and the same validation; both now render
 * <ServerFormFields> and share validateServerForm / buildServerPayload, so the
 * wire contract (POST /servers, PATCH /servers/{id}) has exactly one owner.
 *
 * Per-field errors come from validateServerForm; buildServerPayload must only
 * be called once validation reports no errors.
 */

import { CheckboxField, TextField, TextAreaField } from "./form";

export interface ServerFormValues {
  name: string;
  hostname: string;
  ip_address: string;
  os_name: string;
  os_version: string;
  arch: string;
  environment: string;
  location: string;
  description: string;
  heartbeat_interval_seconds: string;
  offline_after_seconds: string;
  tags: string;
  simulated: boolean;
}

export const EMPTY_SERVER_FORM: ServerFormValues = {
  name: "",
  hostname: "",
  ip_address: "",
  os_name: "",
  os_version: "",
  arch: "",
  environment: "production",
  location: "",
  description: "",
  heartbeat_interval_seconds: "30",
  offline_after_seconds: "",
  tags: "",
  simulated: false,
};

export type ServerFormErrors = Partial<
  Record<"name" | "hostname" | "heartbeat_interval_seconds" | "offline_after_seconds", string>
>;

export function validateServerForm(values: ServerFormValues): ServerFormErrors {
  const errors: ServerFormErrors = {};
  if (!values.name.trim()) errors.name = "Name is required.";
  if (!values.hostname.trim()) errors.hostname = "Hostname is required.";

  const intervalRaw = values.heartbeat_interval_seconds.trim();
  if (intervalRaw) {
    const interval = Number(intervalRaw);
    if (!Number.isFinite(interval) || interval < 5 || interval > 3600) {
      errors.heartbeat_interval_seconds =
        "Heartbeat interval must be between 5 and 3600 seconds.";
    }
  }

  const offlineRaw = values.offline_after_seconds.trim();
  if (offlineRaw) {
    const offlineAfter = Number(offlineRaw);
    if (!Number.isFinite(offlineAfter) || offlineAfter <= 0) {
      errors.offline_after_seconds =
        "Offline threshold must be a positive number of seconds.";
    }
  }

  return errors;
}

/** Payload for POST /servers and PATCH /servers/{id} (mirrors the backend schema). */
export interface ServerPayload {
  name: string;
  hostname: string;
  ip_address: string;
  os_name: string;
  os_version: string;
  arch: string;
  environment: string;
  location: string;
  description: string;
  heartbeat_interval_seconds: number;
  offline_after_seconds: number | null;
  tags: string[];
  simulated: boolean;
}

/** Build the wire payload; call only after validateServerForm reports no errors. */
export function buildServerPayload(values: ServerFormValues): ServerPayload {
  const intervalRaw = values.heartbeat_interval_seconds.trim();
  const offlineRaw = values.offline_after_seconds.trim();
  return {
    name: values.name.trim(),
    hostname: values.hostname.trim(),
    ip_address: values.ip_address.trim(),
    os_name: values.os_name.trim(),
    os_version: values.os_version.trim(),
    arch: values.arch.trim(),
    environment: values.environment.trim() || "production",
    location: values.location.trim(),
    description: values.description.trim(),
    heartbeat_interval_seconds: intervalRaw ? Number(intervalRaw) : 30,
    offline_after_seconds: offlineRaw ? Number(offlineRaw) : null,
    tags: values.tags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean),
    simulated: values.simulated,
  };
}

interface ServerFormFieldsProps {
  values: ServerFormValues;
  onChange: (next: ServerFormValues) => void;
  errors?: ServerFormErrors;
  /** Prefix for control ids so create ("server-*") and edit ("server-edit-*") stay distinct. */
  idPrefix?: string;
  /** Move initial focus to the Name field (create modal convenience). */
  focusName?: boolean;
}

export function ServerFormFields({
  values,
  onChange,
  errors,
  idPrefix = "server",
  focusName = false,
}: ServerFormFieldsProps) {
  const set = <K extends keyof ServerFormValues>(key: K, value: ServerFormValues[K]) =>
    onChange({ ...values, [key]: value });
  const error = (key: keyof ServerFormErrors) => errors?.[key];

  return (
    <>
      <div className="field-row">
        <TextField
          id={`${idPrefix}-name`}
          label="Name"
          required
          error={error("name")}
          value={values.name}
          onChange={(e) => set("name", e.target.value)}
          placeholder="edge-01"
          autoFocus={focusName}
        />
        <TextField
          id={`${idPrefix}-hostname`}
          label="Hostname"
          required
          error={error("hostname")}
          value={values.hostname}
          onChange={(e) => set("hostname", e.target.value)}
          placeholder="edge01.example.net"
        />
      </div>
      <div className="field-row">
        <TextField
          id={`${idPrefix}-ip`}
          label="IP address"
          value={values.ip_address}
          onChange={(e) => set("ip_address", e.target.value)}
          placeholder="10.0.0.14"
        />
        <TextField
          id={`${idPrefix}-environment`}
          label="Environment"
          value={values.environment}
          onChange={(e) => set("environment", e.target.value)}
          placeholder="production"
        />
        <TextField
          id={`${idPrefix}-arch`}
          label="Architecture"
          value={values.arch}
          onChange={(e) => set("arch", e.target.value)}
          placeholder="x86_64"
        />
      </div>
      <div className="field-row">
        <TextField
          id={`${idPrefix}-os-name`}
          label="OS"
          value={values.os_name}
          onChange={(e) => set("os_name", e.target.value)}
          placeholder="Ubuntu"
        />
        <TextField
          id={`${idPrefix}-os-version`}
          label="OS version"
          value={values.os_version}
          onChange={(e) => set("os_version", e.target.value)}
          placeholder="24.04"
        />
        <TextField
          id={`${idPrefix}-location`}
          label="Location"
          value={values.location}
          onChange={(e) => set("location", e.target.value)}
          placeholder="dc-west-rack4"
        />
      </div>
      <div className="field-row">
        <TextField
          id={`${idPrefix}-heartbeat`}
          label="Heartbeat interval (seconds)"
          info="How often the agent reports in. Lower values mean faster offline detection but more traffic — 30s is a good default."
          type="number"
          min={5}
          max={3600}
          error={error("heartbeat_interval_seconds")}
          value={values.heartbeat_interval_seconds}
          onChange={(e) => set("heartbeat_interval_seconds", e.target.value)}
        />
        <TextField
          id={`${idPrefix}-offline-after`}
          label="Offline after (seconds, optional)"
          info="How long the server waits without a heartbeat before marking the server OFFLINE and opening alerts. Empty uses the backend default."
          type="number"
          min={1}
          error={error("offline_after_seconds")}
          value={values.offline_after_seconds}
          onChange={(e) => set("offline_after_seconds", e.target.value)}
        />
        <TextField
          id={`${idPrefix}-tags`}
          label="Tags (comma separated)"
          value={values.tags}
          onChange={(e) => set("tags", e.target.value)}
          placeholder="edge, gpu"
        />
      </div>
      <TextAreaField
        id={`${idPrefix}-description`}
        label="Description"
        rows={2}
        showCount={false}
        value={values.description}
        onChange={(e) => set("description", e.target.value)}
      />
      <CheckboxField
        id={`${idPrefix}-simulated`}
        label="Simulated server (demo data)"
        info="Generates plausible fake metrics, containers and deployments without contacting any real host — for demos and testing the UI."
        checked={values.simulated}
        onChange={(e) => set("simulated", e.target.checked)}
      />
    </>
  );
}
