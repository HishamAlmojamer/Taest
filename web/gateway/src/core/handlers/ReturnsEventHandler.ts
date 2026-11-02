/**
 * Returns Event Handler: Sales & Purchase Returns
 *
 * Accounting Logic for sales.return.approved:
 *   When a sales return is approved, the system must reverse the original sale:
 *
 *   1. DEBIT Sales Returns (contra-revenue, decreases revenue)
 *      - Account: 4200 - Sales Returns
 *      - Amount: totalAmount (pre-tax)
 *
 *   2. DEBIT VAT Output (reduces VAT liability)
 *      - Account: 2120 - VAT Output
 *      - Amount: taxAmount
 *
 *   3. CREDIT Accounts Receivable (customer owes us less)
 *      - Account: 1130 - Accounts Receivable
 *      - Amount: finalAmount (total + tax)
 *
 *   Journal Entry:
 *     Dr. Sales Returns        (4200)    totalAmount
 *     Dr. VAT Output           (2120)    taxAmount
 *     Cr. Accounts Receivable  (1130)    finalAmount
 *
 *   Double-Entry Verification:
 *     Dr. Total = totalAmount + taxAmount = finalAmount
 *     Cr. Total = finalAmount
 *     Sum(Debit) = Sum(Credit) ✓
 *
 * Accounting Logic for purchase.return.approved:
 *   When a purchase return is approved, the system must reverse the original purchase:
 *
 *   1. DEBIT Accounts Payable (we owe the supplier less)
 *      - Account: 2111 - Accounts Payable
 *      - Amount: finalAmount (total + tax)
 *
 *   2. CREDIT Inventory (returned goods leave the warehouse - NOT COGS)
 *      - Account: 1301 - Inventory
 *      - Amount: finalAmount - taxAmount (net of VAT)
 *
 *   3. CREDIT VAT Input (reduces input VAT reclaimable)
 *      - Account: 1400 - VAT Input
 *      - Amount: taxAmount
 *
 *   Journal Entry:
 *     Dr. Accounts Payable  (2111)    finalAmount
 *     Cr. Inventory         (1301)    netAmount
 *     Cr. VAT Input         (1400)    taxAmount
 *
 *   Double-Entry Verification:
 *     Dr. Total = finalAmount
 *     Cr. Total = netAmount + taxAmount = finalAmount
 *     Sum(Debit) = Sum(Credit) ✓
 *
 *   Note: crediting Inventory (not COGS) keeps the purchase-return cycle
 *   consistent with the GR/IR flow - stock physically returns to the
 *   supplier, so the Inventory Asset decreases; COGS is only affected when
 *   goods were actually sold.
 */

import { PoolClient } from 'pg';
import { BaseEvent, SalesReturnApprovedPayload, PurchaseReturnApprovedPayload } from '../events/types';
import { postAndFinalizeEntry, voidJournalEntry } from '../ledger/JournalEntryService';
import { CreateJournalEntryData, STANDARD_ACCOUNTS } from '../ledger/types';
import { logger } from '../../services/logger';
import { resolveAccounts } from '../utils/accountResolver';

/**
 * Handle the sales.return.approved event
 *
 * Creates a balanced journal entry debiting Sales Returns and VAT Output,
 * and crediting Accounts Receivable.
 *
 * @param event - The sales return approved event
 * @param client - Active PoolClient within the caller's transaction
 */
