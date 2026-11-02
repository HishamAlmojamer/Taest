import { useState } from 'react';
import { useToast } from '@/components/ui/Toast';
import { downloadExcel } from '@/api/excel';
import { cn } from '@/lib/utils';

interface ExportButtonProps {
  url: string;
  params?: Record<string, unknown>;
  filename?: string;
  label?: string;
  className?: string;
  icon?: React.ReactNode;
}

export default function ExcelExportButton({
  url,
  params,
  filename,
  label = 'تصدير Excel',
  className,
  icon,
}: ExportButtonProps) {
  const toast = useToast();
  const [busy, setBusy] = useState(false);

  async function handle() {
    setBusy(true);
    try {
      await downloadExcel(url, params, filename);
      toast.success('تم تصدير الملف بنجاح');
    } catch {
      toast.error('تعذر تصدير الملف Excel');
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      type="button"
      onClick={handle}
      disabled={busy}
      className={cn('btn-secondary flex items-center gap-2', busy && 'opacity-60 cursor-not-allowed', className)}
    >
      {icon ?? (
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
      )}
      {busy ? 'جارِ التصدير...' : label}
    </button>
  );
}