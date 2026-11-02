/**
 * Event Bus: Transactional Event Broker
 *
 * This module implements a robust pub/sub Event Broker pattern.
 * The key design requirement is transactional safety:
 *   - If a consumer fails to process an event, the parent database
 *     transaction MUST roll back.
 *   - Events are NOT persisted separately; they are processed synchronously
 *     within the caller's database transaction.
 *
 * Accounting Logic:
 *   - When an invoice is approved, the operational module emits
 *     'sales.invoice.approved' within the SAME database transaction.
 *   - The Event Bus invokes the handler which writes to the financial_ledger.
 *   - If the ledger write fails, the entire transaction rolls back,
 *     preserving data consistency.
 */

import { PoolClient } from 'pg';
import { randomUUID } from 'crypto';
import { logger } from '../../services/logger';
import {
  BaseEvent,
  EventType,
  EventHandler,
  EventPayloadMap,
  EventSubscription,
} from './types';

export class EventBus {
  private subscriptions: Map<string, EventSubscription[]>;
  private static instance: EventBus | null = null;

  private constructor() {
    this.subscriptions = new Map();
  }

  /**
   * Get singleton instance of EventBus
   */
  static getInstance(): EventBus {
    if (!EventBus.instance) {
      EventBus.instance = new EventBus();
    }
    return EventBus.instance;
  }

  /**
   * Subscribe to an event type.
   *
   * @param eventType - The event type to listen for, or '*' for all events
   * @param handler - Async function to handle the event
   * @param priority - Lower numbers execute first (default: 100)
   */
  subscribe<K extends EventType>(
    eventType: K | '*',
    handler: EventHandler<K extends EventType ? EventPayloadMap[K] : Record<string, unknown>>,
    priority: number = 100
  ): void {
    const key = eventType;
    if (!this.subscriptions.has(key)) {
      this.subscriptions.set(key, []);
    }
    this.subscriptions.get(key)!.push({
      eventType,
      handler: handler as unknown as EventHandler,
      priority,
    });
    // Sort by priority so lower-priority-number handlers run first
    this.subscriptions.get(key)!.sort((a, b) => (a.priority ?? 100) - (b.priority ?? 100));
    logger.info(`EventBus: subscribed to "${eventType}" with priority ${priority}`);
  }

  /**
   * Emit an event within a database transaction.
   *
   * This is the critical path for transactional safety:
   *   1. The caller opens a PostgreSQL transaction and passes the client.
   *   2. All subscribed handlers are invoked SYNCHRONOUSLY (awaited in order).
   *   3. If ANY handler throws, the error propagates up and the caller
   *      MUST roll back the transaction.
   *   4. If all handlers succeed, the caller commits the transaction.
   *
   * This ensures that operational writes and ledger writes are atomic.
   *
   * @param eventType - The type of event to emit
   * @param payload - The event payload data
   * @param client - Active PostgreSQL PoolClient within a transaction
   * @param metadata - Optional metadata (userId, companyId, branchId)
   */
  async emit<K extends EventType>(
    eventType: K,
    payload: EventPayloadMap[K],
    client: PoolClient,
    metadata: { userId?: number; companyId?: number; branchId?: number } = {}
  ): Promise<{ correlationId: string; results: unknown[] }> {
    const event = {
      id: randomUUID(),
      type: eventType,
      timestamp: new Date(),
      correlationId: randomUUID(),
      payload,
      metadata,
    } as unknown as BaseEvent;

    logger.info(`EventBus: emitting "${eventType}" [${event.id}]`);

    // Collect handlers for this specific event type
    const typedHandlers = this.subscriptions.get(eventType) ?? [];
    // Collect wildcard handlers
    const wildcardHandlers = this.subscriptions.get('*') ?? [];
    // Merge: typed handlers first (by priority), then wildcard handlers
    const allHandlers = [...typedHandlers, ...wildcardHandlers];

    if (allHandlers.length === 0) {
      logger.warn(`EventBus: no handlers registered for "${eventType}"`);
      return { correlationId: event.correlationId, results: [] };
    }

    // Execute all handlers within the same transaction
    const results: unknown[] = [];
    for (const subscription of allHandlers) {
      try {
        logger.info(
          `EventBus: executing handler for "${eventType}" [${event.id}]`
        );
        const handlerResult = await subscription.handler(event as unknown as BaseEvent<Record<string, unknown>>, client);
        if (handlerResult !== undefined) {
          results.push(handlerResult);
        }
        logger.info(
          `EventBus: handler completed for "${eventType}" [${event.id}]`
        );
      } catch (error) {
        logger.error(
          `EventBus: handler FAILED for "${eventType}" [${event.id}]: ${error}`
        );
        // Re-throw so the caller can roll back the transaction
        throw error;
      }
    }

    logger.info(
      `EventBus: all handlers completed for "${eventType}" [${event.id}]`
    );

    return { correlationId: event.correlationId, results };
  }

  /**
   * Remove all subscriptions (useful for testing)
   */
  clear(): void {
    this.subscriptions.clear();
  }

  /**
   * Get count of registered handlers for debugging
   */
  getHandlerCount(): Record<string, number> {
    const counts: Record<string, number> = {};
    for (const [key, handlers] of this.subscriptions) {
      counts[key] = handlers.length;
    }
    return counts;
  }
}

/**
 * Convenience function to get the EventBus singleton
 */
export function getEventBus(): EventBus {
  return EventBus.getInstance();
}