export async function handleSalesReturnApproved(
  event: BaseEvent<SalesReturnApprovedPayload>,
  client: PoolClient
): Promise<{ entryId: number; entryNumber: string }> {
  const { payload, metadata } = event;

  logger.info(
    `ReturnsEventHandler: processing sales.return.approved for return ${payload.returnNumber} ` +
    `(id: ${payload.returnId}, amount: ${payload.finalAmount})`
  );

  // ==========================================
  // STEP 1: Resolve Account IDs (single query for performance)
  // ==========================================
  const accountCodes = [
    STANDARD_ACCOUNTS.SALES_RETURNS.code,
    STANDARD_ACCOUNTS.VAT_OUTPUT.code,
    STANDARD_ACCOUNTS.ACCOUNTS_RECEIVABLE.code,
  ];
  const accounts = await resolveAccounts(client, accountCodes, metadata.companyId);

  const salesReturnsAccount = accounts.get(STANDARD_ACCOUNTS.SALES_RETURNS.code)!;
  const vatOutputAccount = accounts.get(STANDARD_ACCOUNTS.VAT_OUTPUT.code)!;
  const arAccount = accounts.get(STANDARD_ACCOUNTS.ACCOUNTS_RECEIVABLE.code)!;

  // ==========================================
  // STEP 2: Build Journal Entry Lines
  // ==========================================
  const lines: CreateJournalEntryData['lines'] = [];

  // LINE 1: DEBIT Sales Returns (contra-revenue)
  // Recognized net of VAT (finalAmount - taxAmount) so the entry always
  // balances, including when the return carries a discount.
  const salesReturnsNet = payload.finalAmount - payload.taxAmount;
  if (salesReturnsNet > 0) {
    lines.push({
      accountId: salesReturnsAccount.id,
      description: `Sales return ${payload.returnNumber} - ${payload.customerName}`,
      debit: salesReturnsNet,
      credit: 0,
      partnerId: payload.customerId,
    });
  }

  // LINE 2: DEBIT VAT Output (reduce VAT liability)
  if (payload.taxAmount > 0) {
    lines.push({
      accountId: vatOutputAccount.id,
      description: `VAT reversal on return ${payload.returnNumber}`,
      debit: payload.taxAmount,
      credit: 0,
    });
  }

  // LINE 3: CREDIT Accounts Receivable (customer owes us less)
  lines.push({
    accountId: arAccount.id,
    description: `Credit customer for return ${payload.returnNumber}`,
    debit: 0,
    credit: payload.finalAmount,
    partnerId: payload.customerId,
  });

  // ==========================================
  // STEP 3: Post the Journal Entry
  // ==========================================
  const journalData: CreateJournalEntryData = {
    entryDate: new Date(),
    description: `Sales Return ${payload.returnNumber} - ${payload.customerName}`,
    descriptionEn: `Sales Return ${payload.returnNumber} - ${payload.customerName}`,
    referenceType: 'SalesReturn',
    referenceId: payload.returnId,
    createdBy: metadata.userId,
    companyId: metadata.companyId,
    lines,
  };

  const journalEntry = await postAndFinalizeEntry(journalData, client, metadata.userId);

  logger.info(
    `ReturnsEventHandler: journal entry ${journalEntry.entryNumber} created for sales return ${payload.returnNumber} ` +
    `| Dr. Sales Returns: ${payload.totalAmount} | Dr. VAT Output: ${payload.taxAmount} | Cr. AR: ${payload.finalAmount}`
  );

  // Return the created entry so the backend links sales_returns.journal_entry_id
  // within its OWN transaction. We deliberately avoid updating `sales_returns`
  // here: the backend transaction has already modified that row (status=approved)
  // and is still open, so an UPDATE from this connection would block on the
  // uncommitted row (cross-transaction deadlock / timeout).
  return { entryId: journalEntry.id, entryNumber: journalEntry.entryNumber };
}

/**
 * Handle the sales.return.voided event
 *
 * When a sales return is voided, reverse the original return journal entry.
 *
 * @param event - The sales return voided event
 * @param client - Active PoolClient within the caller's transaction
 */
export async function handleSalesReturnVoided(
  event: BaseEvent<{ returnId: number; returnNumber: string; customerId: number; originalEntryId?: number; reason: string }>,
  client: PoolClient
): Promise<void> {
  const { payload, metadata } = event;

  logger.info(
    `ReturnsEventHandler: processing sales.return.voided for return ${payload.returnNumber} ` +
    `(original entry: ${payload.originalEntryId})`
  );

  // Step 1: Void the original journal entry (creates reversing entry).
  // The backend only allows voiding non-approved returns, so a real void
  // never carries a journal entry; fail loudly instead of silently skipping.
  if (!payload.originalEntryId) {
    throw new Error(
      `ReturnsEventHandler: cannot void sales return ${payload.returnNumber} - no posted journal entry found.`
    );
  }
  await voidJournalEntry(
    payload.originalEntryId,
    `Voided sales return ${payload.returnNumber}: ${payload.reason}`,
    client,
    metadata.userId
  );

  logger.info(
    `ReturnsEventHandler: sales return ${payload.returnNumber} voided successfully`
  );
}

/**
 * Handle the purchase.return.approved event
 *
 * Creates a balanced journal entry debiting Accounts Payable,
 * and crediting COGS and VAT Input.
 *
 * @param event - The purchase return approved event
 * @param client - Active PoolClient within the caller's transaction
 */
