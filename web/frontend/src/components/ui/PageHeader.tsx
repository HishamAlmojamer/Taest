import { cn } from '@/lib/utils';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

/**
 * Unified page header for consistent, professional-looking page titles
 * across all modules.
 */
export function PageHeader({ title, subtitle, icon, actions, className }: PageHeaderProps) {
  return (
    <div
      className={cn(
        'relative mb-6 overflow-hidden rounded-2xl border border-gray-200 bg-gradient-to-r from-white via-white to-primary-50/20 p-5 shadow-card sm:p-6 dark:border-zinc-800 dark:from-zinc-900 dark:via-zinc-900 dark:to-primary-500/5',
        className
      )}
    >
      <div className="absolute -left-24 -top-24 h-48 w-48 rounded-full bg-primary-500/5 blur-3xl dark:bg-primary-400/10" />
      <div className="relative flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          {icon && (
            <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 text-white shadow-lg shadow-primary-500/20 sm:h-12 sm:w-12">
              {icon}
            </div>
          )}
          <div className="min-w-0">
            <h1 className="page-title">{title}</h1>
            {subtitle && <p className="page-subtitle">{subtitle}</p>}
          </div>
        </div>
        {actions && <div className="relative flex flex-shrink-0 flex-wrap items-center gap-2">{actions}</div>}
      </div>
    </div>
  );
}

