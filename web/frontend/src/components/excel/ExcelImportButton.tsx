import { useState, useRef } from 'react';
import { useToast } from '@/components/ui/Toast';
import { uploadExcel } from '@/api/excel';
import { Modal } from '@/components/ui/Modal';
import { cn } from '@/lib/utils';

interface ImportResult {
  imported: number;
  failed: number;
  errors?: Array<{ row: number; error: string }>;
}

interface ImportButtonProps {
  url: string;
  label?: string;
  className?: string;
  helpText?: string;
  onSuccess?: (result: ImportResult) => void;
}

export default function ExcelImportButton({
  url,
  label = 'استيراد Excel',
  className,
  helpText = 'الصق ملف Excel مستوفياً لقالب الاستيراد المتاح',
  onSuccess,
}: ImportButtonProps) {
  const toast = useToast();
  const inputRef = useRef<HTMLInputElement>(null);
  const [showModal, setShowModal] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);

  async function handleFile(file: File | undefined) {
    if (!file) return;
    setBusy(true);
    setResult(null);
    try {
      const res = await uploadExcel(url, file);
      setResult(res);
      toast.success(`تم استيراد ${res.imported} سجل`);
      onSuccess?.(res);
    } catch (e: any) {
      toast.error('خطأ: ' + (e?.response?.data?.detail || e.message || 'تعذر استيراد الملف'));
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = '';
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setShowModal(true)}
        className={cn('btn-secondary flex items-center gap-2', className)}
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
        {label}
      </button>

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="استيراد من Excel" size="md">
        <div className="space-y-4">
          <p className="text-sm text-gray-600 dark:text-zinc-400">{helpText}</p>
          <input
            ref={inputRef}
            type="file"
            accept=".xlsx,.xls,.csv"
            disabled={busy}
            onChange={(e) => handleFile(e.target.files?.[0])}
            className="input"
          />
          {busy && <p className="text-sm text-blue-600 dark:text-blue-400">جارِ الاستيراد... يرجى الانتظار</p>}

          {result && (
            <div className="rounded-lg border border-gray-200 dark:border-zinc-700 p-4 space-y-2">
              <p className="text-sm font-medium">النتيجة:</p>
              <p className="text-sm text-emerald-600 dark:text-emerald-400">تم استيراد {result.imported} سجل</p>
              {result.failed > 0 && <p className="text-sm text-red-600 dark:text-red-400">فشل {result.failed} سجل</p>}
              {(result.errors || []).length > 0 && (
                <ul className="text-xs text-red-600 dark:text-red-400 max-h-40 overflow-y-auto space-y-1">
                  {result.errors!.slice(0, 100).map((err, i) => (
                    <li key={i}>سطر {err.row}: {err.error}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          <div className="flex justify-end">
            <button onClick={() => setShowModal(false)} className="btn-secondary">إغلاق</button>
          </div>
        </div>
      </Modal>
    </>
  );
}