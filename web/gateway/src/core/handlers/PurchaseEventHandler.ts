/**
 * Purchase Event Handler: Purchase Order Approved
 *
 * Accounting Logic for purchase.order.approved:
 *   When a purchase order is approved/processed:
 *
 *   1. DEBIT Inventory Asset (We receive inventory)
 *      - Account: 1210 - Inventory
 *      - Amount: totalAmount (pre-tax)
 *
 *   2. DEBIT VAT Input (We can reclaim input VAT)
 *      - Account: 1240 - VAT Input
 *      - Amount: taxAmount
 *
 *   3. CREDIT Accounts Payable (We owe the supplier)
 *      - Account: 2110 - Accounts Payable
 *      - Amount: finalAmount (total + tax)
 *
 *   Journal Entry:
 *     Dr. Inventory Asset     (1210)    totalAmount
 *     Dr. VAT Input           (1240)    taxAmount
 *     Cr. Accounts Payable    (2110)    finalAmount
 */

import { PoolClient } from 'pg';
import { BaseEvent, PurchaseOrderApprovedPayload } from '../events/types';
import { postAndFinalizeEntry } from '../ledger/JournalEntryService';
import { CreateJournalEntryData, STANDARD_ACCOUNTS } from '../ledger/types';
import { logger } from '../../services/logger';
import { resolveAccount } from '../utils/accountResolver';

/**
 * Handle the purchase.order.approved event
 */
export async function handlePurchaseOrderApproved(
  event: BaseEvent<PurchaseOrderApprovedPayload>,
  client: PoolClient
): Promise<void> {
  const { payload, metadata } = event;

  logger.info(
    `PurchaseEventHandler: processing order.approved for PO ${payload.purchaseOrderNumber} ` +
    `(id: ${payload.purchaseOrderId}, amount: ${payload.finalAmount})`
  );

  // Resolve Account IDs
  const inventoryAccount = await resolveAccount(
    client,
    STANDARD_ACCOUNTS.INVENTORY_ASSET.code,
    metadata.companyId
  );
  const vatInputAccount = await resolveAccount(
    client,
    STANDARD_ACCOUNTS.VAT_INPUT.code,
    metadata.companyId
  );
  const apAccount = await resolveAccount(
    client,
    STANDARD_ACCOUNTS.ACCOUNTS_PAYABLE.code,
    metadata.companyId
  );

  // Build Journal Entry Lines
  const lines: CreateJournalEntryData['lines'] = [];

  // LINE 1: DEBIT Inventory Asset
  if (payload.totalAmount > 0) {
    lines.push({
      accountId: inventoryAccount.id,
      description: `PO ${payload.purchaseOrderNumber} - ${payload.supplierName}`,
      debit: payload.totalAmount,
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

  // Link Journal Entry to Purchase Order
  await client.query(
    `UPDATE purchases SET journal_entry_id = $1 WHERE id = $2`,
    [journalEntry.id, payload.purchaseOrderId]
  );

  logger.info(
    `PurchaseEventHandler: journal entry ${journalEntry.entryNumber} created for PO ${payload.purchaseOrderNumber} ` +
    `| Dr. Inventory: ${payload.totalAmount} | Dr. VAT Input: ${payload.taxAmount} | Cr. AP: ${payload.finalAmount}`
  );
}

/**
 * Handle the purchase.order.voided event
 */
export async function handlePurchaseOrderVoided(
  event: BaseEvent<{ purchaseOrderId: number; purchaseOrderNumber: string; originalEntryId: number; reason: string }>,
  client: PoolClient
): Promise<void> {
  const { payload } = event;

  logger.info(
    `PurchaseEventHandler: processing order.voided for PO ${payload.purchaseOrderNumber} ` +
    `(original entry: ${payload.originalEntryId})`
  );

  // Update the purchase order status
  await client.query(
    `UPDATE purchases SET workflow_state = 'voided' WHERE id = $1`,
    [payload.purchaseOrderId]
  );

  logger.info(
    `PurchaseEventHandler: PO ${payload.purchaseOrderNumber} voided successfully`
  );
}
