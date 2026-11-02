import { useRef, useState, useCallback } from 'react';
import { Modal } from '@/components/ui/Modal';
import { downloadElementAsPdf, printDocument } from '@/lib/print';

interface PrintPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  filename: string;
  children: React.ReactNode;
}

export function PrintPreviewModal({ isOpen, onClose, title, filename, children }: PrintPreviewModalProps) {
  const docRef = useRef<HTMLDivElement>(null);
  const [busy, setBusy] = useState(false);

  const handlePrint = useCallback(() => {
    printDocument();
  }, []);

  const handlePdf = useCallback(async () => {
    if (!docRef.current) return;
    setBusy(true);
    try {
      await downloadElementAsPdf(docRef.current, filename);
    } finally {
      setBusy(false);
    }
  }, [filename]);

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="xl">
      <div className="space-y-4">
        <div className="flex items-center justify-end gap-2 border-b border-gray-200 dark:border-zinc-700 pb-3">
          <button onClick={handlePdf} disabled={busy} className="btn-primary flex items-center gap-2 disabled:opacity-50">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            {busy ? 'جاري التصدير...' : 'حفظ PDF'}
          </button>
          <button onClick={handlePrint} className="btn-secondary flex items-center gap-2">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4H7v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            طباعة
          </button>
        </div>
        <div className="print-document-area overflow-x-auto rounded-xl border border-gray-200 dark:border-zinc-700">
          <div ref={docRef} className="min-w-[720px]">
            {children}
          </div>
        </div>
      </div>
    </Modal>
  );
}
