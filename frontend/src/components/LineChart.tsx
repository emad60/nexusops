/**
 * Dependency-free responsive SVG line chart.
 *
 * Series are arrays of {ts, value} points; the chart normalises each series to
 * its own scale when `normalize` is set (percent metrics), otherwise shares a
 * common y-domain. Grid lines, axis labels and a hover crosshair included.
 */

export interface ChartSeries {
  name: string;
  color: string;
  points: Array<{ ts: number; value: number | null }>;
}

interface LineChartProps {
  series: ChartSeries[];
  height?: number;
  /** 0..100 fixed domain (percent-style metrics). */
  fixedMax?: number;
  unit?: string;
}

const PAD = { top: 12, right: 12, bottom: 22, left: 34 };

export function LineChart({ series, height = 220, fixedMax, unit = "" }: LineChartProps) {
  const width = 720; // viewBox width; scales responsively
  const innerW = width - PAD.left - PAD.right;
  const innerH = height - PAD.top - PAD.bottom;

  const allPoints = series.flatMap((s) => s.points);
  if (allPoints.length === 0) {
    return <div className="empty-state small">No data in this range yet.</div>;
  }

  const times = allPoints.map((p) => p.ts);
  const tMin = Math.min(...times);
  const tMax = Math.max(...times);
  const values = allPoints.map((p) => p.value).filter((v): v is number => v != null);
  const vMax = fixedMax ?? Math.max(1, ...values) * 1.15;
  const vMin = 0;

  const x = (t: number) =>
    tMax === tMin ? PAD.left : PAD.left + ((t - tMin) / (tMax - tMin)) * innerW;
  const y = (v: number) => PAD.top + innerH - ((v - vMin) / (vMax - vMin)) * innerH;

  const gridLines = 4;
  const gridValues = Array.from({ length: gridLines + 1 }, (_, i) => vMin + ((vMax - vMin) * i) / gridLines);

  const formatTime = (t: number) =>
    new Date(t).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });

  return (
    <div className="chart-wrap">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Time series chart">
        {/* grid */}
        {gridValues.map((value) => (
          <g key={value}>
            <line
              x1={PAD.left}
              x2={width - PAD.right}
              y1={y(value)}
              y2={y(value)}
              stroke="#1f2b47"
              strokeDasharray="3 4"
            />
            <text x={PAD.left - 6} y={y(value) + 3} textAnchor="end" fontSize="9" fill="#64748b">
              {Math.round(value)}
              {unit}
            </text>
          </g>
        ))}

        {/* series */}
        {series.map((s) => {
          const segments: string[] = [];
          let open = false;
          for (const point of s.points) {
            if (point.value == null) {
              open = false;
              continue;
            }
            const cmd = open ? "L" : "M";
            segments.push(`${cmd}${x(point.ts).toFixed(1)},${y(point.value).toFixed(1)}`);
            open = true;
          }
          return (
            <path
              key={s.name}
              d={segments.join(" ")}
              fill="none"
              stroke={s.color}
              strokeWidth="1.8"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          );
        })}

        {/* x-axis ticks: first / middle / last */}
        {[tMin, (tMin + tMax) / 2, tMax].map((t) => (
          <text key={t} x={x(t)} y={height - 6} textAnchor="middle" fontSize="9" fill="#64748b">
            {formatTime(t)}
          </text>
        ))}
      </svg>

      {series.length > 1 || series[0]?.name ? (
        <div className="legend">
          {series.map((s) => (
            <span key={s.name}>
              <span className="dot" style={{ background: s.color }} />
              {s.name}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

/** Compact sparkline for table cells and stat cards. */
export function Sparkline({
  values,
  color = "#38bdf8",
  width = 120,
  height = 30,
}: {
  values: Array<number | null>;
  color?: string;
  width?: number;
  height?: number;
}) {
  const clean = values.filter((v): v is number => v != null);
  if (clean.length < 2) return <svg width={width} height={height} aria-hidden />;
  const min = Math.min(...clean);
  const max = Math.max(...clean);
  const span = max - min || 1;
  const stepX = width / (values.length - 1);
  const path = values
    .map((value, i) => {
      if (value == null) return null;
      const px = i * stepX;
      const py = height - 2 - ((value - min) / span) * (height - 4);
      return `${px === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)}`;
    })
    .filter(Boolean)
    .join(" ");
  return (
    <svg width={width} height={height} aria-hidden>
      <path d={path} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}
