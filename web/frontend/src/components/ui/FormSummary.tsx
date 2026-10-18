import { cn } from '@/lib/utils';
import { formatCurrency } from '@/lib/utils';

interface SummaryItem {
  label: string;
  value: string | number;
  highlighted?: boolean;
  currency?: boolean;
}

interface FormSummaryProps {
  items: SummaryItem[];
  title?: string;
  className?: string;
}

export function FormSummary({ items, title = 'الملخص', className }: FormSummaryProps) {
  return (
    <div className={cn('card', className)}>
      <h3 className="text-sm font-semibold text-gray-900 dark:text-zinc-100 mb-4">{title}</h3>
      <div className="space-y-3">
        {items.map((item, i) => (
          <div
            key={i}
            className={cn(
              'flex items-center justify-between text-sm',
              item.highlighted && 'font-bold text-lg pt-2 border-t border-gray-200 dark:border-zinc-700'
            )}
          >
            <span className={cn(
              'text-gray-600 dark:text-zinc-400',
              item.highlighted && 'text-gray-900 dark:text-zinc-100 font-semibold'
            )}>
              {item.label}
            </span>
            <span className={cn(
              'text-gray-900 dark:text-zinc-100 font-medium',
              item.highlighted && 'text-primary-600 dark:text-primary-400'
            )}>
              {item.currency ? formatCurrency(Number(item.value)) : item.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
