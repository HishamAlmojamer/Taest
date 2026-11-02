import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, parseISO } from 'date-fns';
import { ar } from 'date-fns/locale/ar';
import { enUS } from 'date-fns/locale/en-US';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getCommandShortcutLabel(): string {
  if (typeof navigator === 'undefined') return 'Ctrl K';
  return /Mac|iPhone|iPad|iPod/i.test(navigator.platform) ? '⌘K' : 'Ctrl K';
}

export function formatCurrency(amount: number, currency: string = 'SAR'): string {
  return new Intl.NumberFormat('ar-SA', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatDate(date: string | Date | null | undefined, locale: string = 'ar'): string {
  if (!date) return '-';
  try {
    const d = typeof date === 'string' ? parseISO(date) : date;
    if (isNaN(d.getTime())) return '-';
    return format(d, 'dd/MM/yyyy', {
      locale: locale === 'ar' ? ar : enUS,
    });
  } catch {
    return '-';
  }
}

export function formatDateTime(date: string | Date | null | undefined, locale: string = 'ar'): string {
  if (!date) return '-';
  try {
    const d = typeof date === 'string' ? parseISO(date) : date;
    if (isNaN(d.getTime())) return '-';
    return format(d, 'dd/MM/yyyy HH:mm', {
      locale: locale === 'ar' ? ar : enUS,
    });
  } catch {
    return '-';
  }
}

export function formatNumber(num: number): string {
  return new Intl.NumberFormat('ar-SA').format(num);
}

export function getStatusLabel(status: string, locale: string = 'ar'): string {
  const statusMap: Record<string, Record<string, string>> = {
    DRAFT: { ar: 'مسودة', en: 'Draft' },
    SUBMITTED: { ar: 'مُقدَّم', en: 'Submitted' },
    APPROVED: { ar: 'مُعتمد', en: 'Approved' },
    REJECTED: { ar: 'مرفوض', en: 'Rejected' },
    PAID: { ar: 'مدفوع', en: 'Paid' },
    PARTIALLY_PAID: { ar: 'مدفوع جزئياً', en: 'Partially Paid' },
    RECEIVED: { ar: 'مستلم', en: 'Received' },
    PARTIALLY_RECEIVED: { ar: 'مستلم جزئياً', en: 'Partially Received' },
    POSTED: { ar: 'محرر', en: 'Posted' },
    REVERSED: { ar: 'معكوس', en: 'Reversed' },
    Draft: { ar: 'مسودة', en: 'Draft' },
    Posted: { ar: 'مرحّل', en: 'Posted' },
    Voided: { ar: 'ملغي', en: 'Voided' },
    Void: { ar: 'ملغي', en: 'Voided' },
    ACTIVE: { ar: 'نشط', en: 'Active' },
    INACTIVE: { ar: 'غير نشط', en: 'Inactive' },
    ON_LEAVE: { ar: 'في إجازة', en: 'On Leave' },
    PRESENT: { ar: 'حاضر', en: 'Present' },
    ABSENT: { ar: 'غائب', en: 'Absent' },
    LATE: { ar: 'متأخر', en: 'Late' },
    HALF_DAY: { ar: 'نصف يوم', en: 'Half Day' },
    PENDING: { ar: 'قيد الانتظار', en: 'Pending' },
    PLANNING: { ar: 'قيد التخطيط', en: 'Planning' },
    IN_PROGRESS: { ar: 'قيد التنفيذ', en: 'In Progress' },
    ON_HOLD: { ar: 'معلق', en: 'On Hold' },
    COMPLETED: { ar: 'مكتمل', en: 'Completed' },
    CANCELLED: { ar: 'ملغي', en: 'Cancelled' },
    TODO: { ar: 'للقيام', en: 'To Do' },
    REVIEW: { ar: 'قيد المراجعة', en: 'Review' },
    DONE: { ar: 'منجز', en: 'Done' },
    LOW: { ar: 'منخفض', en: 'Low' },
    MEDIUM: { ar: 'متوسط', en: 'Medium' },
    HIGH: { ar: 'عالي', en: 'High' },
    URGENT: { ar: 'عاجل', en: 'Urgent' },
    WON: { ar: 'تم الفوز', en: 'Won' },
    LOST: { ar: 'خسارة', en: 'Lost' },
    NEW: { ar: 'جديد', en: 'New' },
    CONTACTED: { ar: 'تم الاتصال', en: 'Contacted' },
    QUALIFIED: { ar: 'مؤهل', en: 'Qualified' },
    PROPOSAL: { ar: 'عرض سعر', en: 'Proposal' },
    NEGOTIATION: { ar: 'تفاوض', en: 'Negotiation' },
    ACHIEVED: { ar: 'مُحقق', en: 'Achieved' },
    MISSED: { ar: 'فات الموعد', en: 'Missed' },
    PROCESSED: { ar: 'تمت المعالجة', en: 'Processed' },
    CASH: { ar: 'نقدي', en: 'Cash' },
    BANK_TRANSFER: { ar: 'تحويل بنكي', en: 'Bank Transfer' },
    CHECK: { ar: 'شيك', en: 'Check' },
    CREDIT_CARD: { ar: 'بطاقة ائتمان', en: 'Credit Card' },
    ASSET: { ar: 'أصل', en: 'Asset' },
    LIABILITY: { ar: 'التزام', en: 'Liability' },
    EQUITY: { ar: 'حقوق ملكية', en: 'Equity' },
    REVENUE: { ar: 'إيراد', en: 'Revenue' },
    EXPENSE: { ar: 'مصروف', en: 'Expense' },
    IN: { ar: 'وارد', en: 'In' },
    OUT: { ar: 'صادر', en: 'Out' },
    TRANSFER: { ar: 'نقل', en: 'Transfer' },
    ADJUSTMENT: { ar: 'تسوية', en: 'Adjustment' },
    ANNUAL: { ar: 'إجازة سنوية', en: 'Annual Leave' },
    SICK: { ar: 'إجازة مرضية', en: 'Sick Leave' },
    PERSONAL: { ar: 'إجازة شخصية', en: 'Personal Leave' },
    MATERNITY: { ar: 'إجازة أمومة', en: 'Maternity Leave' },
    PATERNITY: { ar: 'إجازة أبوبة', en: 'Paternity Leave' },
    UNPAID: { ar: 'إجازة بدون راتب', en: 'Unpaid Leave' },
    DEPOSIT: { ar: 'إيداع', en: 'Deposit' },
    WITHDRAWAL: { ar: 'سحب', en: 'Withdrawal' },
    FEE: { ar: 'رسوم', en: 'Fee' },
    CALL: { ar: 'مكالمة', en: 'Call' },
    EMAIL: { ar: 'بريد إلكتروني', en: 'Email' },
    MEETING: { ar: 'اجتماع', en: 'Meeting' },
    NOTE: { ar: 'ملاحظة', en: 'Note' },
    OPEN: { ar: 'مفتوحة', en: 'Open' },
    TASK: { ar: 'مهمة', en: 'Task' },
    WHATSAPP: { ar: 'واتساب', en: 'WhatsApp' },
    GOLD: { ar: 'ذهبي', en: 'Gold' },
    SILVER: { ar: 'فضي', en: 'Silver' },
    BRONZE: { ar: 'برونزي', en: 'Bronze' },
    VIP: { ar: 'كبار العملاء', en: 'VIP' },
    STANDARD: { ar: 'قياسي', en: 'Standard' },
    ANNUAL_2026: { ar: '2026', en: '2026' },
  };
  const map = statusMap[status];
  return map ? map[locale] || status : status;
}

export function getStatusColor(status: string): string {
  const colorMap: Record<string, string> = {
    DRAFT: 'bg-amber-500/10 text-amber-600 dark:bg-amber-400/10 dark:text-amber-400',
    SUBMITTED: 'bg-amber-500/10 text-amber-600 dark:bg-amber-400/10 dark:text-amber-400',
    APPROVED: 'bg-emerald-500/10 text-emerald-600 dark:bg-emerald-400/10 dark:text-emerald-400',
    REJECTED: 'bg-red-500/10 text-red-600 dark:bg-red-400/10 dark:text-red-400',
    PAID: 'bg-emerald-500/10 text-emerald-600 dark:bg-emerald-400/10 dark:text-emerald-400',
    PARTIALLY_PAID: 'bg-amber-500/10 text-amber-600 dark:bg-amber-400/10 dark:text-amber-400',
    RECEIVED: 'bg-emerald-500/10 text-emerald-600 dark:bg-emerald-400/10 dark:text-emerald-400',
    PARTIALLY_RECEIVED: 'bg-amber-500/10 text-amber-600 dark:bg-amber-400/10 dark:text-amber-400',
    POSTED: 'bg-emerald-500/10 text-emerald-600 dark:bg-emerald-400/10 dark:text-emerald-400',
    REVERSED: 'bg-red-500/10 text-red-600 dark:bg-red-400/10 dark:text-red-400',
    Draft: 'bg-amber-500/10 text-amber-600 dark:bg-amber-400/10 dark:text-amber-400',
    Posted: 'bg-emerald-500/10 text-emerald-600 dark:bg-emerald-400/10 dark:text-emerald-400',
    Voided: 'bg-red-500/10 text-red-600 dark:bg-red-400/10 dark:text-red-400',
    Void: 'bg-red-500/10 text-red-600 dark:bg-red-400/10 dark:text-red-400',
    ACTIVE: 'bg-emerald-500/10 text-emerald-600 dark:bg-emerald-400/10 dark:text-emerald-400',
    INACTIVE: 'bg-red-500/10 text-red-600 dark:bg-red-400/10 dark:text-red-400',
    ON_LEAVE: 'bg-amber-500/10 text-amber-600 dark:bg-amber-400/10 dark:text-amber-400',
    PRESENT: 'bg-emerald-500/10 text-emerald-600 dark:bg-emerald-400/10 dark:text-emerald-400',
    ABSENT: 'bg-red-500/10 text-red-600 dark:bg-red-400/10 dark:text-red-400',
    LATE: 'bg-amber-500/10 text-amber-600 dark:bg-amber-400/10 dark:text-amber-400',
    PENDING: 'bg-amber-500/10 text-amber-600 dark:bg-amber-400/10 dark:text-amber-400',
    PLANNING: 'bg-sky-500/10 text-sky-600 dark:bg-sky-400/10 dark:text-sky-400',
    IN_PROGRESS: 'bg-sky-500/10 text-sky-600 dark:bg-sky-400/10 dark:text-sky-400',
    ON_HOLD: 'bg-amber-500/10 text-amber-600 dark:bg-amber-400/10 dark:text-amber-400',
    COMPLETED: 'bg-emerald-500/10 text-emerald-600 dark:bg-emerald-400/10 dark:text-emerald-400',
    CANCELLED: 'bg-red-500/10 text-red-600 dark:bg-red-400/10 dark:text-red-400',
    TODO: 'bg-sky-500/10 text-sky-600 dark:bg-sky-400/10 dark:text-sky-400',
    REVIEW: 'bg-amber-500/10 text-amber-600 dark:bg-amber-400/10 dark:text-amber-400',
    DONE: 'bg-emerald-500/10 text-emerald-600 dark:bg-emerald-400/10 dark:text-emerald-400',
    WON: 'bg-emerald-500/10 text-emerald-600 dark:bg-emerald-400/10 dark:text-emerald-400',
    LOST: 'bg-red-500/10 text-red-600 dark:bg-red-400/10 dark:text-red-400',
    NEW: 'bg-sky-500/10 text-sky-600 dark:bg-sky-400/10 dark:text-sky-400',
    CONTACTED: 'bg-sky-500/10 text-sky-600 dark:bg-sky-400/10 dark:text-sky-400',
    QUALIFIED: 'bg-amber-500/10 text-amber-600 dark:bg-amber-400/10 dark:text-amber-400',
    PROPOSAL: 'bg-amber-500/10 text-amber-600 dark:bg-amber-400/10 dark:text-amber-400',
    NEGOTIATION: 'bg-sky-500/10 text-sky-600 dark:bg-sky-400/10 dark:text-sky-400',
    OPEN: 'bg-sky-500/10 text-sky-600 dark:bg-sky-400/10 dark:text-sky-400',
    TASK: 'bg-violet-500/10 text-violet-600 dark:bg-violet-400/10 dark:text-violet-400',
    WHATSAPP: 'bg-emerald-500/10 text-emerald-600 dark:bg-emerald-400/10 dark:text-emerald-400',
    GOLD: 'bg-amber-500/10 text-amber-600 dark:bg-amber-400/10 dark:text-amber-400',
    SILVER: 'bg-zinc-500/10 text-zinc-600 dark:bg-zinc-400/10 dark:text-zinc-400',
    BRONZE: 'bg-orange-500/10 text-orange-600 dark:bg-orange-400/10 dark:text-orange-400',
  };
  return colorMap[status] || 'bg-zinc-500/10 text-zinc-600 dark:bg-zinc-400/10 dark:text-zinc-400';
}
