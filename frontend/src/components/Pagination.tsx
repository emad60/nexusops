import type { Page } from "../api/types";

interface PaginationProps {
  page: Page<unknown>;
  onPage: (offset: number) => void;
}

export function Pagination({ page, onPage }: PaginationProps) {
  const { total, limit, offset } = page;
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + limit, total);
  const hasPrev = offset > 0;
  const hasNext = offset + limit < total;

  return (
    <div className="pagination">
      <span>
        Showing {from}–{to} of {total}
      </span>
      <div className="pages">
        <button
          type="button"
          className="btn sm"
          disabled={!hasPrev}
          onClick={() => onPage(Math.max(0, offset - limit))}
        >
          ← Prev
        </button>
        <button
          type="button"
          className="btn sm"
          disabled={!hasNext}
          onClick={() => onPage(offset + limit)}
        >
          Next →
        </button>
      </div>
    </div>
  );
}
