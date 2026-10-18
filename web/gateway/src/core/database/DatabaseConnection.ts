/**
 * Database Connection: PostgreSQL Pool Manager
 *
 * Provides a managed PostgreSQL connection pool with transaction support.
 * All financial operations MUST go through transactional clients to ensure
 * atomicity of multi-table writes (e.g., journal_entries + journal_items).
 */

import { Pool, PoolClient, PoolConfig, QueryResult } from 'pg';
import { config } from '../../config';
import { logger } from '../../services/logger';

let pool: Pool | null = null;

/**
 * Get or create the PostgreSQL connection pool.
 * Uses the same DATABASE_URL from the gateway config (shared with Python backend).
 */
export function getPool(): Pool {
  if (!pool) {
    const connectionString = process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/warehouse_management';
    const poolConfig: PoolConfig = {
      connectionString,
      max: 20,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 5000,
    };

    pool = new Pool(poolConfig);

    pool.on('error', (err) => {
      logger.error(`DatabasePool: unexpected error on idle client: ${err.message}`);
    });

    pool.on('connect', () => {
      logger.debug('DatabasePool: new client connected');
    });

    logger.info('DatabasePool: initialized');
  }
  return pool;
}

/**
 * Execute a function within a database transaction.
 *
 * Accounting Logic:
 *   - All financial writes (journal entries, balance updates) MUST use this.
 *   - If the function throws, the transaction is automatically rolled back.
 *   - If the function succeeds, the transaction is committed.
 *   - This guarantees the ACID properties required for double-entry bookkeeping.
 *
 * @param fn - Async function that receives a PoolClient and performs work
 * @returns The return value of the function
 *
 * @example
 * ```typescript
 * const entry = await withTransaction(async (client) => {
 *   const result = await client.query(
 *     'INSERT INTO journal_entries (...) VALUES (...) RETURNING id',
 *     [...]
 *   );
 *   await client.query(
 *     'INSERT INTO journal_items (...) VALUES (...)',
 *     [...]
 *   );
 *   return result.rows[0];
 * });
 * ```
 */
export async function withTransaction<T>(
  fn: (client: PoolClient) => Promise<T>
): Promise<T> {
  const pool = getPool();
  const client = await pool.connect();

  try {
    await client.query('BEGIN');
    logger.debug('Transaction: BEGIN');

    const result = await fn(client);

    await client.query('COMMIT');
    logger.debug('Transaction: COMMIT');

    return result;
  } catch (error) {
    logger.error(`Transaction: ROLLBACK - ${error}`);
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
}

/**
 * Execute a raw SQL query (non-transactional)
 */
export async function query(text: string, params?: unknown[]): Promise<QueryResult> {
  const pool = getPool();
  return pool.query(text, params);
}

/**
 * Close the pool (for graceful shutdown)
 */
export async function closePool(): Promise<void> {
  if (pool) {
    await pool.end();
    pool = null;
    logger.info('DatabasePool: closed');
  }
}
