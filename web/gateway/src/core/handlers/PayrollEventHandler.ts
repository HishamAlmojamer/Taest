/**
 * Payroll Event Handler: Payroll Approved
 *
 * Accounting Logic for payroll.approved:
 *   When an employee's payroll is approved, the system must:
 *
 *   1. DEBIT Salary Expense (Expense increases with debit)
 *      - Account: 5210 - Salary Expense
 *      - Amount: basicSalary
 *
 *   2. DEBIT Allowance Expense (if applicable)
 *      - Account: 5230 - Allowance Expense
 *      - Amount: totalAllowances (housing + transport + other)
 *
 *   3. DEBIT Bonus Expense (if applicable)
 *      - Account: 5220 - Bonus Expense
 *      - Amount: bonus
 *
 *   4. CREDIT Salaries Payable (Liability increases with credit)
 *      - Account: 2130 - Salaries Payable
 *      - Amount: netSalary (what we owe the employee)
 *
 *   5. CREDIT Deductions (if applicable)
 *      - Various liability accounts
 *      - Amount: deductions
 *
 *   Journal Entry:
 *     Dr. Salary Expense       (5210)    basicSalary
 *     Dr. Allowance Expense    (5230)    totalAllowances
 *     Dr. Bonus Expense        (5220)    bonus
 *     Cr. Salaries Payable     (2130)    netSalary + deductions
 *     Cr. Deductions Payable   (2140)    deductions
 *
 *   Double-Entry Verification:
 *     Dr. Total = basicSalary + totalAllowances + bonus
 *     Cr. Total = netSalary + deductions
 *     Since: netSalary = basicSalary + totalAllowances + overtime + bonus - deductions
 *     Then: Cr. Total = (basicSalary + totalAllowances + overtime + bonus - deductions) + deductions
 *                     = basicSalary + totalAllowances + overtime + bonus
 *     Dr. Total = basicSalary + totalAllowances + bonus + overtime
 *     Sum(Debit) = Sum(Credit) ✓
 *
 *   Note: Overtime is included in the salary expense line
 */

import { PoolClient } from 'pg';
import { BaseEvent, PayrollApprovedPayload, PayrollSettledPayload } from '../events/types';
import { postAndFinalizeEntry, voidJournalEntry } from '../ledger/JournalEntryService';
import { CreateJournalEntryData, CreateJournalEntryLineData, STANDARD_ACCOUNTS } from '../ledger/types';
import { logger } from '../../services/logger';
import { resolveAccounts } from '../utils/accountResolver';

/**
 * Handle the payroll.approved event
 *
 * Creates a balanced journal entry recording salary expenses
 * and the corresponding liability to pay the employee.
 *
 * @param event - The payroll approved event
 * @param client - Active PoolClient within the caller's transaction
 */
