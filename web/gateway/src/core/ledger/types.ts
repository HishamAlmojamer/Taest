/**
 * Ledger Engine: Type Definitions
 *
 * Core types for the double-entry bookkeeping system.
 *
 * Accounting Logic:
 *   - Every financial transaction produces a Journal Entry with balanced
 *     debits and credits (Σ Debit == Σ Credit).
 *   - Posted journal entries are IMMUTABLE (audit trail integrity).
 *   - Corrections must use reversing/adjustment entries.
 *   - All monetary values use NUMERIC(15,4) to prevent floating-point errors.
 */

export type AccountType = 'Asset' | 'Liability' | 'Equity' | 'Revenue' | 'Expense';

export type JournalEntryStatus = 'Draft' | 'Posted' | 'Voided';

export interface ChartOfAccount {
  id: number;
  code: string;
  name: string;
  nameAr?: string;
  type: AccountType;
  parentId?: number;
  isActive: boolean;
  openingBalance: number;
  currencyCode: string;
}

export interface JournalEntry {
  id: number;
  entryNumber: string;
  entryDate: Date;
  reference?: string;
  referenceType?: string;
  referenceId?: number;
  description: string;
  descriptionEn?: string;
  status: JournalEntryStatus;
  createdBy?: number;
  approvedBy?: number;
  approvedAt?: Date;
  voidedBy?: number;
  voidedAt?: Date;
  voidReason?: string;
  companyId?: number;
  createdAt: Date;
}

export interface JournalEntryLine {
  id: number;
  journalEntryId: number;
  accountId: number;
  accountCode?: string;
  accountName?: string;
  description?: string;
  debit: number;
  credit: number;
  partnerId?: number;
  costCenterId?: number;
  projectId?: number;
}

export interface CreateJournalEntryData {
  entryDate: Date;
  description: string;
  descriptionEn?: string;
  reference?: string;
  referenceType?: string;
  referenceId?: number;
  createdBy?: number;
  companyId?: number;
  lines: CreateJournalEntryLineData[];
}

export interface CreateJournalEntryLineData {
  accountId: number;
  description?: string;
  debit: number;
  credit: number;
  partnerId?: number;
  costCenterId?: number;
  projectId?: number;
}

export interface JournalEntryWithLines extends JournalEntry {
  lines: JournalEntryLine[];
}

export interface AccountBalance {
  accountId: number;
  accountCode: string;
  accountName: string;
  accountType: AccountType;
  totalDebit: number;
  totalCredit: number;
  balance: number;
}

/**
 * Standard Chart of Accounts codes for Saudi ERP system
 *
 * Accounting Logic:
 *   - Assets: 1xxx (current: 11xx, non-current: 12xx)
 *   - Liabilities: 2xxx (current: 21xx, non-current: 22xx)
 *   - Equity: 3xxx
 *   - Revenue: 4xxx
 *   - Expenses: 5xxx (COGS: 51xx, Operating: 52xx)
 *   - Tax accounts: 213x (VAT Output), 122x (VAT Input)
 */
export const STANDARD_ACCOUNTS = {
  // Assets
  CASH: { code: '1110', name: 'Cash', nameAr: 'الصندوق', type: 'Asset' as AccountType },
  BANK: { code: '1120', name: 'Bank Accounts', nameAr: 'الحسابات البنكية', type: 'Asset' as AccountType },
  ACCOUNTS_RECEIVABLE: { code: '1130', name: 'Accounts Receivable', nameAr: 'المدينون', type: 'Asset' as AccountType },
  INVENTORY_ASSET: { code: '1210', name: 'Inventory', nameAr: 'المخزون', type: 'Asset' as AccountType },
  PREPAID_EXPENSES: { code: '1220', name: 'Prepaid Expenses', nameAr: 'المصروفات المدفوعة مقدماً', type: 'Asset' as AccountType },
  GRNI_ACCRUAL: { code: '1230', name: 'Goods Received Not Invoiced', nameAr: 'البضائع المستلمة غير المفوترة', type: 'Asset' as AccountType },
  VAT_INPUT: { code: '1240', name: 'VAT Input', nameAr: 'ضريبة القيمة المضافة (مدفوعة)', type: 'Asset' as AccountType },

  // Liabilities
  ACCOUNTS_PAYABLE: { code: '2110', name: 'Accounts Payable', nameAr: 'الدائنون', type: 'Liability' as AccountType },
  VAT_OUTPUT: { code: '2120', name: 'VAT Output', nameAr: 'ضريبة القيمة المضافة (مستحقة)', type: 'Liability' as AccountType },
  SALARIES_PAYABLE: { code: '2130', name: 'Salaries Payable', nameAr: 'الرواتب المستحقة', type: 'Liability' as AccountType },
  ACCRUED_EXPENSES: { code: '2140', name: 'Accrued Expenses', nameAr: 'المصروفات المستحقة', type: 'Liability' as AccountType },

  // Equity
  OWNER_EQUITY: { code: '3100', name: 'Owner Equity', nameAr: 'رأس المال', type: 'Equity' as AccountType },
  RETAINED_EARNINGS: { code: '3200', name: 'Retained Earnings', nameAr: 'الأرباح المحتجزة', type: 'Equity' as AccountType },

  // Revenue
  SALES_REVENUE: { code: '4100', name: 'Sales Revenue', nameAr: 'إيرادات المبيعات', type: 'Revenue' as AccountType },
  SALES_RETURNS: { code: '4200', name: 'Sales Returns', nameAr: 'مرتجعات المبيعات', type: 'Revenue' as AccountType },
  OTHER_INCOME: { code: '4300', name: 'Other Income', nameAr: 'إيرادات أخرى', type: 'Revenue' as AccountType },

  // Expenses
  COST_OF_GOODS_SOLD: { code: '5100', name: 'Cost of Goods Sold', nameAr: 'تكلفة البضاعة المباعة', type: 'Expense' as AccountType },
  SALARY_EXPENSE: { code: '5210', name: 'Salary Expense', nameAr: 'مصاريف الرواتب', type: 'Expense' as AccountType },
  BONUS_EXPENSE: { code: '5220', name: 'Bonus Expense', nameAr: 'مصاريف المكافآت', type: 'Expense' as AccountType },
  ALLOWANCE_EXPENSE: { code: '5230', name: 'Allowance Expense', nameAr: 'مصاريف البدلات', type: 'Expense' as AccountType },
  RENT_EXPENSE: { code: '5310', name: 'Rent Expense', nameAr: 'مصاريف الإيجار', type: 'Expense' as AccountType },
  UTILITIES_EXPENSE: { code: '5320', name: 'Utilities Expense', nameAr: 'مصاريف المرافق', type: 'Expense' as AccountType },
  DEPRECIATION: { code: '5400', name: 'Depreciation Expense', nameAr: 'مصاريف الإهلاك', type: 'Expense' as AccountType },
  OTHER_EXPENSE: { code: '5500', name: 'Other Expenses', nameAr: 'مصاريف أخرى', type: 'Expense' as AccountType },
} as const;
