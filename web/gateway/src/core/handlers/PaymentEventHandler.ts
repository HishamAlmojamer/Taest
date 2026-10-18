/**
 * Payment Event Handler: Payment Received / Payment Made
 *
 * Accounting Logic for payment.received:
 *   When a customer payment is received:
 *
 *   1. DEBIT Bank/Cash (Asset increases)
 *      - Account: 1120 - Bank Account
 *      - Amount: payment amount
 *
 *   2. CREDIT Accounts Receivable (Asset decreases - customer owes less)
 *      - Account: 1130 - Accounts Receivable
 *      - Amount: payment amount
 *
 *   Journal Entry:
 *     Dr. Bank Account        (1120)    amount
 *     Cr. Accounts Receivable  (1130)    amount
 *
 * Accounting Logic for payment.made:
 *   When a supplier payment is made:
 *
 *   1. DEBIT Accounts Payable (Liability decreases - we owe less)
 *      - Account: 2110 - Accounts Payable
 *      - Amount: payment amount
 *
 *   2. CREDIT Bank/Cash (Asset decreases)
 *      - Account: 1120 - Bank Account
 *      - Amount: payment amount
 *
 *   Journal Entry:
 *     Dr. Accounts Payable    (2110)    amount
 *     Cr. Bank Account        (1120)    amount
 */

import { PoolClient } from 'pg';
import { BaseEvent, PaymentReceivedPayload, PaymentMadePayload } from '../events/types';
import { postAndFinalizeEntry } from '../ledger/JournalEntryService';
import { CreateJournalEntryData, STANDARD_ACCOUNTS } from '../ledger/types';
import { logger } from '../../services/logger';
import { resolveAccount } from '../utils/accountResolver';

/**
 * Handle the payment.received event
 *
 * Creates a balanced journal entry debiting Bank and crediting AR.
 */
export async function handlePaymentReceived(
  event: BaseEvent<PaymentReceivedPayload>,
  client: PoolClient
): Promise<void> {
  const { payload, metadata } = event;

  logger.info(
    `PaymentEventHandler: processing payment.received for customer "${payload.customerName}" ` +
    `(id: ${payload.paymentId}, amount: ${payload.amount}, method: ${payload.paymentMethod})`
  );

  // Resolve Account IDs
  const bankAccount = await resolveAccount(
    client,
    STANDARD_ACCOUNTS.BANK.code,
    metadata.companyId
  );
  const arAccount = await resolveAccount(
    client,
    STANDARD_ACCOUNTS.ACCOUNTS_RECEIVABLE.code,
    metadata.companyId
  );

  // Build Journal Entry Lines
  const lines: CreateJournalEntryData['lines'] = [
    {
      accountId: bankAccount.id,
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

  // Link Journal Entry to Payment
  await client.query(
    `UPDATE customer_payments SET journal_entry_id = $1 WHERE id = $2`,
    [journalEntry.id, payload.paymentId]
  );

  logger.info(
    `PaymentEventHandler: journal entry ${journalEntry.entryNumber} created for customer payment ` +
    `| Dr. Bank: ${payload.amount} | Cr. AR: ${payload.amount} | Customer: ${payload.customerName}`
  );
}

/**
 * Handle the payment.made event
 *
 * Creates a balanced journal entry debiting AP and crediting Bank.
 */
export async function handlePaymentMade(
  event: BaseEvent<PaymentMadePayload>,
  client: PoolClient
): Promise<void> {
  const { payload, metadata } = event;

  logger.info(
    `PaymentEventHandler: processing payment.made for supplier "${payload.supplierName}" ` +
    `(id: ${payload.paymentId}, amount: ${payload.amount}, method: ${payload.paymentMethod})`
  );

  // Resolve Account IDs
  const apAccount = await resolveAccount(
    client,
    STANDARD_ACCOUNTS.ACCOUNTS_PAYABLE.code,
    metadata.companyId
  );
  const bankAccount = await resolveAccount(
    client,
    STANDARD_ACCOUNTS.BANK.code,
    metadata.companyId
  );

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
      accountId: bankAccount.id,
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

  // Link Journal Entry to Payment
  await client.query(
    `UPDATE supplier_payments SET journal_entry_id = $1 WHERE id = $2`,
    [journalEntry.id, payload.paymentId]
  );

  logger.info(
    `PaymentEventHandler: journal entry ${journalEntry.entryNumber} created for supplier payment ` +
    `| Dr. AP: ${payload.amount} | Cr. Bank: ${payload.amount} | Supplier: ${payload.supplierName}`
  );
}
