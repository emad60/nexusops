/**
 * Active-organization control for the top bar.
 *
 * Tenancy is never inferred, so the console always *shows* which organization it
 * is acting in — a list of one still renders the name, because "which tenant am
 * I looking at" must be answerable at a glance, not only when there are several.
 * Switching reloads the shell (see AuthContext.selectOrganization) so nothing
 * cached from the previous tenant can survive.
 */

import { Building2 } from "lucide-react";
import { useAuth } from "../auth/AuthContext";

export function OrganizationSwitcher() {
  const { organizations, activeMembership, selectOrganization } = useAuth();
  const active = activeMembership;

  if (organizations.length === 0) return null;

  return (
    <div className="flex gap-8" style={{ alignItems: "center" }}>
      <Building2 size={15} aria-hidden />
      {organizations.length > 1 ? (
        <label className="flex gap-8" style={{ alignItems: "center" }}>
          <span className="sr-only">Active organization</span>
          <select
            className="input"
            aria-label="Active organization"
            value={active?.organization.id ?? ""}
            onChange={(event) => selectOrganization(event.target.value)}
          >
            {organizations.map((membership) => (
              <option key={membership.organization.id} value={membership.organization.id}>
                {membership.organization.name}
                {membership.role_name ? ` — ${membership.role_name}` : ""}
              </option>
            ))}
          </select>
        </label>
      ) : (
        <span className="small" title="Active organization">
          {active?.organization.name}
          {active?.organization.is_provisional ? (
            <span
              className="tag-chip"
              style={{ marginLeft: 6 }}
              title="Auto-provisioned for data that pre-dates organizations — rename it"
            >
              provisional
            </span>
          ) : null}
        </span>
      )}
      {active?.role_name ? <span className="small muted">({active.role_name})</span> : null}
    </div>
  );
}
