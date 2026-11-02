/**
 * Payment Event Handler: Payment Received / Payment Made
 *
 * Accounting Logic for payment.received:
 *   When a customer payment is received:
 *
 *   1. DEBIT Cash (1111) or Bank (1121) depending on paymentMethod (Asset increases)
 *      - Cash-explicit methods (cash / نقدي / COD) -> 1111 Cash
 *      - All other methods (transfer, card, cheque, ...) -> 1121 Bank
 *      - Amount: payment amount
 *
 *   2. CREDIT Accounts Receivable (Asset decreases - customer owes less)
 *      - Account: 1130 - Accounts Receivable
 *      - Amount: payment amount
 *
 *   Journal Entry:
 *     Dr. Cash|Bank            (1111|1121)    amount
 *     Cr. Accounts Receivable  (1130)         amount
 *
 * Accounting Logic for payment.made:
 *   When a supplier payment is made:
 *
 *   1. DEBIT Accounts Payable (Liability decreases - we owe less)
 *      - Account: 2111 - Accounts Payable
 *      - Amount: payment amount
 *
 *   2. CREDIT Cash (1111) or Bank (1121) depending on paymentMethod (Asset decreases)
 *      - Cash-explicit methods -> 1111 Cash, otherwise -> 1121 Bank
 *
 *   Journal Entry:
 *     Dr. Accounts Payable    (2111)         amount
 *     Cr. Cash|Bank           (1111|1121)    amount
 */

import { PoolClient } from 'pg';
import { BaseEvent, PaymentReceivedPayload, PaymentMadePayload } from '../events/types';
import { postAndFinalizeEntry } from '../ledger/JournalEntryService';
import { CreateJournalEntryData, STANDARD_ACCOUNTS } from '../ledger/types';
import { logger } from '../../services/logger';
import { resolveAccounts, isCashPaymentMethod } from '../utils/accountResolver';

/**
 * Handle the payment.received event
 *
 * Creates a balanced journal entry debiting Bank (or Cash for cash payments)
 * and crediting AR.
 */
export async function handlePaymentReceived(
  event: BaseEvent<PaymentReceivedPayload>,
  client: PoolClient
): Promise<{ entryId: number; entryNumber: string }> {
  const { payload, metadata } = event;

  logger.info(
    `PaymentEventHandler: processing payment.received for customer "${payload.customerName}" ` +
    `(id: ${payload.paymentId}, amount: ${payload.amount}, method: ${payload.paymentMethod})`
  );

  // Resolve Account IDs (single query for performance).
  // Standard accounts: CASH=1111, BANK=1121.
  const accountCodes = [
    STANDARD_ACCOUNTS.CASH.code,
    STANDARD_ACCOUNTS.BANK.code,
    STANDARD_ACCOUNTS.ACCOUNTS_RECEIVABLE.code,
  ];
  const accounts = await resolveAccounts(client, accountCodes, metadata.companyId);

  const bankAccount = accounts.get(STANDARD_ACCOUNTS.BANK.code)!;
  const cashAccount = accounts.get(STANDARD_ACCOUNTS.CASH.code)!;
  const arAccount = accounts.get(STANDARD_ACCOUNTS.ACCOUNTS_RECEIVABLE.code)!;

  // Cash payments land in the Cash account; everything else in the Bank account.
  const useCash = isCashPaymentMethod(payload.paymentMethod);
  const fundsAccount = useCash ? cashAccount : bankAccount;

  // Build Journal Entry Lines
  const lines: CreateJournalEntryData['lines'] = [
    {
      accountId: fundsAccount.id,
      description: `Payment received from ${payload.customerName} via ${payload.paymentMethod}`,
      debit: payload.amount,
      credit: 0,
      partnerId: payload.customerId,
    },
    {
      accountId: arAccount.id,
      description: `Payment applied to ${payload.customerName} account`,
      debit: 0,
      credit: payload.amount,
      partnerId: payload.customerId,
    },
  ];

  // Post the Journal Entry
  const journalData: CreateJournalEntryData = {
    entryDate: new Date(),
    description: `Customer Payment - ${payload.customerName} (${payload.paymentMethod})`,
    descriptionEn: `Customer Payment - ${payload.customerName} (${payload.paymentMethod})`,
    referenceType: 'CustomerPayment',
    referenceId: payload.paymentId,
    createdBy: metadata.userId,
    companyId: metadata.companyId,
    lines,
  };

  const journalEntry = await postAndFinalizeEntry(journalData, client, metadata.userId);

  logger.info(
    `PaymentEventHandler: journal entry ${journalEntry.entryNumber} created for customer payment ` +
    `| Dr. ${useCash ? 'Cash' : 'Bank'}: ${payload.amount} | Cr. AR: ${payload.amount} | Customer: ${payload.customerName}`
  );

  // Return the created entry so the backend links customer_payments.journal_entry_id
  // within its OWN transaction. We deliberately avoid updating `customer_payments`
  // here: the operational transaction is still open on the backend connection, and
  // an UPDATE from this separate connection would block on the uncommitted row
  // (cross-transaction deadlock).
  return { entryId: journalEntry.id, entryNumber: journalEntry.entryNumber };
}

