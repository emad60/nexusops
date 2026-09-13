import { useEffect, useRef } from "react";
import type { KeyboardEvent as ReactKeyboardEvent, ReactNode } from "react";

/** Status pill — color derives from the status word itself via styles.css. */
export function StatusBadge({ value, className }: { value: string; className?: string }) {
  return <span className={`badge ${value} ${className ?? ""}`}>{value.replaceAll("_", " ")}</span>;
}

export function TagChip({ name, color }: { name: string; color?: string }) {
  const style = color ? { borderColor: `${color}55`, color } : undefined;
  return (
    <span className="tag-chip" style={style}>
      {name}
    </span>
  );
}

export function EmptyState({
  icon = "◎",
  title,
  hint,
  action,
}: {
  icon?: string;
  title: string;
  hint?: string;
  /** Optional call-to-action (usually a button) under the hint. */
  action?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <div className="icon" aria-hidden>
        {icon}
      </div>
      <p className="empty-title">{title}</p>
      {hint ? <p className="small faint mt-8">{hint}</p> : null}
      {action ? (
        <div style={{ marginTop: 14 }}>{action}</div>
      ) : null}
    </div>
  );
}

export function LoadingBlock({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="loading-block">
      <span className="spinner" aria-hidden />
      <span>{label}</span>
    </div>
  );
}

/** Error block that understands the backend error envelope. */
export function ErrorBlock({ error }: { error: unknown }) {
  const apiError = error as { code?: string; message?: string; status?: number };
  return (
    <div className="form-error" role="alert">
      {apiError?.code === "NETWORK_ERROR"
        ? "Cannot reach the NexusOps server."
        : `Error${apiError?.code ? ` (${apiError.code})` : ""}: ${
            apiError?.message ?? "Something went wrong"
          }`}
    </div>
  );
}

export interface ModalProps {
  open: boolean;
  title: string;
  onClose: () => void;
  wide?: boolean;
  children: ReactNode;
}

/** Shared with the sidebar drawer, which mirrors the modal's focus management. */
export const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function Modal({ open, title, onClose, wide, children }: ModalProps) {
  const dialogRef = useRef<HTMLDivElement | null>(null);
  const openerRef = useRef<HTMLElement | null>(null);

  // Focus management: move focus into the dialog when it opens, keep Tab
  // cycling inside it, and restore focus to the opener when it closes.
  useEffect(() => {
    if (!open) return undefined;
    openerRef.current =
      document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const node = dialogRef.current;
    if (node) {
      const first = node.querySelector<HTMLElement>(FOCUSABLE_SELECTOR);
      (first ?? node).focus();
    }
    return () => {
      if (openerRef.current?.isConnected) openerRef.current.focus();
      openerRef.current = null;
    };
  }, [open]);

  if (!open) return null;

  const handleKeyDown = (event: ReactKeyboardEvent) => {
    if (event.key === "Escape") {
      onClose();
      return;
    }
    if (event.key !== "Tab") return;
    const node = dialogRef.current;
    if (!node) return;
    const focusables = Array.from(
      node.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR),
    ).filter((el) => el.offsetParent !== null);
    if (focusables.length === 0) {
      event.preventDefault();
      node.focus();
      return;
    }
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    const active = document.activeElement;
    const inside = active instanceof HTMLElement && node.contains(active);
    if (event.shiftKey && (!inside || active === first)) {
      event.preventDefault();
      last.focus();
    } else if (!inside || active === last) {
      event.preventDefault();
      first.focus();
    }
  };

  return (
    <div
      className="modal-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
      onKeyDown={handleKeyDown}
      role="dialog"
      aria-modal="true"
      aria-label={title}
      tabIndex={-1}
    >
      {/* tabIndex={-1} makes the dialog focusable so focus() lands here when no
          child is focusable, and keydown (Escape/Tab) bubbles to the overlay. */}
      <div className={`modal ${wide ? "wide" : ""}`} ref={dialogRef} tabIndex={-1}>
        <div className="modal-head">
          <h2>{title}</h2>
          <button type="button" className="btn ghost sm" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