export async function handlePayrollApproved(
  event: BaseEvent<PayrollApprovedPayload>,
  client: PoolClient
): Promise<{ entryId: number; entryNumber: string }> {
  const { payload, metadata } = event;

  logger.info(
    `PayrollEventHandler: processing payroll.approved for employee "${payload.employeeName}" ` +
    `(code: ${payload.employeeCode}, period: ${payload.periodMonth}/${payload.periodYear}, ` +
    `net: ${payload.netSalary})`
  );

  // ==========================================
  // STEP 1: Resolve Account IDs (single query for performance)
  // ==========================================
  const accountCodes = [
    STANDARD_ACCOUNTS.SALARY_EXPENSE.code,
    STANDARD_ACCOUNTS.BONUS_EXPENSE.code,
    STANDARD_ACCOUNTS.ALLOWANCE_EXPENSE.code,
    STANDARD_ACCOUNTS.SALARIES_PAYABLE.code,
    STANDARD_ACCOUNTS.ACCRUED_EXPENSES.code,
    STANDARD_ACCOUNTS.EMPLOYEE_ADVANCES.code,
  ];
  const accounts = await resolveAccounts(client, accountCodes, metadata.companyId);

  const salaryExpenseAccount = accounts.get(STANDARD_ACCOUNTS.SALARY_EXPENSE.code)!;
  const bonusExpenseAccount = accounts.get(STANDARD_ACCOUNTS.BONUS_EXPENSE.code)!;
  const allowanceExpenseAccount = accounts.get(STANDARD_ACCOUNTS.ALLOWANCE_EXPENSE.code)!;
  const salariesPayableAccount = accounts.get(STANDARD_ACCOUNTS.SALARIES_PAYABLE.code)!;
  const accruedExpensesAccount = accounts.get(STANDARD_ACCOUNTS.ACCRUED_EXPENSES.code)!;
  const employeeAdvancesAccount = accounts.get(STANDARD_ACCOUNTS.EMPLOYEE_ADVANCES.code)!;

  // ==========================================
  // STEP 2: Build Journal Entry Lines
  // ==========================================
  const lines: CreateJournalEntryData['lines'] = [];

  // LINE 1: DEBIT Salary Expense
  // Basic salary is a core expense for the company
  if (payload.basicSalary > 0) {
    lines.push({
      accountId: salaryExpenseAccount.id,
      description: `Salary: ${payload.employeeName} (${payload.periodMonth}/${payload.periodYear})`,
      debit: payload.basicSalary + payload.overtime, // Include overtime in salary expense
      credit: 0,
    });
  }

  // LINE 2: DEBIT Allowance Expense
  // Housing, transportation, and other allowances
  if (payload.totalAllowances > 0) {
    lines.push({
      accountId: allowanceExpenseAccount.id,
      description: `Allowances: ${payload.employeeName} (H: ${payload.housingAllowance}, T: ${payload.transportationAllowance}, O: ${payload.otherAllowances})`,
      debit: payload.totalAllowances,
      credit: 0,
    });
  }

  // LINE 3: DEBIT Bonus Expense
  if (payload.bonus > 0) {
    lines.push({
      accountId: bonusExpenseAccount.id,
      description: `Bonus: ${payload.employeeName}`,
      debit: payload.bonus,
      credit: 0,
    });
  }

  // LINE 4: CREDIT Salaries Payable
  // The net amount we owe to the employee
  lines.push({
    accountId: salariesPayableAccount.id,
    description: `Net salary payable: ${payload.employeeName}`,
    debit: 0,
    credit: payload.netSalary,
  });

  // LINE 5: CREDIT Deductions
  // Advance installments reduce the Employee Advances asset,
  // other deductions are withheld (accrued expense).
  const advanceDeduction = payload.advanceDeduction || 0;
  const otherDeductions = payload.deductions - advanceDeduction;
  if (otherDeductions > 0) {
    lines.push({
      accountId: accruedExpensesAccount.id,
      description: `Deductions: ${payload.employeeName}`,
      debit: 0,
      credit: otherDeductions,
    });
  }
  if (advanceDeduction > 0) {
    lines.push({
      accountId: employeeAdvancesAccount.id,
      description: `Advance installment: ${payload.employeeName}`,
      debit: 0,
      credit: advanceDeduction,
    });
  }

  // ==========================================
  // STEP 3: Validate Balance
  // ==========================================
  const totalDebit = lines.reduce((sum: number, l: CreateJournalEntryLineData) => sum + l.debit, 0);
  const totalCredit = lines.reduce((sum: number, l: CreateJournalEntryLineData) => sum + l.credit, 0);

  logger.info(
    `PayrollEventHandler: balance check - Debits: ${totalDebit}, Credits: ${totalCredit}, ` +
    `Difference: ${Math.abs(totalDebit - totalCredit)}`
  );

  // ==========================================
  // STEP 4: Post the Journal Entry
  // ==========================================
  const periodLabel = `${payload.periodMonth}/${payload.periodYear}`;

  const journalData: CreateJournalEntryData = {
    entryDate: new Date(),
    description: `Payroll ${periodLabel} - ${payload.employeeName} (${payload.employeeCode})`,
    descriptionEn: `Payroll ${periodLabel} - ${payload.employeeName} (${payload.employeeCode})`,
    referenceType: 'Payroll',
    referenceId: payload.payrollId,
    createdBy: metadata.userId,
    companyId: metadata.companyId,
    lines,
  };

  const journalEntry = await postAndFinalizeEntry(journalData, client, metadata.userId);

  logger.info(
    `PayrollEventHandler: journal entry ${journalEntry.entryNumber} created for payroll ` +
    `| Dr. Salary: ${payload.basicSalary} | Dr. Allowances: ${payload.totalAllowances} | ` +
    `Dr. Bonus: ${payload.bonus} | Cr. Payable: ${payload.netSalary} | Cr. Deductions: ${payload.deductions}`
  );

  return { entryId: journalEntry.id, entryNumber: journalEntry.entryNumber };
}

/**
 * Handle the payroll.voided event
 *
 * When payroll is voided, reverse the original journal entry.
 *
 * @param event - The payroll voided event
 * @param client - Active PoolClient within the caller's transaction
 */
export async function handlePayrollVoided(
  event: BaseEvent<{ payrollId: number; employeeId: number; originalEntryId: number; reason: string }>,
  client: PoolClient
): Promise<void> {
  const { payload, metadata } = event;

  logger.info(
    `PayrollEventHandler: processing payroll.voided for payroll ${payload.payrollId} ` +
    `(original entry: ${payload.originalEntryId})`
  );

  // Step 1: Void the original journal entry (creates reversing entry).
  // Fail loudly if the original posting is missing rather than silently
  // leaving the payroll accrual unreversed.
  if (!payload.originalEntryId) {
    throw new Error(
      `PayrollEventHandler: cannot void payroll ${payload.payrollId} - ` +
      `no original journal entry found (payroll was never posted).`
    );
  }
  await voidJournalEntry(
    payload.originalEntryId,
    `Voided payroll for employee ${payload.employeeId}: ${payload.reason}`,
    client,
    metadata.userId
  );

  logger.info(
    `PayrollEventHandler: payroll ${payload.payrollId} voided successfully`
  );
}

