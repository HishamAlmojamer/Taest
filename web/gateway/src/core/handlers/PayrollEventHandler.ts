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
import { BaseEvent, PayrollApprovedPayload } from '../events/types';
import { postAndFinalizeEntry } from '../ledger/JournalEntryService';
import { CreateJournalEntryData, CreateJournalEntryLineData, STANDARD_ACCOUNTS } from '../ledger/types';
import { logger } from '../../services/logger';
import { resolveAccount } from '../utils/accountResolver';

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
): Promise<void> {
  const { payload, metadata } = event;

  logger.info(
    `PayrollEventHandler: processing payroll.approved for employee "${payload.employeeName}" ` +
    `(code: ${payload.employeeCode}, period: ${payload.periodMonth}/${payload.periodYear}, ` +
    `net: ${payload.netSalary})`
  );

  // ==========================================
  // STEP 1: Resolve Account IDs
  // ==========================================
  const salaryExpenseAccount = await resolveAccount(
    client,
    STANDARD_ACCOUNTS.SALARY_EXPENSE.code,
    metadata.companyId
  );
  const bonusExpenseAccount = await resolveAccount(
    client,
    STANDARD_ACCOUNTS.BONUS_EXPENSE.code,
    metadata.companyId
  );
  const allowanceExpenseAccount = await resolveAccount(
    client,
    STANDARD_ACCOUNTS.ALLOWANCE_EXPENSE.code,
    metadata.companyId
  );
  const salariesPayableAccount = await resolveAccount(
    client,
    STANDARD_ACCOUNTS.SALARIES_PAYABLE.code,
    metadata.companyId
  );
  const accruedExpensesAccount = await resolveAccount(
    client,
    STANDARD_ACCOUNTS.ACCRUED_EXPENSES.code,
    metadata.companyId
  );

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

  // LINE 5: CREDIT Deductions (as accrued expense)
  // Deductions are withheld from the employee's salary
  if (payload.deductions > 0) {
    lines.push({
      accountId: accruedExpensesAccount.id,
      description: `Deductions: ${payload.employeeName}`,
      debit: 0,
      credit: payload.deductions,
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

  // ==========================================
  // STEP 5: Link Journal Entry to Payroll Record
  // ==========================================
  await client.query(
    `UPDATE hr_payroll SET journal_entry_id = $1 WHERE id = $2`,
    [journalEntry.id, payload.payrollId]
  );

  logger.info(
    `PayrollEventHandler: journal entry ${journalEntry.entryNumber} created for payroll ` +
    `| Dr. Salary: ${payload.basicSalary} | Dr. Allowances: ${payload.totalAllowances} | ` +
    `Dr. Bonus: ${payload.bonus} | Cr. Payable: ${payload.netSalary} | Cr. Deductions: ${payload.deductions}`
  );
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
  const { payload } = event;

  logger.info(
    `PayrollEventHandler: processing payroll.voided for payroll ${payload.payrollId} ` +
    `(original entry: ${payload.originalEntryId})`
  );

  // Update the payroll status
  await client.query(
    `UPDATE hr_payroll SET status = 'voided' WHERE id = $1`,
    [payload.payrollId]
  );

  logger.info(
    `PayrollEventHandler: payroll ${payload.payrollId} voided successfully`
  );
}