export async function handlePurchaseReturnApproved(
  event: BaseEvent<PurchaseReturnApprovedPayload>,
  client: PoolClient
): Promise<{ entryId: number; entryNumber: string }> {
  const { payload, metadata } = event;

  logger.info(
    `ReturnsEventHandler: processing purchase.return.approved for return ${payload.returnNumber} ` +
    `(id: ${payload.returnId}, amount: ${payload.finalAmount})`
  );

  // ==========================================
  // STEP 1: Resolve Account IDs (single query for performance)
  // ==========================================
  const accountCodes = [
    STANDARD_ACCOUNTS.ACCOUNTS_PAYABLE.code,
    STANDARD_ACCOUNTS.INVENTORY_ASSET.code,
    STANDARD_ACCOUNTS.VAT_INPUT.code,
  ];
  const accounts = await resolveAccounts(client, accountCodes, metadata.companyId);

  const apAccount = accounts.get(STANDARD_ACCOUNTS.ACCOUNTS_PAYABLE.code)!;
  const inventoryAccount = accounts.get(STANDARD_ACCOUNTS.INVENTORY_ASSET.code)!;
  const vatInputAccount = accounts.get(STANDARD_ACCOUNTS.VAT_INPUT.code)!;

  // ==========================================
  // STEP 2: Build Journal Entry Lines
  // ==========================================
  const lines: CreateJournalEntryData['lines'] = [];

  // LINE 1: DEBIT Accounts Payable (we owe the supplier less)
  lines.push({
    accountId: apAccount.id,
    description: `Purchase return ${payload.returnNumber} - ${payload.supplierName}`,
    debit: payload.finalAmount,
    credit: 0,
    partnerId: payload.supplierId,
  });

  // LINE 2: CREDIT Inventory (returned goods leave the warehouse)
  // Recognized net of VAT (finalAmount - taxAmount) so the entry always
  // balances, including when the return carries a discount. CREDITING
  // INVENTORY (not COGS) is the correct treatment: the goods physically
  // return to the supplier, so the Inventory Asset decreases. Crediting
  // COGS previously understated COGS and overstated Inventory.
  const purchaseReturnsNet = payload.finalAmount - payload.taxAmount;
  if (purchaseReturnsNet > 0) {
    lines.push({
      accountId: inventoryAccount.id,
      description: `Returned goods from ${payload.supplierName} (${payload.returnNumber})`,
      debit: 0,
      credit: purchaseReturnsNet,
    });
  }

  // LINE 3: CREDIT VAT Input (reduce input VAT reclaimable)
  if (payload.taxAmount > 0) {
    lines.push({
      accountId: vatInputAccount.id,
      description: `VAT reversal on purchase return ${payload.returnNumber}`,
      debit: 0,
      credit: payload.taxAmount,
    });
  }

  // ==========================================
  // STEP 3: Post the Journal Entry
  // ==========================================
  const journalData: CreateJournalEntryData = {
    entryDate: new Date(),
    description: `Purchase Return ${payload.returnNumber} - ${payload.supplierName}`,
    descriptionEn: `Purchase Return ${payload.returnNumber} - ${payload.supplierName}`,
    referenceType: 'PurchaseReturn',
    referenceId: payload.returnId,
    createdBy: metadata.userId,
    companyId: metadata.companyId,
    lines,
  };

  const journalEntry = await postAndFinalizeEntry(journalData, client, metadata.userId);

  logger.info(
    `ReturnsEventHandler: journal entry ${journalEntry.entryNumber} created for purchase return ${payload.returnNumber} ` +
    `| Dr. AP: ${payload.finalAmount} | Cr. Inventory: ${purchaseReturnsNet} | Cr. VAT Input: ${payload.taxAmount}`
  );

  // Return the created entry so the backend links purchase_returns.journal_entry_id
  // within its OWN transaction (avoids cross-transaction deadlock on the open row).
  return { entryId: journalEntry.id, entryNumber: journalEntry.entryNumber };
}

/**
 * Handle the purchase.return.voided event
 *
 * When a purchase return is voided, reverse the original return journal entry.
 *
 * @param event - The purchase return voided event
 * @param client - Active PoolClient within the caller's transaction
 */
export async function handlePurchaseReturnVoided(
  event: BaseEvent<{ returnId: number; returnNumber: string; supplierId: number; originalEntryId?: number; reason: string }>,
  client: PoolClient
): Promise<void> {
  const { payload, metadata } = event;

  logger.info(
    `ReturnsEventHandler: processing purchase.return.voided for return ${payload.returnNumber} ` +
    `(original entry: ${payload.originalEntryId})`
  );

  // Void the original journal entry (creates reversing entry).
  // The backend only allows voiding non-approved returns, so a real void
  // never carries a journal entry; fail loudly instead of silently skipping.
  if (!payload.originalEntryId) {
    throw new Error(
      `ReturnsEventHandler: cannot void purchase return ${payload.returnNumber} - no posted journal entry found.`
    );
  }
  await voidJournalEntry(
    payload.originalEntryId,
    `Voided purchase return ${payload.returnNumber}: ${payload.reason}`,
    client,
    metadata.userId
  );

  logger.info(
    `ReturnsEventHandler: purchase return ${payload.returnNumber} voided successfully`
  );
}

