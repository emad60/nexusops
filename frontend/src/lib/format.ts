/** Formatting helpers shared by pages and components. */

export function formatBytesMb(mb: number | null | undefined): string {
  if (mb == null) return "—";
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`;
  return `${Math.round(mb)} MB`;
}

export function formatGb(gb: number | null | undefined): string {
  if (gb == null) return "—";
  if (gb >= 1024) return `${(gb / 1024).toFixed(1)} TB`;
  return `${Math.round(gb)} GB`;
}

export function formatPercent(value: number | null | undefined, digits = 0): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toFixed(digits)}%`;
}

export function formatDurationMs(ms: number | null | undefined): string {
  if (ms == null) return "—";
  const seconds = ms / 1000;
  if (seconds < 60) return `${seconds.toFixed(seconds < 10 ? 1 : 0)}s`;
  const minutes = Math.floor(seconds / 60);
  const rest = Math.round(seconds % 60);
  if (minutes < 60) return `${minutes}m ${rest}s`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${minutes % 60}m`;
}

export function formatUptime(seconds: number | null | undefined): string {
  if (seconds == null || seconds <= 0) return "—";
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatRelative(iso: string | null | undefined): string {
  if (!iso) return "—";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "—";
  const deltaSeconds = Math.round((Date.now() - then) / 1000);
  const future = deltaSeconds < 0;
  const abs = Math.abs(deltaSeconds);
  let text: string;
  if (abs < 45) text = `${abs}s`;
  else if (abs < 3600) text = `${Math.round(abs / 60)}m`;
  else if (abs < 86400) text = `${Math.round(abs / 3600)}h`;
  else text = `${Math.round(abs / 86400)}d`;
  return future ? `in ${text}` : `${text} ago`;
}

export function truncate(text: string, max = 80): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}
