/**
 * Shared parsing/formatting for configuration maps.
 *
 * Configuration is a flat `string → string` map, authored in the UI as
 * `KEY=VALUE` lines. Values may be secret **references** — `${secret:KEY}` —
 * which are stored verbatim and resolved server-side at deploy time only.
 */

/** A whole value that is nothing but a secret reference. */
export const SECRET_REF_RE = /^\$\{secret:[A-Za-z0-9_]+\}$/;

export function parseConfigText(text: string): {
  config: Record<string, string>;
  error: string | null;
} {
  const config: Record<string, string> = {};
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (line === "") continue;
    const eq = line.indexOf("=");
    if (eq <= 0) {
      return { config: {}, error: `Invalid line "${line.slice(0, 40)}" — expected KEY=VALUE` };
    }
    config[line.slice(0, eq).trim()] = line.slice(eq + 1);
  }
  return { config, error: null };
}

export function configToText(config: Record<string, unknown>): string {
  return Object.entries(config)
    .map(([key, value]) => `${key}=${String(value)}`)
    .join("\n");
}
