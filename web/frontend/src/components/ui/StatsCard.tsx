import { cn } from '@/lib/utils';
import { formatCurrency } from '@/lib/utils';

interface StatsCardProps {
  title: string;
  value: number | string;
  currency?: boolean;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
    label?: string;
  };
  sparkData?: number[];
  color?: 'green' | 'blue' | 'yellow' | 'red' | 'purple';
  footer?: React.ReactNode;
}

const colorMap = {
  green: {
    bg: 'bg-primary-50 text-primary-600 dark:bg-primary-500/10 dark:text-primary-400',
    spark: 'fill-primary-500/5',
    line: '#10b981',
  },
  blue: {
    bg: 'bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400',
    spark: 'fill-blue-500/5',
    line: '#3b82f6',
  },
  yellow: {
    bg: 'bg-yellow-50 text-yellow-600 dark:bg-yellow-500/10 dark:text-yellow-400',
    spark: 'fill-yellow-500/5',
    line: '#f59e0b',
  },
  red: {
    bg: 'bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400',
    spark: 'fill-red-500/5',
    line: '#ef4444',
  },
  purple: {
    bg: 'bg-purple-50 text-purple-600 dark:bg-purple-500/10 dark:text-purple-400',
    spark: 'fill-purple-500/5',
    line: '#8b5cf6',
  },
};

/** Mini sparkline rendered as an inline SVG (no external dependency). */
function Sparkline({ data, line, fill }: { data: number[]; line: string; fill: string }) {
  if (!data || data.length < 2) return null;
  const width = 96;
  const height = 32;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const step = width / (data.length - 1);
  const points = data.map((v, i) => {
    const x = i * step;
    const y = height - ((v - min) / range) * (height - 4) - 2;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const path = `M${points.join(' L')}`;
  const area = `${path} L${width},${height} L0,${height} Z`;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="h-8 w-24 flex-shrink-0 overflow-visible"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <path d={area} className={cn(fill)} />
      <path
        d={path}
        fill="none"
        stroke={line}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function StatsCard({
  title,
  value,
  currency,
  icon,
  trend,
  sparkData,
  color = 'green',
  footer,
}: StatsCardProps) {
  const palette = colorMap[color];

  return (
    <div className="card card-hover animate-slide-up relative overflow-hidden p-5" role="group" aria-label={title}>
      {/* subtle top accent */}
      <div
        className="absolute top-0 inset-x-0 h-0.5"
        style={{ background: `linear-gradient(90deg, transparent, ${palette.line}, transparent)` }}
      />

      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-sm text-gray-500 dark:text-zinc-400 mb-1 truncate">{title}</p>
          <p className="text-2xl font-bold leading-tight break-words text-gray-900 tabular-nums dark:text-zinc-100">
            {currency ? formatCurrency(Number(value)) : value}
          </p>

          {trend && (
            <div
              className={cn(
                'flex items-center mt-2 text-sm',
                trend.isPositive ? 'text-emerald-600 dark:text-emerald-400' : 'text-danger-600 dark:text-danger-400'
              )}
            >
              <svg
                className={cn('h-4 w-4 ml-1 flex-shrink-0', trend.isPositive ? '' : 'rotate-180')}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
              <span className="font-semibold">{Math.abs(trend.value)}%</span>
              <span className="text-gray-400 dark:text-zinc-500 ml-1 text-xs">
                {trend.label || 'مقارنة بالفترة السابقة'}
              </span>
            </div>
          )}

          {footer && <div className="mt-2">{footer}</div>}
        </div>

        {/* right column: icon + sparkline */}
        <div className="flex flex-col items-end gap-2 flex-shrink-0">
          {icon && <div className={cn('p-3 rounded-xl shadow-sm', palette.bg)}>{icon}</div>}
          <Sparkline data={sparkData || []} line={palette.line} fill={palette.spark} />
        </div>
      </div>
    </div>
  );
}

