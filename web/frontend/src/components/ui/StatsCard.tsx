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
  };
  color?: 'green' | 'blue' | 'yellow' | 'red' | 'purple';
}

const colorMap = {
  green: 'bg-primary-50 text-primary-600 dark:bg-primary-500/10 dark:text-primary-400',
  blue: 'bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400',
  yellow: 'bg-yellow-50 text-yellow-600 dark:bg-yellow-500/10 dark:text-yellow-400',
  red: 'bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400',
  purple: 'bg-purple-50 text-purple-600 dark:bg-purple-500/10 dark:text-purple-400',
};

export function StatsCard({ title, value, currency, icon, trend, color = 'green' }: StatsCardProps) {
  return (
    <div className="card flex items-start justify-between animate-slide-up">
      <div className="flex-1">
        <p className="text-sm text-gray-500 dark:text-zinc-400 mb-1">{title}</p>
        <p className="text-2xl font-bold text-gray-900 dark:text-zinc-100">
          {currency ? formatCurrency(Number(value)) : value}
        </p>
        {trend && (
          <div className={cn('flex items-center mt-2 text-sm', trend.isPositive ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400')}>
            <svg
              className={cn('h-4 w-4 ml-1', trend.isPositive ? '' : 'rotate-180')}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
            </svg>
            <span>{Math.abs(trend.value)}%</span>
          </div>
        )}
      </div>
      {icon && <div className={cn('p-3 rounded-lg', colorMap[color])}>{icon}</div>}
    </div>
  );
}
