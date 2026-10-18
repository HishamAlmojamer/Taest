/**
 * Core Module: Event-Driven Financial Ledger Engine
 *
 * This module provides the complete event-driven infrastructure
 * for the ERP financial system, as specified in ERP_INSTRUCTIONS.md.
 *
 * Architecture Overview:
 *   ┌─────────────────────┐
 *   │  Operational Module  │ (Sales, Inventory, HR)
 *   │  emits event within  │
 *   │  same DB transaction │
 *   └──────────┬──────────┘
 *              │
 *              ▼
 *   ┌─────────────────────┐
 *   │     Event Bus       │ (Transactional Broker)
 *   │  invokes handlers   │
 *   │  synchronously      │
 *   └──────────┬──────────┘
 *              │
 *              ▼
 *   ┌─────────────────────┐
 *   │   Ledger Engine     │ (JournalEntryService)
 *   │  writes balanced    │
 *   │  journal entries    │
 *   └──────────┬──────────┘
 *              │
 *              ▼
 *   ┌─────────────────────┐
 *   │   PostgreSQL DB     │
 *   │  COMMIT or ROLLBACK │
 *   └─────────────────────┘
 *
 * Key Guarantees:
 *   1. Atomicity: All writes in a single transaction
 *   2. Consistency: Σ(Debit) == Σ(Credit) enforced
 *   3. Isolation: PostgreSQL transaction isolation
 *   4. Durability: Committed data survives crashes
 */

import { registerEventHandlers } from './handlers';
import { getEventBus } from './events/EventBus';
import { withTransaction, getPool, closePool, query } from './database/DatabaseConnection';
import {
  postJournalEntry,
  postAndFinalizeEntry,
  voidJournalEntry,
  getTrialBalance,
} from './ledger/JournalEntryService';
import { STANDARD_ACCOUNTS } from './ledger/types';

/**
 * Initialize the core financial engine.
 * Call this once during application startup.
 */
export async function initializeCore(): Promise<void> {
  const bus = getEventBus();

  // Register all event handlers
  registerEventHandlers();

  // Verify database connectivity
  try {
    const pool = getPool();
    await pool.query('SELECT 1');
    console.log('[Core] Database connection verified');
  } catch (error) {
    console.error('[Core] Database connection failed:', error);
    throw error;
  }

  console.log('[Core] Financial Ledger Engine initialized successfully');
  console.log('[Core] Event handlers registered:', bus.getHandlerCount());
}

/**
 * Graceful shutdown
 */
export async function shutdownCore(): Promise<void> {
  await closePool();
  console.log('[Core] Financial Ledger Engine shut down');
}

// Re-export all public APIs
export { getEventBus } from './events/EventBus';
export { withTransaction, getPool, closePool, query } from './database/DatabaseConnection';
export { postJournalEntry, postAndFinalizeEntry, voidJournalEntry, getTrialBalance } from './ledger/JournalEntryService';
export { STANDARD_ACCOUNTS } from './ledger/types';
export type { CreateJournalEntryData, JournalEntryWithLines, AccountBalance } from './ledger/types';
export type { BaseEvent, EventType, EventPayloadMap } from './events/types';
