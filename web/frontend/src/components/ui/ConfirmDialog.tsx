import { Modal } from '@/components/ui/Modal';
import { cn } from '@/lib/utils';

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'info';
  isLoading?: boolean;
}

const variantStyles = {
  danger: {
    icon: 'bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400',
    button: 'bg-red-600 hover:bg-red-700 shadow-sm hover:shadow-md',
    path: 'M12 9v4m0 4h.01M10.29 3.86l-8.1 14A2 2 0 004 21h16a2 2 0 001.71-3.14l-8.1-14a2 2 0 00-3.42 0z',
  },
  warning: {
    icon: 'bg-amber-50 text-amber-600 dark:bg-amber-500/10 dark:text-amber-400',
    button: 'bg-amber-600 hover:bg-amber-700 shadow-sm hover:shadow-md',
    path: 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  },
  info: {
    icon: 'bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400',
    button: 'bg-blue-600 hover:bg-blue-700 shadow-sm hover:shadow-md',
    path: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  },
};

export function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'تأكيد',
  cancelText = 'إلغاء',
  variant = 'danger',
  isLoading = false,
}: ConfirmDialogProps) {
  if (!isOpen) return null;

  const styles = variantStyles[variant];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="sm">
      <div className="space-y-5">
        <div className="flex items-start gap-3">
          <div
            className={cn(
              'flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full',
              styles.icon
            )}
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={styles.path} />
            </svg>
          </div>
          <p className="pt-1.5 text-sm leading-relaxed text-gray-600 dark:text-zinc-300">{message}</p>
        </div>

        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} disabled={isLoading} className="btn-outline">
            {cancelText}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isLoading}
            className={cn('btn text-white', styles.button)}
          >
            {isLoading && (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
            )}
            {isLoading ? 'جاري التنفيذ...' : confirmText}
          </button>
        </div>
      </div>
    </Modal>
  );
}
