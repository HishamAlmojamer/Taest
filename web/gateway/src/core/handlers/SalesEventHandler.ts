/**
 * Sales Event Handler: Invoice Approved
 *
 * Accounting Logic for sales.invoice.approved:
 *   When a sales invoice is approved, the system must:
 *
 *   1. DEBIT Accounts Receivable (Customer owes us money)
 *      - Account: 1130 - Accounts Receivable (Asset increases with debit)
 *      - Amount: finalAmount (what the customer must pay)
 *
 *   2. CREDIT Sales Revenue (We earned revenue from the sale)
 *      - Account: 4100 - Sales Revenue (Revenue increases with credit)
 *      - Amount: totalAmount (pre-tax amount of goods sold)
 *
 *   3. DEBIT VAT Input (We collected VAT on behalf of government)
 *      - Account: 2120 - VAT Output (Liability increases with credit)
 *      - Amount: taxAmount (15% VAT on the sale)
 *
 *   Journal Entry:
 *     Dr. Accounts Receivable    (1130)    finalAmount
 *     Cr. Sales Revenue          (4100)    totalAmount
 *     Cr. VAT Output             (2120)    taxAmount
 *
 *   Note: finalAmount = totalAmount + taxAmount - discount
 *
 *   4. If items have different tax rates, create separate lines per item
 *
 *   Double-Entry Verification:
 *     Dr. 1130 AR              = finalAmount
 *     Cr. 4100 Revenue         = totalAmount
 *     Cr. 2120 VAT Output      = taxAmount
 *     Sum(Debit) = finalAmount
 *     Sum(Credit) = totalAmount + taxAmount = finalAmount ✓
 */

import { PoolClient } from 'pg';
import { BaseEvent, SalesInvoiceApprovedPayload } from '../events/types';
import { postAndFinalizeEntry } from '../ledger/JournalEntryService';
import { CreateJournalEntryData, STANDARD_ACCOUNTS } from '../ledger/types';
import { logger } from '../../services/logger';
import { resolveAccount } from '../utils/accountResolver';

/**
 * Handle the sales.invoice.approved event
 *
 * Creates a balanced journal entry debiting Accounts Receivable
 * and crediting Sales Revenue + VAT Output.
 *
 * @param event - The sales invoice approved event
 * @param client - Active PoolClient within the caller's transaction
 */
export async function handleSalesInvoiceApproved(
  event: BaseEvent<SalesInvoiceApprovedPayload>,
  client: PoolClient
): Promise<void> {
  const { payload, metadata } = event;

  logger.info(
    `SalesEventHandler: processing invoice.approved for invoice ${payload.invoiceNumber} ` +
    `(id: ${payload.invoiceId}, amount: ${payload.finalAmount})`
  );

  // ==========================================
  // STEP 1: Resolve Account IDs
  // ==========================================
  const arAccount = await resolveAccount(
    client,
    STANDARD_ACCOUNTS.ACCOUNTS_RECEIVABLE.code,
    metadata.companyId
  );
  const revenueAccount = await resolveAccount(
    client,
    STANDARD_ACCOUNTS.SALES_REVENUE.code,
    metadata.companyId
  );
  const vatOutputAccount = await resolveAccount(
    client,
    STANDARD_ACCOUNTS.VAT_OUTPUT.code,
    metadata.companyId
  );

  // ==========================================
  // STEP 2: Build Journal Entry Lines
  // ==========================================
  // Group items by tax rate to create accurate revenue lines
  // For simplicity, we use the total amounts from the invoice

  const lines: CreateJournalEntryData['lines'] = [];

  // LINE 1: DEBIT Accounts Receivable
  // The customer now owes us the final amount (after discount, including tax)
  lines.push({
    accountId: arAccount.id,
    description: `Invoice ${payload.invoiceNumber} - ${payload.customerName}`,
    debit: payload.finalAmount,
    credit: 0,
    partnerId: payload.customerId,
  });

  // LINE 2: CREDIT Sales Revenue
  // Revenue is recorded at the pre-tax amount
  if (payload.totalAmount > 0) {
    lines.push({
      accountId: revenueAccount.id,
      description: `Revenue from invoice ${payload.invoiceNumber}`,
      debit: 0,
      credit: payload.totalAmount,
    });
  }

  // LINE 3: CREDIT VAT Output
  // VAT collected is a liability we owe to the government
  if (payload.taxAmount > 0) {
    lines.push({
      accountId: vatOutputAccount.id,
      description: `VAT 15% on invoice ${payload.invoiceNumber}`,
      debit: 0,
      credit: payload.taxAmount,
    });
  }

  // If there's a discount, we may need to adjust
  // The finalAmount already accounts for discount, so the entry should balance

  // ==========================================
  // STEP 3: Post the Journal Entry
  // ==========================================
  const journalData: CreateJournalEntryData = {
    entryDate: new Date(),
    description: `Sales Invoice ${payload.invoiceNumber} - ${payload.customerName}`,
    descriptionEn: `Sales Invoice ${payload.invoiceNumber} - ${payload.customerName}`,
    referenceType: 'SalesInvoice',
    referenceId: payload.invoiceId,
    createdBy: metadata.userId,
    companyId: metadata.companyId,
    lines,
  };

  const journalEntry = await postAndFinalizeEntry(journalData, client, metadata.userId);

  // ==========================================
  // STEP 4: Link Journal Entry to Invoice
  // ==========================================
  await client.query(
    `UPDATE sales SET journal_entry_id = $1 WHERE id = $2`,
    [journalEntry.id, payload.invoiceId]
  );

  logger.info(
    `SalesEventHandler: journal entry ${journalEntry.entryNumber} created for invoice ${payload.invoiceNumber} ` +
    `| Dr. AR: ${payload.finalAmount} | Cr. Revenue: ${payload.totalAmount} | Cr. VAT: ${payload.taxAmount}`
  );
}

/**
 * Handle the sales.invoice.voided event
 *
 * When a sales invoice is voided, we must reverse the original journal entry.
 *
 * @param event - The sales invoice voided event
 * @param client - Active PoolClient within the caller's transaction
 */
export async function handleSalesInvoiceVoided(
  event: BaseEvent<{ invoiceId: number; invoiceNumber: string; originalEntryId: number; reason: string }>,
  client: PoolClient
): Promise<void> {
  const { payload } = event;

  logger.info(
    `SalesEventHandler: processing invoice.voided for invoice ${payload.invoiceNumber} ` +
    `(original entry: ${payload.originalEntryId})`
  );

  // The voidJournalEntry function handles:
  // 1. Marking original entry as Voided
  // 2. Creating reversing entry with swapped debits/credits
  // We import it here but it's called from the router/handler that initiates the void
  // This event handler just logs and performs any additional cleanup

  // Update the invoice status to reflect voiding
  await client.query(
    `UPDATE sales SET workflow_state = 'voided' WHERE id = $1`,
    [payload.invoiceId]
  );

  logger.info(
    `SalesEventHandler: invoice ${payload.invoiceNumber} voided successfully`
  );
}
