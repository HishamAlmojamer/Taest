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
        'sticky bottom-0 bg-white dark:bg-zinc-900 border-t border-gray-200 dark:border-zinc-800 p-4 flex items-center justify-end gap-3 z-10',
        className
      )}
    >
      {onCancel && (
        <button type="button" onClick={onCancel} className="btn-outline">
          {cancelLabel}
        </button>
      )}
      {onSave && (
        <button type="button" onClick={onSave} disabled={isSubmitting} className="btn-primary">
          {isSubmitting ? 'جاري الحفظ...' : saveLabel}
        </button>
      )}
    </div>
  );
}
