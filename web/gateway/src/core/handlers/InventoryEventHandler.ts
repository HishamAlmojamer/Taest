/**
 * Inventory Event Handler: Goods Received
 *
 * Accounting Logic for inventory.goods.received:
 *   When goods are received into inventory (e.g., from a purchase order),
 *   the system must:
 *
 *   1. DEBIT Inventory Asset (We now have more inventory)
 *      - Account: 1210 - Inventory (Asset increases with debit)
 *      - Amount: totalCost (quantity × unit_cost)
 *
 *   2. CREDIT Goods Received Not Invoiced (GRNI Accrual)
 *      - Account: 1230 - GRNI Accrual (Liability/Contra-Asset increases with credit)
 *      - Amount: totalCost
 *
 *   Journal Entry:
 *     Dr. Inventory Asset         (1210)    totalCost
 *     Cr. GRNI Accrual            (1230)    totalCost
 *
 *   Double-Entry Verification:
 *     Dr. 1210 Inventory  = totalCost
 *     Cr. 1230 GRNI       = totalCost
 *     Sum(Debit) = Sum(Credit) ✓
 *
 *   Note: GRNI is used when goods are received but the supplier invoice
 *   hasn't been processed yet. When the invoice arrives, GRNI is debited
 *   and Accounts Payable is credited.
 *
 *   The unit_cost is recorded for inventory valuation (FIFO/Weighted Average).
 */

import { PoolClient } from 'pg';
import { BaseEvent, InventoryGoodsReceivedPayload } from '../events/types';
import { postAndFinalizeEntry } from '../ledger/JournalEntryService';
import { CreateJournalEntryData, STANDARD_ACCOUNTS } from '../ledger/types';
import { logger } from '../../services/logger';
import { resolveAccount } from '../utils/accountResolver';

/**
 * Handle the inventory.goods.received event
 *
 * Creates a balanced journal entry debiting Inventory Asset
 * and crediting GRNI Accrual.
 *
 * @param event - The inventory goods received event
 * @param client - Active PoolClient within the caller's transaction
 */
export async function handleInventoryGoodsReceived(
  event: BaseEvent<InventoryGoodsReceivedPayload>,
  client: PoolClient
): Promise<void> {
  const { payload, metadata } = event;

  logger.info(
    `InventoryEventHandler: processing goods.received for product "${payload.productName}" ` +
    `(qty: ${payload.quantity}, unit cost: ${payload.unitCost}, total: ${payload.totalCost})`
  );

  // ==========================================
  // STEP 1: Resolve Account IDs
  // ==========================================
  const inventoryAccount = await resolveAccount(
    client,
    STANDARD_ACCOUNTS.INVENTORY_ASSET.code,
    metadata.companyId
  );
  const grniAccount = await resolveAccount(
    client,
    STANDARD_ACCOUNTS.GRNI_ACCRUAL.code,
    metadata.companyId
  );

  // ==========================================
  // STEP 2: Build Journal Entry Lines
  // ==========================================
  const lines: CreateJournalEntryData['lines'] = [];

  // LINE 1: DEBIT Inventory Asset
  // Inventory (an asset) increases when goods are received
  lines.push({
    accountId: inventoryAccount.id,
    description: `Received: ${payload.productName} (${payload.quantity} units @ ${payload.unitCost})`,
    debit: payload.totalCost,
    credit: 0,
  });

  // LINE 2: CREDIT GRNI Accrual
  // GRNI represents goods received but not yet invoiced by the supplier
  // This is a temporary account that will be cleared when the purchase invoice is processed
  lines.push({
    accountId: grniAccount.id,
    description: `GRNI: ${payload.productName} - ${payload.supplierName || 'Unknown Supplier'}`,
    debit: 0,
    credit: payload.totalCost,
  });

  // ==========================================
  // STEP 3: Post the Journal Entry
  // ==========================================
  const referenceNumber = payload.purchaseOrderNumber || `GR-${payload.transactionId}`;

  const journalData: CreateJournalEntryData = {
    entryDate: new Date(),
    description: `Goods Received: ${payload.productName} - ${payload.warehouseName}`,
    descriptionEn: `Goods Received: ${payload.productName} - ${payload.warehouseName}`,
    referenceType: 'InventoryTransaction',
    referenceId: payload.transactionId,
    createdBy: metadata.userId,
    companyId: metadata.companyId,
    lines,
  };

  const journalEntry = await postAndFinalizeEntry(journalData, client, metadata.userId);

  // ==========================================
  // STEP 4: Link Journal Entry to Inventory Transaction
  // ==========================================
  await client.query(
    `UPDATE stock_movements SET journal_entry_id = $1 WHERE id = $2`,
    [journalEntry.id, payload.transactionId]
  );

  logger.info(
    `InventoryEventHandler: journal entry ${journalEntry.entryNumber} created for goods received ` +
    `| Dr. Inventory: ${payload.totalCost} | Cr. GRNI: ${payload.totalCost} ` +
    `| Product: ${payload.productName} | Warehouse: ${payload.warehouseName}`
  );
}

