/**
 * Edge and sink addresses for the journey.
 *
 * Overridable so `make e2e` can run the stack on its own host ports without
 * clashing with a dev stack that is already up. Defaults match the compose
 * defaults in `.env.example`.
 */
export const EDGE = process.env.E2E_BASE_URL ?? "http://127.0.0.1:8080";
export const MAILPIT = process.env.E2E_MAILPIT_URL ?? "http://127.0.0.1:8025";
