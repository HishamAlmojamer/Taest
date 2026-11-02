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
 * These codes map to the canonical `accounts` table (FastAPI chart of accounts).
 * The gateway resolves accounts from `accounts` by `account_code`, so the codes
 * below must exist in that table.
 *
 * Accounting Logic:
 *   - Assets: 1xxx (current: 11xx, non-current: 12xx)
 *   - Liabilities: 2xxx (current: 21xx, non-current: 22xx)
 *   - Equity: 3xxx
 *   - Revenue: 4xxx
 *   - Expenses: 5xxx (COGS: 51xx, Operating: 52xx)
 *   - Tax accounts: 2121 (VAT Output), 1400 (VAT Input)
 */
export const STANDARD_ACCOUNTS = {
  // Assets
  CASH: { code: '1111', name: 'Main Cash Drawer', nameAr: 'الصندوق الرئيسي', type: 'Asset' as AccountType },
  BANK: { code: '1121', name: 'Bank Accounts', nameAr: 'بنك الأهلي السعودي', type: 'Asset' as AccountType },
  ACCOUNTS_RECEIVABLE: { code: '1201', name: 'Accounts Receivable', nameAr: 'حسابات العملاء', type: 'Asset' as AccountType },
  OTHER_RECEIVABLES: { code: '1202', name: 'Other Receivables', nameAr: 'ديون مدينة مختلفة', type: 'Asset' as AccountType },
  EMPLOYEE_ADVANCES: { code: '1203', name: 'Employee Advances', nameAr: 'سلف موظفين', type: 'Asset' as AccountType },
  CHEQUES_ON_HAND: { code: '1205', name: 'Cheques on Hand', nameAr: 'شيكات تحت التحصيل', type: 'Asset' as AccountType },
  INVENTORY_ASSET: { code: '1301', name: 'Inventory - Finished Goods', nameAr: 'المخزون - بضائع تامة', type: 'Asset' as AccountType },
  PREPAID_EXPENSES: { code: '1210', name: 'Prepaid Expenses', nameAr: 'مصروفات مدفوعة مقدماً', type: 'Asset' as AccountType },
  GRNI_ACCRUAL: { code: '1303', name: 'Goods Received Not Invoiced', nameAr: 'بضائع مستلمة غير مفوترة', type: 'Asset' as AccountType },
  VAT_INPUT: { code: '1400', name: 'VAT Input', nameAr: 'ضريبة القيمة المضافة (مدفوعة)', type: 'Asset' as AccountType },

  // Liabilities
  ACCOUNTS_PAYABLE: { code: '2111', name: 'Accounts Payable', nameAr: 'حسابات الموردين', type: 'Liability' as AccountType },
  CHEQUES_ISSUED: { code: '2124', name: 'Cheques Issued', nameAr: 'شيكات مسحوبة', type: 'Liability' as AccountType },
  VAT_OUTPUT: { code: '2121', name: 'VAT Output', nameAr: 'ضريبة القيمة المضافة المستحقة', type: 'Liability' as AccountType },
  SALARIES_PAYABLE: { code: '2131', name: 'Salaries Payable', nameAr: 'رواتب مستحقة', type: 'Liability' as AccountType },
  ACCRUED_EXPENSES: { code: '2133', name: 'Other Accrued Expenses', nameAr: 'مصروفات أخرى مستحقة', type: 'Liability' as AccountType },

  // Equity
  OWNER_EQUITY: { code: '3100', name: 'Capital', nameAr: 'رأس المال', type: 'Equity' as AccountType },
  RETAINED_EARNINGS: { code: '3400', name: 'Retained Earnings', nameAr: 'أرباح محتجزة', type: 'Equity' as AccountType },

  // Revenue
  SALES_REVENUE: { code: '4110', name: 'Local Sales', nameAr: 'مبيعات محلية', type: 'Revenue' as AccountType },
  SALES_RETURNS: { code: '4210', name: 'Local Sales Returns', nameAr: 'مرتجعات مبيعات محلية', type: 'Revenue' as AccountType },
  OTHER_INCOME: { code: '4430', name: 'Miscellaneous Income', nameAr: 'إيرادات أخرى مختلفة', type: 'Revenue' as AccountType },

  // Expenses
  COST_OF_GOODS_SOLD: { code: '5110', name: 'Cost of Sales', nameAr: 'تكلفة المبيعات', type: 'Expense' as AccountType },
  SALARY_EXPENSE: { code: '5210', name: 'Salaries', nameAr: 'رواتب', type: 'Expense' as AccountType },
  BONUS_EXPENSE: { code: '5220', name: 'Bonuses', nameAr: 'مكافآت', type: 'Expense' as AccountType },
  ALLOWANCE_EXPENSE: { code: '5230', name: 'Allowances', nameAr: 'بدلات', type: 'Expense' as AccountType },
  RENT_EXPENSE: { code: '5310', name: 'Rent', nameAr: 'إيجار', type: 'Expense' as AccountType },
  UTILITIES_EXPENSE: { code: '5320', name: 'Utilities', nameAr: 'مرافق', type: 'Expense' as AccountType },
  DEPRECIATION: { code: '5600', name: 'Depreciation Expense', nameAr: 'مصروفات الإهلاك', type: 'Expense' as AccountType },
  OTHER_EXPENSE: { code: '5710', name: 'Miscellaneous Expense', nameAr: 'مصروفات مختلفة', type: 'Expense' as AccountType },
} as const;
