import { useRef, useCallback } from 'react';
import { cn } from '@/lib/utils';

interface EditableColumn<T> {
  key: string;
  header: string;
  type?: 'text' | 'number' | 'select' | 'computed';
  options?: { value: string; label: string }[];
  width?: string;
  render?: (item: T, index: number) => React.ReactNode;
  editable?: boolean;
}

interface EditableTableProps<T> {
  columns: EditableColumn<T>[];
  data: T[];
  onChange: (data: T[]) => void;
  onAddRow?: () => void;
  onDeleteRow?: (index: number) => void;
  addRowLabel?: string;
  className?: string;
}

export function EditableTable<T extends Record<string, unknown>>({
  columns,
  data,
  onChange,
  onAddRow,
  onDeleteRow,
  addRowLabel = '+ إضافة صف',
  className,
}: EditableTableProps<T>) {
  const tableRef = useRef<HTMLTableElement>(null);

  const handleCellChange = useCallback(
    (index: number, key: string, value: unknown) => {
      const newData = [...data];
      newData[index] = { ...newData[index], [key]: value };
      onChange(newData);
    },
    [data, onChange]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent, rowIndex: number, colIndex: number) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (onAddRow && rowIndex === data.length - 1) {
          onAddRow();
        }
        const nextRow = Math.min(rowIndex + 1, data.length - 1);
        const nextCell = tableRef.current?.querySelector(
          `[data-row="${nextRow}"][data-col="${colIndex}"]`
        ) as HTMLElement;
        nextCell?.focus();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        const nextRow = Math.min(rowIndex + 1, data.length - 1);
        const nextCell = tableRef.current?.querySelector(
          `[data-row="${nextRow}"][data-col="${colIndex}"]`
        ) as HTMLElement;
        nextCell?.focus();
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        const prevRow = Math.max(rowIndex - 1, 0);
        const prevCell = tableRef.current?.querySelector(
          `[data-row="${prevRow}"][data-col="${colIndex}"]`
        ) as HTMLElement;
        prevCell?.focus();
      }
    },
    [data.length, onAddRow]
  );

  return (
    <div className={cn('overflow-x-auto', className)}>
      <table ref={tableRef} className="w-full" role="grid">
        <thead>
          <tr className="table-header">
            {columns.map((col) => (
              <th
                key={col.key}
                className="px-3 py-2 text-right text-xs font-semibold uppercase tracking-wider"
                style={{ width: col.width }}
              >
                {col.header}
              </th>
            ))}
            {onDeleteRow && <th className="w-10" />}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIndex) => (
            <tr
              key={rowIndex}
              className="table-row"
              data-row={rowIndex}
            >
              {columns.map((col, colIndex) => (
                <td
                  key={col.key}
                  className="px-2 py-1"
                  data-row={rowIndex}
                  data-col={colIndex}
                >
                  {col.render ? (
                    col.render(row, rowIndex)
                  ) : col.type === 'computed' ? (
                    <span className="text-sm text-gray-700 dark:text-zinc-300 px-2 py-1">
                      {String(row[col.key] ?? '')}
                    </span>
                  ) : col.type === 'select' ? (
                    <select
                      value={String(row[col.key] ?? '')}
                      onChange={(e) => handleCellChange(rowIndex, col.key, e.target.value)}
                      onKeyDown={(e) => handleKeyDown(e, rowIndex, colIndex)}
                      className="input py-1 text-sm"
                      tabIndex={0}
                    >
                      <option value="">اختر...</option>
                      {col.options?.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type={col.type || 'text'}
                      value={String(row[col.key] ?? '')}
                      onChange={(e) =>
                        handleCellChange(
                          rowIndex,
                          col.key,
                          col.type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value
                        )
                      }
                      onKeyDown={(e) => handleKeyDown(e, rowIndex, colIndex)}
                      className="input py-1 text-sm"
                      tabIndex={0}
                    />
                  )}
                </td>
              ))}
              {onDeleteRow && (
                <td className="px-2 py-1">
                  <button
                    onClick={() => onDeleteRow(rowIndex)}
                    className="p-1 text-red-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 rounded transition-colors"
                    title="حذف الصف"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>

      {onAddRow && (
        <button
          onClick={onAddRow}
          className="w-full py-2 text-sm text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-500/10 transition-colors border border-dashed border-gray-300 dark:border-zinc-700 rounded-b-lg"
        >
          {addRowLabel}
        </button>
      )}
    </div>
  );
}
