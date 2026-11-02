import { useState, useMemo, useRef, useCallback, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { EmptyState } from './EmptyState';
import { LoadingSpinner } from './LoadingSpinner';
import { Skeleton } from './Skeleton';

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
  keepPreviousData?: boolean;
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
  keepPreviousData = false,
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
  const [localSearch, setLocalSearch] = useState(searchValue || '');
  const tableRef = useRef<HTMLTableSectionElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    setLocalSearch(searchValue || '');
  }, [searchValue]);

  useEffect(() => {
    setActiveRowIndex(-1);
  }, [data]);

  const handleSearchChange = (value: string) => {
    setLocalSearch(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      if (page !== 1) onPageChange?.(1);
      onSearchChange?.(value);
    }, 300);
  };

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  const totalPages = useMemo(() => Math.ceil(totalItems / pageSize), [totalItems, pageSize]);

  const pageNumbers = useMemo(() => {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, index) => index + 1);
    }
    const pages: (number | 'dots-left' | 'dots-right')[] = [1];
    const start = Math.max(2, page - 1);
    const end = Math.min(totalPages - 1, page + 1);
    if (start > 2) pages.push('dots-left');
    for (let pageNumber = start; pageNumber <= end; pageNumber += 1) {
      pages.push(pageNumber);
    }
    if (end < totalPages - 1) pages.push('dots-right');
    pages.push(totalPages);
    return pages;
  }, [page, totalPages]);

  const handleSort = (key: string) => {
    const newOrder = sortKey === key && sortOrder === 'asc' ? 'desc' : 'asc';
    setSortKey(key);
    setSortOrder(newOrder);
    setActiveRowIndex(-1);
    onSort?.(key, newOrder);
  };

  const rowPadding = density === 'compact' ? 'py-1.5' : 'py-3';

  // Fall back to client-side sorting of the current page when the caller does
  // not provide a server-side sort handler.
  const sortedData = useMemo(() => {
    if (sortKey === null || onSort) return data;
    const direction = sortOrder === 'asc' ? 1 : -1;
    return [...data].sort((a, b) => {
      const left = a[sortKey];
      const right = b[sortKey];
      if (left === right) return 0;
      if (left === null || left === undefined) return 1;
      if (right === null || right === undefined) return -1;
      if (typeof left === 'number' && typeof right === 'number') {
        return (left - right) * direction;
      }
      const leftNumber = Number(left);
      const rightNumber = Number(right);
      if (
        left !== '' &&
        right !== '' &&
        !Number.isNaN(leftNumber) &&
        !Number.isNaN(rightNumber)
      ) {
        return (leftNumber - rightNumber) * direction;
      }
      return String(left).localeCompare(String(right), 'ar', {
        numeric: true,
        sensitivity: 'base',
      }) * direction;
    });
  }, [data, sortKey, sortOrder, onSort]);

  const scrollRowIntoView = useCallback((index: number) => {
    const row = tableRef.current?.querySelector<HTMLElement>(`[data-row-index="${index}"]`);
    row?.scrollIntoView({ block: 'nearest' });
  }, []);

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLTableSectionElement>) => {
      if (!onRowClick || sortedData.length === 0) return;

      let nextIndex = activeRowIndex;

      if (event.key === 'ArrowDown') {
        nextIndex = Math.min(activeRowIndex + 1, sortedData.length - 1);
      } else if (event.key === 'ArrowUp') {
        nextIndex = Math.max(activeRowIndex - 1, 0);
      } else if (event.key === 'Home') {
        nextIndex = 0;
      } else if (event.key === 'End') {
        nextIndex = sortedData.length - 1;
      } else if (event.key === 'Enter' || event.key === ' ') {
        if (activeRowIndex >= 0 && activeRowIndex < sortedData.length) {
          event.preventDefault();
          onRowClick(sortedData[activeRowIndex]);
        }
        return;
      } else {
        return;
      }

      event.preventDefault();
      setActiveRowIndex(nextIndex);
      scrollRowIntoView(nextIndex);
    },
    [activeRowIndex, sortedData, onRowClick, scrollRowIntoView]
  );

  const headerRow = (
    <tr className="table-header">
      {columns.map((col) => (
        <th
          key={col.key}
          scope="col"
          aria-sort={
            col.sortable
              ? sortKey === col.key
                ? sortOrder === 'asc'
                  ? 'ascending'
                  : 'descending'
                : 'none'
              : undefined
          }
          className={cn(
            'px-4 py-2 text-right text-xs font-semibold uppercase tracking-wider',
            col.className
          )}
        >
          {col.sortable ? (
            <button
              type="button"
              onClick={() => handleSort(col.key)}
              className="group inline-flex items-center gap-1 transition-colors hover:text-gray-800 dark:hover:text-zinc-300"
            >
              {col.header}
              <span className="text-gray-400 dark:text-zinc-500">
                {sortKey === col.key ? (
                  <svg
                    className={cn('h-3 w-3 transition-transform', sortOrder === 'desc' && 'rotate-180')}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                  </svg>
                ) : (
                  <svg
                    className="h-3 w-3 opacity-0 transition-opacity group-hover:opacity-100"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l4-4 4 4m0 6l-4 4-4-4" />
                  </svg>
                )}
              </span>
            </button>
          ) : (
            <div>{col.header}</div>
          )}
        </th>
      ))}
    </tr>
  );

  return (
    <div
      className="card overflow-hidden p-0 dark:border-zinc-800 dark:bg-zinc-900"
      aria-busy={loading}
    >
      <div className="flex flex-col gap-3 border-b border-gray-100 p-4 sm:flex-row sm:items-center sm:justify-between dark:border-zinc-800">
        <div className="w-full sm:max-w-sm">
          {onSearchChange && (
            <div className="relative">
              <svg
                className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400 dark:text-zinc-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                value={localSearch}
                onChange={(event) => handleSearchChange(event.target.value)}
                placeholder={searchPlaceholder}
                aria-label={searchPlaceholder}
                className="input pl-9 pr-10 text-sm"
              />
              {localSearch && (
                <button
                  type="button"
                  onClick={() => handleSearchChange('')}
                  aria-label="مسح البحث"
                  className="absolute left-2 top-1/2 -translate-y-1/2 rounded p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-zinc-700 dark:hover:text-zinc-200"
                >
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          )}
        </div>
        {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
      </div>

      {loading && data.length === 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full" role="table" aria-label="جاري تحميل البيانات">
            <thead className="sticky top-0 z-10">{headerRow}</thead>
            <tbody>
              {Array.from({ length: 6 }).map((_, rowIndex) => (
                <tr
                  key={rowIndex}
                  className="border-b border-gray-100 last:border-0 dark:border-zinc-800"
                >
                  {columns.map((col) => (
                    <td key={col.key} className={cn('px-4', rowPadding)}>
                      <Skeleton
                        variant="text"
                        className={cn('h-4', rowIndex % 2 === 0 ? 'w-3/4' : 'w-2/3')}
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : !loading && data.length === 0 ? (
        <EmptyState title={emptyTitle} description={emptyDescription} />
      ) : (
        <>
          <div className="relative overflow-x-auto">
            {loading && keepPreviousData && data.length > 0 && (
              <div className="absolute inset-0 z-20 flex items-center justify-center bg-white/60 backdrop-blur-[1px] dark:bg-zinc-900/60">
                <LoadingSpinner />
              </div>
            )}
            <table className="w-full" role="table">
              <thead className="sticky top-0 z-10">{headerRow}</thead>
              <tbody
                ref={tableRef}
                onKeyDown={onRowClick ? handleKeyDown : undefined}
                onFocus={onRowClick ? () => setActiveRowIndex((prev) => (prev < 0 ? 0 : prev)) : undefined}
                tabIndex={onRowClick ? 0 : undefined}
                aria-label={onRowClick ? 'استخدم الأسهم للتنقل و Enter للفتح' : undefined}
                className={cn(
                  'focus:outline-none',
                  loading && keepPreviousData && 'opacity-60'
                )}
              >
                {sortedData.map((item, idx) => (
                  <tr
                    key={idx}
                    data-row-index={idx}
                    aria-selected={idx === activeRowIndex ? true : undefined}
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

          {totalItems > 0 && (
            <div className="flex flex-col items-center justify-between gap-2 border-t border-gray-100 px-4 py-3 sm:flex-row dark:border-zinc-800">
              <span className="text-xs text-gray-500 sm:text-sm dark:text-zinc-400">
                عرض {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, totalItems)} من {totalItems}
              </span>

              {totalPages > 1 && (
                <nav aria-label="ترقيم الصفحات" className="flex flex-wrap items-center justify-center gap-1">
                  <button
                    type="button"
                    onClick={() => onPageChange?.(1)}
                    disabled={page <= 1}
                    aria-label="الصفحة الأولى"
                    className="rounded-md border border-gray-300 px-2 py-1 text-sm transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-600 dark:hover:bg-zinc-800 dark:text-zinc-300"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    onClick={() => onPageChange?.(page - 1)}
                    disabled={page <= 1}
                    className="rounded-md border border-gray-300 px-3 py-1 text-sm transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-600 dark:hover:bg-zinc-800 dark:text-zinc-300"
                  >
                    السابق
                  </button>

                  {pageNumbers.map((pageNumber, index) =>
                    typeof pageNumber === 'number' ? (
                      <button
                        key={pageNumber}
                        type="button"
                        onClick={() => onPageChange?.(pageNumber)}
                        aria-current={pageNumber === page ? 'page' : undefined}
                        className={cn(
                          'min-w-8 rounded-md px-2.5 py-1 text-sm transition-colors',
                          pageNumber === page
                            ? 'bg-primary-600 text-white shadow-sm'
                            : 'border border-gray-300 hover:bg-gray-50 dark:border-zinc-600 dark:hover:bg-zinc-800 dark:text-zinc-300'
                        )}
                      >
                        {pageNumber}
                      </button>
                    ) : (
                      <span key={`${pageNumber}-${index}`} className="px-1 text-gray-400" aria-hidden="true">
                        …
                      </span>
                    )
                  )}

                  <button
                    type="button"
                    onClick={() => onPageChange?.(page + 1)}
                    disabled={page >= totalPages}
                    className="rounded-md border border-gray-300 px-3 py-1 text-sm transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-600 dark:hover:bg-zinc-800 dark:text-zinc-300"
                  >
                    التالي
                  </button>
                  <button
                    type="button"
                    onClick={() => onPageChange?.(totalPages)}
                    disabled={page >= totalPages}
                    aria-label="الصفحة الأخيرة"
                    className="rounded-md border border-gray-300 px-2 py-1 text-sm transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-600 dark:hover:bg-zinc-800 dark:text-zinc-300"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                    </svg>
                  </button>
                </nav>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