/**
 * Handle the payroll.settled event
 *
 * Accounting Logic for payroll.settled:
 *   When an approved payroll is actually paid out (from bank or cash),
 *   the company's obligation to the employee (Salaries Payable) is cleared:
 *
 *   1. DEBIT Salaries Payable (Liability decreases with debit)
 *      - Account: 2130 - Salaries Payable
 *      - Amount: netSalary
 *
 *   2. CREDIT Bank/Cash (Asset decreases with credit)
 *      - Account: 1120 - Bank Accounts (default) or 1110 - Cash
 *      - Amount: netSalary
 *
 *   Journal Entry:
 *     Dr. Salaries Payable  (2130)    netSalary
 *     Cr. Bank/Cash         (1120/1110) netSalary
 *
 *   Double-Entry Verification:
 *     Dr. Total = netSalary
 *     Cr. Total = netSalary
 *     Sum(Debit) = Sum(Credit) ✓
 *
 * @param event - The payroll settled event
 * @param client - Active PoolClient within the caller's transaction
 */
export async function handlePayrollSettled(
  event: BaseEvent<PayrollSettledPayload>,
  client: PoolClient
): Promise<{ entryId: number; entryNumber: string }> {
  const { payload, metadata } = event;

  logger.info(
    `PayrollEventHandler: processing payroll.settled for employee "${payload.employeeName}" ` +
    `(period: ${payload.periodMonth}/${payload.periodYear}, net: ${payload.netSalary}, method: ${payload.paymentMethod})`
  );

  const paymentMethod = (payload.paymentMethod || 'BANK').toUpperCase();
  const isCash = paymentMethod.includes('CASH');

  // ==========================================
  // STEP 1: Resolve Account IDs
  // ==========================================
  const accountCodes = [
    STANDARD_ACCOUNTS.SALARIES_PAYABLE.code,
    isCash ? STANDARD_ACCOUNTS.CASH.code : STANDARD_ACCOUNTS.BANK.code,
  ];
  const accounts = await resolveAccounts(client, accountCodes, metadata.companyId);

  const salariesPayableAccount = accounts.get(STANDARD_ACCOUNTS.SALARIES_PAYABLE.code)!;
  const fundingAccount = accounts.get(isCash ? STANDARD_ACCOUNTS.CASH.code : STANDARD_ACCOUNTS.BANK.code)!;

  // ==========================================
  // STEP 2: Build Journal Entry Lines
  // ==========================================
  const lines: CreateJournalEntryData['lines'] = [];

  // LINE 1: DEBIT Salaries Payable (clear the obligation)
  lines.push({
    accountId: salariesPayableAccount.id,
    description: `Salary payment: ${payload.employeeName} (${payload.periodMonth}/${payload.periodYear})`,
    debit: payload.netSalary,
    credit: 0,
  });

  // LINE 2: CREDIT Bank/Cash (money leaves the company)
  lines.push({
    accountId: fundingAccount.id,
    description: `Salary payment via ${isCash ? 'cash' : 'bank'}: ${payload.employeeName}`,
    debit: 0,
    credit: payload.netSalary,
  });

  // ==========================================
  // STEP 3: Post the Journal Entry
  // ==========================================
  const periodLabel = `${payload.periodMonth}/${payload.periodYear}`;

  const journalData: CreateJournalEntryData = {
    entryDate: payload.paymentDate ? new Date(payload.paymentDate) : new Date(),
    description: `Payroll settlement ${periodLabel} - ${payload.employeeName} (${isCash ? 'cash' : payload.bankAccountName || 'bank'})`,
    descriptionEn: `Payroll settlement ${periodLabel} - ${payload.employeeName}`,
    referenceType: 'PayrollSettlement',
    referenceId: payload.payrollId,
    createdBy: metadata.userId,
    companyId: metadata.companyId,
    lines,
  };

  const journalEntry = await postAndFinalizeEntry(journalData, client, metadata.userId);

  logger.info(
    `PayrollEventHandler: journal entry ${journalEntry.entryNumber} created for payroll settlement ` +
    `| Dr. Salaries Payable: ${payload.netSalary} | Cr. ${isCash ? 'Cash' : 'Bank'}: ${payload.netSalary}`
  );

  return { entryId: journalEntry.id, entryNumber: journalEntry.entryNumber };
}