/**
 * Handle the payment.made event
 *
 * Creates a balanced journal entry debiting AP and crediting Bank (or Cash
 * for cash payments).
 */
export async function handlePaymentMade(
  event: BaseEvent<PaymentMadePayload>,
  client: PoolClient
): Promise<{ entryId: number; entryNumber: string }> {
  const { payload, metadata } = event;

  logger.info(
    `PaymentEventHandler: processing payment.made for supplier "${payload.supplierName}" ` +
    `(id: ${payload.paymentId}, amount: ${payload.amount}, method: ${payload.paymentMethod})`
  );

  // Resolve Account IDs (single query for performance).
  // Standard accounts: CASH=1111, BANK=1121.
  const accountCodes = [
    STANDARD_ACCOUNTS.ACCOUNTS_PAYABLE.code,
    STANDARD_ACCOUNTS.CASH.code,
    STANDARD_ACCOUNTS.BANK.code,
  ];
  const accounts = await resolveAccounts(client, accountCodes, metadata.companyId);

  const apAccount = accounts.get(STANDARD_ACCOUNTS.ACCOUNTS_PAYABLE.code)!;
  const bankAccount = accounts.get(STANDARD_ACCOUNTS.BANK.code)!;
  const cashAccount = accounts.get(STANDARD_ACCOUNTS.CASH.code)!;

  // Cash payments come out of the Cash account; everything else from Bank.
  const useCash = isCashPaymentMethod(payload.paymentMethod);
  const fundsAccount = useCash ? cashAccount : bankAccount;

  // Build Journal Entry Lines
  const lines: CreateJournalEntryData['lines'] = [
    {
      accountId: apAccount.id,
      description: `Payment to ${payload.supplierName} via ${payload.paymentMethod}`,
      debit: payload.amount,
      credit: 0,
      partnerId: payload.supplierId,
    },
    {
      accountId: fundsAccount.id,
      description: `Payment made to ${payload.supplierName}`,
      debit: 0,
      credit: payload.amount,
      partnerId: payload.supplierId,
    },
  ];

  // Post the Journal Entry
  const journalData: CreateJournalEntryData = {
    entryDate: new Date(),
    description: `Supplier Payment - ${payload.supplierName} (${payload.paymentMethod})`,
    descriptionEn: `Supplier Payment - ${payload.supplierName} (${payload.paymentMethod})`,
    referenceType: 'SupplierPayment',
    referenceId: payload.paymentId,
    createdBy: metadata.userId,
    companyId: metadata.companyId,
    lines,
  };

  const journalEntry = await postAndFinalizeEntry(journalData, client, metadata.userId);

  logger.info(
    `PaymentEventHandler: journal entry ${journalEntry.entryNumber} created for supplier payment ` +
    `| Dr. AP: ${payload.amount} | Cr. ${useCash ? 'Cash' : 'Bank'}: ${payload.amount} | Supplier: ${payload.supplierName}`
  );

  // Return the created entry so the backend links supplier_payments.journal_entry_id
  // within its OWN transaction (avoids cross-transaction deadlock on the uncommitted row).
  return { entryId: journalEntry.id, entryNumber: journalEntry.entryNumber };
}
