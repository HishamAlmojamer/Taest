/**
 * Employee Advance Event Handler: Grant / Repaid / Voided
 *
 * Accounting Logic for employee advances (سلف الموظفين):
 *
 * employee.advance.granted:
 *   When an advance is given to an employee (money leaves the company):
 *
 *   1. DEBIT Employee Advances (Asset increases with debit)
 *      - Account: 1131 - Employee Advances
 *      - Amount: amount
 *
 *   2. CREDIT Bank/Cash (Asset decreases with credit)
 *      - Account: 1120 - Bank Accounts (default) or 1110 - Cash
 *      - Amount: amount
 *
 *   Journal Entry:
 *     Dr. Employee Advances (1131)    amount
 *     Cr. Bank/Cash          (1120/1110) amount
 *
 * employee.advance.repaid:
 *   When the employee repays the advance (money returns to the company):
 *
 *   1. DEBIT Bank/Cash
 *      - Amount: amount
 *   2. CREDIT Employee Advances
 *      - Amount: amount
 *
 *   Journal Entry:
 *     Dr. Bank/Cash (1120/1110)       amount
 *     Cr. Employee Advances (1131)    amount
 *
 * employee.advance.voided:
 *   Reverses the original grant journal entry (voidJournalEntry).
 */

import { PoolClient } from 'pg';
import {
  BaseEvent,
  EmployeeAdvanceGrantedPayload,
  EmployeeAdvanceRepaidPayload,
  EmployeeAdvanceVoidedPayload,
} from '../events/types';
import { postAndFinalizeEntry, voidJournalEntry } from '../ledger/JournalEntryService';
import { CreateJournalEntryData, CreateJournalEntryLineData, STANDARD_ACCOUNTS } from '../ledger/types';
import { logger } from '../../services/logger';
import { resolveAccounts } from '../utils/accountResolver';

/**
 * Handle the employee.advance.granted event
 *
 * @param event - The advance granted event
 * @param client - Active PoolClient within the caller's transaction
 */
export async function handleEmployeeAdvanceGranted(
  event: BaseEvent<EmployeeAdvanceGrantedPayload>,
  client: PoolClient
): Promise<{ entryId: number; entryNumber: string }> {
  const { payload, metadata } = event;

  logger.info(
    `AdvanceEventHandler: processing employee.advance.granted for employee "${payload.employeeName}" ` +
    `(code: ${payload.employeeCode}, amount: ${payload.amount}, method: ${payload.paymentMethod})`
  );

  const paymentMethod = (payload.paymentMethod || 'BANK').toUpperCase();
  const isCash = paymentMethod.includes('CASH');

  // ==========================================
  // STEP 1: Resolve Account IDs
  // ==========================================
  const accountCodes = [
    STANDARD_ACCOUNTS.EMPLOYEE_ADVANCES.code,
    isCash ? STANDARD_ACCOUNTS.CASH.code : STANDARD_ACCOUNTS.BANK.code,
  ];
  const accounts = await resolveAccounts(client, accountCodes, metadata.companyId);

  const employeeAdvancesAccount = accounts.get(STANDARD_ACCOUNTS.EMPLOYEE_ADVANCES.code)!;
  const fundingAccount = accounts.get(isCash ? STANDARD_ACCOUNTS.CASH.code : STANDARD_ACCOUNTS.BANK.code)!;

  // ==========================================
  // STEP 2: Build Journal Entry Lines
  // ==========================================
  const lines: CreateJournalEntryData['lines'] = [];

  // LINE 1: DEBIT Employee Advances (receivable from the employee)
  lines.push({
    accountId: employeeAdvancesAccount.id,
    description: `Advance (${payload.advanceType}): ${payload.employeeName}`,
    debit: payload.amount,
    credit: 0,
  });

  // LINE 2: CREDIT Bank/Cash (money leaves the company)
  lines.push({
    accountId: fundingAccount.id,
    description: `Advance paid via ${isCash ? 'cash' : 'bank'}: ${payload.employeeName}`,
    debit: 0,
    credit: payload.amount,
  });

  // ==========================================
  // STEP 3: Post the Journal Entry
  // ==========================================
  const journalData: CreateJournalEntryData = {
    entryDate: payload.requestDate ? new Date(payload.requestDate) : new Date(),
    description: `Employee advance (${payload.advanceType}) - ${payload.employeeName} (${payload.employeeCode})`,
    descriptionEn: `Employee advance - ${payload.employeeName}`,
    referenceType: 'EmployeeAdvance',
    referenceId: payload.advanceId,
    createdBy: metadata.userId,
    companyId: metadata.companyId,
    lines,
  };

  const journalEntry = await postAndFinalizeEntry(journalData, client, metadata.userId);

  logger.info(
    `AdvanceEventHandler: journal entry ${journalEntry.entryNumber} created for advance grant ` +
    `| Dr. Employee Advances: ${payload.amount} | Cr. ${isCash ? 'Cash' : 'Bank'}: ${payload.amount}`
  );

  return { entryId: journalEntry.id, entryNumber: journalEntry.entryNumber };
}

