/**
 * Purchase Event Handler: Purchase Order Approved
 *
 * Accounting Logic for purchase.order.approved (GR / IR cycle):
 *   When a purchase order is approved the supplier invoice is recognized.
 *   The goods are booked into GRNI (Goods Received Not Invoiced) and only
 *   move into Inventory when the inventory.goods.received event arrives,
 *   which clears the GRNI accrual. This avoids double-counting inventory:
 *
 *   1. DEBIT GRNI (Goods Received Not Invoiced)  - goods value (net of VAT)
 *      - Account: 1303 - GRNI
 *      - Amount: finalAmount - taxAmount
 *
 *   2. DEBIT VAT Input (We can reclaim input VAT)
 *      - Account: 1400 - VAT Input
 *      - Amount: taxAmount
 *
 *   3. CREDIT Accounts Payable (We owe the supplier)
 *      - Account: 2111 - Accounts Payable
 *      - Amount: finalAmount (total + tax)
 *
 *   Journal Entry:
 *     Dr. GRNI               (1303)    netAmount
 *     Dr. VAT Input          (1400)    taxAmount
 *     Cr. Accounts Payable   (2111)    finalAmount
 *
 *   Combined with inventory.goods.received (Dr Inventory / Cr GRNI) the
 *   net effect over the full cycle is:
 *     Dr. Inventory          (1301)    netAmount
 *     Dr. VAT Input          (1400)    taxAmount
 *     Cr. Accounts Payable   (2111)    finalAmount
 */

import { PoolClient } from 'pg';
import { BaseEvent, PurchaseOrderApprovedPayload } from '../events/types';
import { postAndFinalizeEntry, voidJournalEntry } from '../ledger/JournalEntryService';
import { CreateJournalEntryData, STANDARD_ACCOUNTS } from '../ledger/types';
import { logger } from '../../services/logger';
import { resolveAccounts } from '../utils/accountResolver';

/**
 * Handle the purchase.order.approved event
 */
export async function handlePurchaseOrderApproved(
  event: BaseEvent<PurchaseOrderApprovedPayload>,
  client: PoolClient
): Promise<{ entryId: number; entryNumber: string }> {
  const { payload, metadata } = event;

  logger.info(
    `PurchaseEventHandler: processing order.approved for PO ${payload.purchaseOrderNumber} ` +
    `(id: ${payload.purchaseOrderId}, amount: ${payload.finalAmount})`
  );

  // Resolve Account IDs (single query for performance)
  const accountCodes = [
    STANDARD_ACCOUNTS.GRNI_ACCRUAL.code,
    STANDARD_ACCOUNTS.VAT_INPUT.code,
    STANDARD_ACCOUNTS.ACCOUNTS_PAYABLE.code,
  ];
  const accounts = await resolveAccounts(client, accountCodes, metadata.companyId);

  const grniAccount = accounts.get(STANDARD_ACCOUNTS.GRNI_ACCRUAL.code)!;
  const vatInputAccount = accounts.get(STANDARD_ACCOUNTS.VAT_INPUT.code)!;
  const apAccount = accounts.get(STANDARD_ACCOUNTS.ACCOUNTS_PAYABLE.code)!;

  // Build Journal Entry Lines
  const lines: CreateJournalEntryData['lines'] = [];

  // LINE 1: DEBIT GRNI (Goods Received Not Invoiced)
  // The supplier invoice is recognized at net-of-VAT cost. The inventory value
  // is only recognized when the goods physically arrive via the
  // inventory.goods.received event (Dr Inventory / Cr GRNI), which clears this
  // accrual. This guarantees the entry always balances and prevents the
  // double-counting of inventory (previously both PO approval and goods
  // receipt debited Inventory).
  const netInventoryAmount = payload.finalAmount - payload.taxAmount;
  if (netInventoryAmount > 0) {
    lines.push({
      accountId: grniAccount.id,
      description: `PO ${payload.purchaseOrderNumber} - ${payload.supplierName}`,
      debit: netInventoryAmount,
      credit: 0,
      partnerId: payload.supplierId,
    });
  }

  // LINE 2: DEBIT VAT Input (if applicable)
  if (payload.taxAmount > 0) {
    lines.push({
      accountId: vatInputAccount.id,
      description: `VAT 15% on PO ${payload.purchaseOrderNumber}`,
      debit: payload.taxAmount,
      credit: 0,
    });
  }

  // LINE 3: CREDIT Accounts Payable
  lines.push({
    accountId: apAccount.id,
    description: `Amount owed to ${payload.supplierName} for PO ${payload.purchaseOrderNumber}`,
    debit: 0,
    credit: payload.finalAmount,
    partnerId: payload.supplierId,
  });

  // Post the Journal Entry
  const journalData: CreateJournalEntryData = {
    entryDate: new Date(),
    description: `Purchase Order ${payload.purchaseOrderNumber} - ${payload.supplierName}`,
    descriptionEn: `Purchase Order ${payload.purchaseOrderNumber} - ${payload.supplierName}`,
    referenceType: 'PurchaseOrder',
    referenceId: payload.purchaseOrderId,
    createdBy: metadata.userId,
    companyId: metadata.companyId,
    lines,
  };

  const journalEntry = await postAndFinalizeEntry(journalData, client, metadata.userId);

  logger.info(
    `PurchaseEventHandler: journal entry ${journalEntry.entryNumber} created for PO ${payload.purchaseOrderNumber} ` +
    `| Dr. GRNI: ${netInventoryAmount} | Dr. VAT Input: ${payload.taxAmount} | Cr. AP: ${payload.finalAmount}`
  );

  // Return the created entry so the backend links purchases.journal_entry_id
  // within its own transaction (the gateway no longer writes to `purchases`
  // directly to avoid a cross-transaction deadlock).
  return { entryId: journalEntry.id, entryNumber: journalEntry.entryNumber };
}

/**
 * Handle the purchase.order.voided event
 */
export async function handlePurchaseOrderVoided(
  event: BaseEvent<{ purchaseOrderId: number; purchaseOrderNumber: string; originalEntryId: number; reason: string }>,
  client: PoolClient
): Promise<{ voided: boolean; entryId: number }> {
  const { payload, metadata } = event;

  logger.info(
    `PurchaseEventHandler: processing order.voided for PO ${payload.purchaseOrderNumber} ` +
    `(original entry: ${payload.originalEntryId})`
  );

  // Step 1: Void the original journal entry (creates reversing entry)
  // A purchase that was approved always carries a linked journal entry. If it
  // is missing, silently skipping the reversal would leave the ledger wrong
  // while the backend still marks the order voided - so we fail loudly instead.
  if (!payload.originalEntryId) {
    throw new Error(
      `PurchaseEventHandler: cannot void PO ${payload.purchaseOrderNumber} - no original journal entry id provided`
    );
  }

  await voidJournalEntry(
    payload.originalEntryId,
    `Voided purchase order ${payload.purchaseOrderNumber}: ${payload.reason}`,
    client,
    metadata.userId
  );

  logger.info(
    `PurchaseEventHandler: PO ${payload.purchaseOrderNumber} voided successfully`
  );

  // The backend sets workflow_state = 'voided' and reverses stock in its own
  // transaction; we return here without writing to `purchases` directly to
  // avoid a cross-transaction deadlock.
  return { voided: true, entryId: payload.originalEntryId };
}
