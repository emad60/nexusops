/**
 * SimulatedChip — the honesty label for views whose data the platform fabricates.
 *
 * Deployment execution is a staged simulation until Phase 6 (see
 * docs/product-roadmap.md §3 and docs/deployment-architecture.md §13): the
 * runner renders docker-style step output and performs no real work, so a
 * "Deploy" that ends SUCCESS must never look like shipped code. Orchestration
 * — queueing, numbering, streaming, cancel, rollback, audit — is real.
 *
 * Gated on the runtime `/meta` flag (never a build-time default), sharing the
 * `["meta"]` query cache with the dashboard and sidebar badges so the SPA makes
 * one metadata call.
 */

import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../api/client";
import { InfoHint } from "./InfoHint";

/** Public instance metadata (subset of the backend MetaOut schema). */
interface MetaInfo {
  simulation_mode?: boolean;
}

export function SimulatedChip({
  label = "Simulated",
  detail = (
    <>
      No code is pulled, built or started — the deployment runner renders staged step output for
      demonstration. Queueing, live logs, cancellation, rollback and the audit trail are real.
      Real execution arrives with Phase 6.
    </>
  ),
}: {
  label?: string;
  detail?: ReactNode;
}) {
  const { data: meta } = useQuery({
    queryKey: ["meta"],
    queryFn: ({ signal }) => apiGet<MetaInfo>("/meta", undefined, signal),
    staleTime: 5 * 60_000,
  });

  if (!meta?.simulation_mode) return null;

  return (
    <span
      className="badge no-dot"
      style={{ background: "var(--warn-soft)", color: "var(--warn)" }}
    >
      {label}
      <InfoHint label="About simulated deployments">{detail}</InfoHint>
    </span>
  );
}
