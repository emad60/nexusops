/**
 * Skeleton loaders — shimmering placeholders rendered while a query is in
 * flight, instead of a spinner block. They echo the shape of the content they
 * replace, so layout doesn't jump when data arrives.
 *
 * Use `TableSkeleton` for the main list pages (matches `table.data` rhythm),
 * `SkeletonCard` for card grids, and raw `<Skeleton>` bars anywhere bespoke.
 * LoadingBlock stays available for non-tabular detail panes.
 */

import type { ReactNode } from "react";

export function Skeleton({ w = "100%", h = 12, className }: { w?: number | string; h?: number; className?: string }) {
  return (
    <span
      className={`skeleton${className ? ` ${className}` : ""}`}
      style={{ width: w, height: h }}
      aria-hidden
    />
  );
}

/**
 * Placeholder for the paged list tables: header bar + N row stripes.
 * Deliberately NOT a real <table> — fake table semantics would be announced
 * to screen readers and would satisfy findByRole("table") before real data
 * arrives; a div grid announces nothing but its status label.
 */
export function TableSkeleton({ label, rows = 8, cols = 5 }: { label: string; rows?: number; cols?: number }) {
  return (
    <div className="card" role="status" aria-label={label}>
      <div className="table-wrap">
        <div className="skeleton-table">
          <div className="skeleton-row head">
            {Array.from({ length: cols }, (_, i) => (
              <Skeleton key={i} w={i === 0 ? 90 : 56} h={10} />
            ))}
          </div>
          {Array.from({ length: rows }, (_, row) => (
            <div className="skeleton-row" key={row}>
              {Array.from({ length: cols }, (_, col) => (
                <Skeleton key={col} w={col === 0 ? "70%" : "45%"} h={12} />
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/** Placeholder for card grids (projects, hosts) — title bar + three lines. */
export function SkeletonCard({ lines = 3 }: { lines?: number }) {
  return (
    <div className="card" aria-hidden>
      <Skeleton w="55%" h={14} className="mb-8" />
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton key={i} w={i === lines - 1 ? "40%" : "85%"} h={10} className="mb-8" />
      ))}
    </div>
  );
}

/** Grid of SkeletonCards with an accessible collective label. */
export function SkeletonCardGrid({ label, count = 4, columns = 2, children }: { label: string; count?: number; columns?: number; children?: ReactNode }) {
  return (
    <div
      role="status"
      aria-label={label}
      className="skeleton-grid"
      style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
    >
      {Array.from({ length: count }, (_, i) => (
        <SkeletonCard key={i} />
      ))}
      {children}
    </div>
  );
}