/**
 * Handle the employee.advance.repaid event
 *
 * @param event - The advance repaid event
 * @param client - Active PoolClient within the caller's transaction
 */
export async function handleEmployeeAdvanceRepaid(
  event: BaseEvent<EmployeeAdvanceRepaidPayload>,
  client: PoolClient
): Promise<void> {
  const { payload, metadata } = event;

  logger.info(
    `AdvanceEventHandler: processing employee.advance.repaid for employee "${payload.employeeName}" ` +
    `(advance: ${payload.advanceId}, amount: ${payload.amount}, method: ${payload.paymentMethod})`
  );

  const paymentMethod = (payload.paymentMethod || 'CASH').toUpperCase();
  const isCash = paymentMethod.includes('CASH');

  // ==========================================
  // STEP 1: Resolve Account IDs
  // ==========================================
  const accountCodes = [
    STANDARD_ACCOUNTS.EMPLOYEE_ADVANCES.code,
    isCash ? STANDARD_ACCOUNTS.CASH.code : STANDARD_ACCOUNTS.BANK.code,
  ];
  const accounts = await resolveAccounts(client, accountCodes, metadata.companyId);

  const employeeAdvancesAccount = accounts.get(STANDARD_ACCOUNTS.EMPLOYEE_ADVANCES.code)!;
  const fundingAccount = accounts.get(isCash ? STANDARD_ACCOUNTS.CASH.code : STANDARD_ACCOUNTS.BANK.code)!;

  // ==========================================
  // STEP 2: Build Journal Entry Lines
  // ==========================================
  const lines: CreateJournalEntryData['lines'] = [];

  // LINE 1: DEBIT Bank/Cash (money returns to the company)
  lines.push({
    accountId: fundingAccount.id,
    description: `Advance repayment via ${isCash ? 'cash' : 'bank'}: ${payload.employeeName}`,
    debit: payload.amount,
    credit: 0,
  });

  // LINE 2: CREDIT Employee Advances (receivable is reduced)
  lines.push({
    accountId: employeeAdvancesAccount.id,
    description: `Advance repayment: ${payload.employeeName}`,
    debit: 0,
    credit: payload.amount,
  });

  // ==========================================
  // STEP 3: Post the Journal Entry
  // ==========================================
  const journalData: CreateJournalEntryData = {
    entryDate: payload.repaymentDate ? new Date(payload.repaymentDate) : new Date(),
    description: `Employee advance repayment - ${payload.employeeName}`,
    descriptionEn: `Employee advance repayment - ${payload.employeeName}`,
    referenceType: 'EmployeeAdvanceRepayment',
    referenceId: payload.advanceId,
    createdBy: metadata.userId,
    companyId: metadata.companyId,
    lines,
  };

  const journalEntry = await postAndFinalizeEntry(journalData, client, metadata.userId);

  logger.info(
    `AdvanceEventHandler: journal entry ${journalEntry.entryNumber} created for advance repayment ` +
    `| Dr. ${isCash ? 'Cash' : 'Bank'}: ${payload.amount} | Cr. Employee Advances: ${payload.amount}`
  );
}

/**
 * Handle the employee.advance.voided event
 *
 * When an advance is voided, reverse the original grant journal entry.
 *
 * @param event - The advance voided event
 * @param client - Active PoolClient within the caller's transaction
 */
export async function handleEmployeeAdvanceVoided(
  event: BaseEvent<EmployeeAdvanceVoidedPayload>,
  client: PoolClient
): Promise<void> {
  const { payload, metadata } = event;

  logger.info(
    `AdvanceEventHandler: processing employee.advance.voided for advance ${payload.advanceId} ` +
    `(original entry: ${payload.originalEntryId})`
  );

  // Step 1: Void the original journal entry (creates reversing entry).
  // Fail loudly if the original posting is missing rather than silently
  // leaving the advance postings unreversed.
  if (!payload.originalEntryId) {
    throw new Error(
      `AdvanceEventHandler: cannot void advance ${payload.advanceId} - ` +
      `no original journal entry found (advance was never paid).`
    );
  }
  await voidJournalEntry(
    payload.originalEntryId,
    `Voided advance for employee ${payload.employeeId}: ${payload.reason}`,
    client,
    metadata.userId
  );

  logger.info(
    `AdvanceEventHandler: advance ${payload.advanceId} voided successfully`
  );
}
