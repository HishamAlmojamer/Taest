import { cn } from '@/lib/utils';
import { getStatusLabel, getStatusColor } from '@/lib/utils';
import { useUIStore } from '@/stores/uiStore';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
  className?: string;
}

export function StatusBadge({ status, size = 'sm', className }: StatusBadgeProps) {
  const locale = useUIStore((s) => s.locale);
  const label = getStatusLabel(status, locale);
  const colorClasses = getStatusColor(status);

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full font-medium',
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm',
        colorClasses,
        className
      )}
    >
      {label}
    </span>
  );
}
