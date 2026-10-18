import { useState, useMemo, useRef, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { EmptyState } from './EmptyState';
import { LoadingSpinner } from './LoadingSpinner';

export interface Column<T> {
  key: string;
  header: string;
  sortable?: boolean;
  render?: (item: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  totalItems?: number;
  page?: number;
  pageSize?: number;
  onPageChange?: (page: number) => void;
  onSort?: (key: string, order: 'asc' | 'desc') => void;
  onRowClick?: (item: T) => void;
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  searchPlaceholder?: string;
  emptyTitle?: string;
  emptyDescription?: string;
  actions?: React.ReactNode;
  density?: 'compact' | 'normal';
}

export function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  loading,
  totalItems = 0,
  page = 1,
  pageSize = 10,
  onPageChange,
  onSort,
  onRowClick,
  searchValue,
  onSearchChange,
  searchPlaceholder = 'بحث...',
  emptyTitle = 'لا توجد بيانات',
  emptyDescription = 'لم يتم العثور على أي سجلات',
  actions,
  density = 'normal',
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [activeRowIndex, setActiveRowIndex] = useState(-1);
  const tableRef = useRef<HTMLTableSectionElement>(null);

  const totalPages = useMemo(() => Math.ceil(totalItems / pageSize), [totalItems, pageSize]);

  const handleSort = (key: string) => {
    if (!onSort) return;
    const newOrder = sortKey === key && sortOrder === 'asc' ? 'desc' : 'asc';
    setSortKey(key);
    setSortOrder(newOrder);
    onSort(key, newOrder);
  };

  const rowPadding = density === 'compact' ? 'py-1.5' : 'py-3';

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!onRowClick || data.length === 0) return;
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setActiveRowIndex((prev) => {
          const next = Math.min(prev + 1, data.length - 1);
          onRowClick(data[next] as T);
          return next;
        });
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActiveRowIndex((prev) => {
          const next = Math.max(prev - 1, 0);
          onRowClick(data[next] as T);
          return next;
        });
      }
    },
    [data, onRowClick]
  );

  return (
    <div className="card p-0 overflow-hidden dark:bg-zinc-900 dark:border-zinc-800">
      <div className="flex items-center justify-between p-4 border-b border-gray-100 dark:border-zinc-800">
        <div className="flex-1 max-w-sm">
          {onSearchChange && (
            <div className="relative">
              <svg
                className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 dark:text-zinc-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                value={searchValue || ''}
                onChange={(e) => onSearchChange(e.target.value)}
                placeholder={searchPlaceholder}
                className="input pr-10 text-sm"
              />
            </div>
          )}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : data.length === 0 ? (
        <EmptyState title={emptyTitle} description={emptyDescription} />
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full" role="table">
              <thead className="sticky top-0 z-10">
                <tr className="table-header">
                  {columns.map((col) => (
                    <th
                      key={col.key}
                      className={cn(
                        'px-4 py-2 text-right text-xs font-semibold uppercase tracking-wider',
                        col.sortable && 'cursor-pointer select-none hover:text-gray-800 dark:hover:text-zinc-300',
                        col.className
                      )}
                      onClick={() => col.sortable && handleSort(col.key)}
                    >
                      <div className="flex items-center gap-1">
                        {col.header}
                        {col.sortable && sortKey === col.key && (
                          <svg
                            className={cn('h-3 w-3 transition-transform', sortOrder === 'desc' && 'rotate-180')}
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                          </svg>
                        )}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody ref={tableRef} onKeyDown={handleKeyDown} tabIndex={0}>
                {data.map((item, idx) => (
                  <tr
                    key={idx}
                    className={cn(
                      'table-row',
                      onRowClick && 'cursor-pointer',
                      idx === activeRowIndex && 'bg-primary-50 dark:bg-primary-500/10'
                    )}
                    onClick={() => {
                      setActiveRowIndex(idx);
                      onRowClick?.(item);
                    }}
                  >
                    {columns.map((col) => (
                      <td
                        key={col.key}
                        className={cn(
                          'px-4 text-sm text-gray-700 dark:text-zinc-300',
                          rowPadding,
                          col.className
                        )}
                      >
                        {col.render ? col.render(item) : String(item[col.key] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-gray-100 dark:border-zinc-800 px-4 py-2">
              <span className="text-sm text-gray-500 dark:text-zinc-400">
                عرض {(page - 1) * pageSize + 1}-{Math.min(page * pageSize, totalItems)} من {totalItems}
              </span>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => onPageChange?.(page - 1)}
                  disabled={page <= 1}
                  className="px-3 py-1 text-sm rounded-md border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed dark:border-zinc-600 dark:hover:bg-zinc-800 dark:text-zinc-300"
                >
                  السابق
                </button>
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum: number;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (page <= 3) {
                    pageNum = i + 1;
                  } else if (page >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = page - 2 + i;
                  }
                  return (
                    <button
                      key={pageNum}
                      onClick={() => onPageChange?.(pageNum)}
                      className={cn(
                        'px-3 py-1 text-sm rounded-md transition-colors',
                        pageNum === page
                          ? 'bg-primary-600 text-white'
                          : 'border border-gray-300 hover:bg-gray-50 dark:border-zinc-600 dark:hover:bg-zinc-800 dark:text-zinc-300'
                      )}
                    >
                      {pageNum}
                    </button>
                  );
                })}
                <button
                  onClick={() => onPageChange?.(page + 1)}
                  disabled={page >= totalPages}
                  className="px-3 py-1 text-sm rounded-md border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed dark:border-zinc-600 dark:hover:bg-zinc-800 dark:text-zinc-300"
                >
                  التالي
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