/**
 * Handle the inventory.goods.issued event
 *
 * Accounting Logic for inventory.goods.issued:
 *   When goods are issued from inventory (e.g., for a sales order):
 *
 *   1. DEBIT Cost of Goods Sold (Expense increases with debit)
 *      - Account: 5100 - COGS
 *      - Amount: totalCost (quantity × unit_cost)
 *
 *   2. CREDIT Inventory Asset (Asset decreases with credit)
 *      - Account: 1210 - Inventory
 *      - Amount: totalCost
 *
 *   Journal Entry:
 *     Dr. COGS            (5100)    totalCost
 *     Cr. Inventory Asset  (1210)    totalCost
 *
 * @param event - The inventory goods issued event
 * @param client - Active PoolClient within the caller's transaction
 */
export async function handleInventoryGoodsIssued(
  event: BaseEvent<{ transactionId: number; productId: number; productName: string; warehouseId: number; warehouseName: string; quantity: number; unitCost: number; totalCost: number; currencyCode: string }>,
  client: PoolClient
): Promise<void> {
  const { payload, metadata } = event;

  logger.info(
    `InventoryEventHandler: processing goods.issued for product "${payload.productName}" ` +
    `(qty: ${payload.quantity}, unit cost: ${payload.unitCost}, total: ${payload.totalCost})`
  );

  const cogsAccount = await resolveAccount(
    client,
    STANDARD_ACCOUNTS.COST_OF_GOODS_SOLD.code,
    metadata.companyId
  );
  const inventoryAccount = await resolveAccount(
    client,
    STANDARD_ACCOUNTS.INVENTORY_ASSET.code,
    metadata.companyId
  );

  const lines: CreateJournalEntryData['lines'] = [
    {
      accountId: cogsAccount.id,
      description: `COGS: ${payload.productName} (${payload.quantity} units)`,
      debit: payload.totalCost,
      credit: 0,
    },
    {
      accountId: inventoryAccount.id,
      description: `Inventory issued: ${payload.productName} from ${payload.warehouseName}`,
      debit: 0,
      credit: payload.totalCost,
    },
  ];

  const journalData: CreateJournalEntryData = {
    entryDate: new Date(),
    description: `Goods Issued: ${payload.productName} from ${payload.warehouseName}`,
    descriptionEn: `Goods Issued: ${payload.productName} from ${payload.warehouseName}`,
    referenceType: 'InventoryTransaction',
    referenceId: payload.transactionId,
    createdBy: metadata.userId,
    companyId: metadata.companyId,
    lines,
  };

  const journalEntry = await postAndFinalizeEntry(journalData, client, metadata.userId);

  await client.query(
    `UPDATE stock_movements SET journal_entry_id = $1 WHERE id = $2`,
    [journalEntry.id, payload.transactionId]
  );

  logger.info(
    `InventoryEventHandler: journal entry ${journalEntry.entryNumber} created for goods issued ` +
    `| Dr. COGS: ${payload.totalCost} | Cr. Inventory: ${payload.totalCost}`
  );
}
