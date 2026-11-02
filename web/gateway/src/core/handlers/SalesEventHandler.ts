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
import { BaseEvent, SalesInvoiceApprovedPayload, SalesInvoiceVoidedPayload } from '../events/types';
import { postAndFinalizeEntry, voidJournalEntry } from '../ledger/JournalEntryService';
import { CreateJournalEntryData, STANDARD_ACCOUNTS } from '../ledger/types';
import { logger } from '../../services/logger';
import { resolveAccounts } from '../utils/accountResolver';

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
): Promise<{ entryId: number; entryNumber: string }> {
  const { payload, metadata } = event;

  logger.info(
    `SalesEventHandler: processing invoice.approved for invoice ${payload.invoiceNumber} ` +
    `(id: ${payload.invoiceId}, amount: ${payload.finalAmount})`
  );

  // ==========================================
  // STEP 1: Resolve Account IDs (single query for performance)
  // ==========================================
  const accountCodes = [
    STANDARD_ACCOUNTS.ACCOUNTS_RECEIVABLE.code,
    STANDARD_ACCOUNTS.SALES_REVENUE.code,
    STANDARD_ACCOUNTS.VAT_OUTPUT.code,
  ];
  const accounts = await resolveAccounts(client, accountCodes, metadata.companyId);

  const arAccount = accounts.get(STANDARD_ACCOUNTS.ACCOUNTS_RECEIVABLE.code)!;
  const revenueAccount = accounts.get(STANDARD_ACCOUNTS.SALES_REVENUE.code)!;
  const vatOutputAccount = accounts.get(STANDARD_ACCOUNTS.VAT_OUTPUT.code)!;

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
  // Revenue is recorded net of VAT: finalAmount - taxAmount. This is the
  // amount the customer actually pays for the goods (after any discount),
  // and it guarantees the journal entry always balances, regardless of
  // whether `totalAmount` carries a gross or net-of-discount value.
  const revenueNet = payload.finalAmount - payload.taxAmount;
  if (revenueNet > 0) {
    lines.push({
      accountId: revenueAccount.id,
      description: `Revenue from invoice ${payload.invoiceNumber}`,
      debit: 0,
      credit: revenueNet,
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

  logger.info(
    `SalesEventHandler: journal entry ${journalEntry.entryNumber} created for invoice ${payload.invoiceNumber} ` +
    `| Dr. AR: ${payload.finalAmount} | Cr. Revenue: ${payload.totalAmount} | Cr. VAT: ${payload.taxAmount}`
  );

  // Return the created entry so the caller (backend) can link it to the
  // operational record within its OWN transaction. We deliberately avoid
  // updating `sales` here: the operational transaction is still open on the
  // backend connection, and an UPDATE from this separate connection would
  // block on the uncommitted row (cross-transaction deadlock).
  return { entryId: journalEntry.id, entryNumber: journalEntry.entryNumber };
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
  event: BaseEvent<SalesInvoiceVoidedPayload>,
  client: PoolClient
): Promise<void> {
  const { payload, metadata } = event;

  logger.info(
    `SalesEventHandler: processing invoice.voided for invoice ${payload.invoiceNumber} ` +
    `(original entry: ${payload.originalEntryId}, ${(payload.stockMovementIds || []).length} COGS entries)`
  );

  // The backend never emits a void without a linked revenue entry: a sale only
  // reaches the 'approved' state (required to void) by going through
  // approve_sale, which always records journal_entry_id. Failing loudly instead
  // of silently no-oping keeps the ledger correct.
  if (!payload.originalEntryId) {
    throw new Error(
      `SalesEventHandler: cannot void invoice ${payload.invoiceNumber} - no original journal entry id provided`
    );
  }

  // Step 1: Void the original journal entry (creates reversing entry)
  await voidJournalEntry(
    payload.originalEntryId,
    `Voided sales invoice ${payload.invoiceNumber}: ${payload.reason}`,
    client,
    metadata.userId
  );

  // Step 2: Void every COGS journal entry that was posted when this sale's
  // goods were issued (Dr COGS / Cr Inventory). Each goods.issued event is
  // stored with referenceType='InventoryTransaction' and referenceId = the
  // stock movement id, so we reverse them by their stock movement ids.
  if (payload.stockMovementIds && payload.stockMovementIds.length > 0) {
    const cogsResult = await client.query(
      `SELECT id FROM journal_entries
       WHERE reference_type = 'InventoryTransaction'
         AND reference_id = ANY($1::int[])
         AND status = 'Posted'
       ORDER BY id ASC`,
      [payload.stockMovementIds]
    );

    for (const row of cogsResult.rows) {
      await voidJournalEntry(
        Number(row.id),
        `Voided COGS for sales invoice ${payload.invoiceNumber}: ${payload.reason}`,
        client,
        metadata.userId
      );
    }
    logger.info(
      `SalesEventHandler: voided ${cogsResult.rows.length} COGS entries for invoice ${payload.invoiceNumber}`
    );
  }

  logger.info(
    `SalesEventHandler: invoice ${payload.invoiceNumber} voided successfully`
  );
}
