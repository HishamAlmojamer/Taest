import { cn } from '@/lib/utils';

interface FormActionsProps {
  onSave?: () => void;
  onCancel?: () => void;
  isSubmitting?: boolean;
  saveLabel?: string;
  cancelLabel?: string;
  className?: string;
}

export function FormActions({
  onSave,
  onCancel,
  isSubmitting = false,
  saveLabel = 'حفظ',
  cancelLabel = 'إلغاء',
  className,
}: FormActionsProps) {
  return (
    <div
      className={cn(
        'sticky bottom-0 z-10 flex items-center justify-end gap-3 border-t border-gray-200 bg-white/95 p-4 backdrop-blur dark:border-zinc-800 dark:bg-zinc-900/95',
        className
      )}
    >
      {onCancel && (
        <button type="button" onClick={onCancel} className="btn-outline">
          {cancelLabel}
        </button>
      )}
      {onSave && (
        <button
          type="button"
          onClick={onSave}
          disabled={isSubmitting}
          aria-busy={isSubmitting}
          className="btn-primary"
        >
          {isSubmitting && (
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
          )}
          {isSubmitting ? 'جاري الحفظ...' : saveLabel}
        </button>
      )}
    </div>
  );
}
