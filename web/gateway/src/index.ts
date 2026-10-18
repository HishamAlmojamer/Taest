import dotenv from 'dotenv';
dotenv.config();

import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import { createServer } from 'http';
import { config } from './config';
import { apiLimiter } from './middleware/rateLimit';
import { authenticate } from './middleware/auth';
import { errorHandler } from './middleware/errorHandler';
import { logger } from './services/logger';
import { createWsProxy } from './services/wsProxy';

import authRouter from './routes/auth';
import { createBackendProxy } from './services/pythonProxy';

// =============================================================================
// Core Financial Engine Initialization
// =============================================================================
import { initializeCore, shutdownCore, getEventBus, withTransaction, getPool } from './core';
import { EventType } from './core/events/types';
import { PoolClient } from 'pg';

const app = express();
const server = createServer(app);

// =============================================================================
// Middleware
// =============================================================================
app.use(helmet());
app.use(cors({
  origin: config.corsOrigins,
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
}));
app.use(apiLimiter);
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// =============================================================================
// Health Check
// =============================================================================
app.get('/health', async (_req, res) => {
  try {
    const pool = getPool();
    await pool.query('SELECT 1');
    res.json({
      status: 'ok',
      service: 'erp-gateway',
      timestamp: new Date().toISOString(),
      core: 'initialized',
      database: 'connected',
    });
  } catch (error) {
    res.status(503).json({
      status: 'error',
      service: 'erp-gateway',
      timestamp: new Date().toISOString(),
      database: 'disconnected',
    });
  }
});

// =============================================================================
// Financial Ledger API Endpoints
// =============================================================================

/**
 * POST /api/ledger/emit
 * Emit a domain event within a database transaction.
 * This is the bridge between operational modules and the financial ledger.
 *
 * Request body:
 *   { type: EventType, payload: EventPayloadMap[K], metadata?: {...} }
 */
app.post('/api/ledger/emit', authenticate, async (req, res, next) => {
  try {
    const { type, payload, metadata } = req.body;

    if (!type || !payload) {
      return res.status(400).json({
        success: false,
        message: 'Missing required fields: type, payload',
      });
    }

    const bus = getEventBus();

    // Execute within a database transaction for atomicity
    const result = await withTransaction(async (client: PoolClient) => {
      await bus.emit(type as EventType, payload, client, metadata || {});
      return { success: true, eventType: type };
    });

    res.json({
      success: true,
      message: `Event "${type}" processed successfully`,
      data: result,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/ledger/trial-balance
 * Generate a trial balance report.
 *
 * Query params:
 *   companyId? - Filter by company
 *   asOfDate?  - Date to calculate balances as of (ISO string)
 */
app.get('/api/ledger/trial-balance', authenticate, async (req, res, next) => {
  try {
    const { getTrialBalance } = await import('./core/ledger/JournalEntryService');
    const { withTransaction: wt } = await import('./core/database/DatabaseConnection');

    const companyId = req.query.companyId ? parseInt(req.query.companyId as string) : undefined;
    const asOfDate = req.query.asOfDate ? new Date(req.query.asOfDate as string) : undefined;

    const result = await wt(async (client: PoolClient) => {
      return getTrialBalance(client, companyId, asOfDate);
    });

    const totalDebit = result.reduce((sum, a) => sum + a.totalDebit, 0);
    const totalCredit = result.reduce((sum, a) => sum + a.totalCredit, 0);

    res.json({
      success: true,
      data: {
        accounts: result,
        totalDebit,
        totalCredit,
        isBalanced: Math.abs(totalDebit - totalCredit) < 0.01,
      },
    });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/ledger/journal-entries
 * Create a new journal entry directly (without going through event bus).
 * Use this for manual journal entries or adjustments.
 */
app.post('/api/ledger/journal-entries', authenticate, async (req, res, next) => {
  try {
    const { postJournalEntry } = await import('./core/ledger/JournalEntryService');
    const { withTransaction: wt } = await import('./core/database/DatabaseConnection');

    const entryData = {
      ...req.body,
      entryDate: new Date(req.body.entryDate),
    };

    const result = await wt(async (client: PoolClient) => {
      return postJournalEntry(entryData, client);
    });

    res.status(201).json({
      success: true,
      message: 'Journal entry created successfully',
      data: result,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/ledger/journal-entries/:id/void
 * Void a posted journal entry and create a reversing entry.
 */
app.post('/api/ledger/journal-entries/:id/void', authenticate, async (req, res, next) => {
  try {
    const { voidJournalEntry } = await import('./core/ledger/JournalEntryService');
    const { withTransaction: wt } = await import('./core/database/DatabaseConnection');

    const entryId = parseInt(req.params.id as string);
    const { reason } = req.body;

    if (!reason) {
      return res.status(400).json({
        success: false,
        message: 'Reason is required to void a journal entry',
      });
    }

    const result = await wt(async (client: PoolClient) => {
      return voidJournalEntry(entryId, reason, client);
    });

    res.json({
      success: true,
      message: `Journal entry voided successfully. Reversing entry: ${result.entryNumber}`,
      data: result,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/ledger/accounts
 * List all chart of accounts with balances.
 */
app.get('/api/ledger/accounts', authenticate, async (req, res, next) => {
  try {
    const { query: q } = await import('./core/database/DatabaseConnection');

    const result = await q(`
      SELECT
        id, code, name, name_ar, type, parent_id,
        is_active, opening_balance, currency_code, created_at
      FROM chart_of_accounts
      WHERE is_active = true
      ORDER BY code ASC
    `);

    res.json({
      success: true,
      data: result.rows,
    });
  } catch (error) {
    next(error);
  }
});

// =============================================================================
// Routes
// =============================================================================
const proxy = createBackendProxy();
app.use('/api/auth', authRouter);
app.use('/api', proxy);
app.use(errorHandler);

// =============================================================================
// WebSocket Proxy
// =============================================================================
const wsProxy = createWsProxy();
server.on('upgrade', (req, socket, head) => {
  if (req.url?.startsWith('/ws')) {
    (wsProxy as any).upgrade(req, socket, head);
  }
});

// =============================================================================
// Startup
// =============================================================================
async function startServer() {
  try {
    // Initialize the core financial engine
    await initializeCore();
    logger.info('[Core] Financial Ledger Engine ready');

    // Start listening
    server.listen(config.port, () => {
      logger.info(`ERP Gateway running on port ${config.port}`);
      logger.info(`Python backend: ${config.pythonBackendUrl}`);
      logger.info(`CORS origins: ${config.corsOrigins.join(', ')}`);
      logger.info('---');
      logger.info('Financial Ledger API Endpoints:');
      logger.info('  POST /api/ledger/emit              - Emit domain events');
      logger.info('  GET  /api/ledger/trial-balance      - Trial balance report');
      logger.info('  POST /api/ledger/journal-entries     - Create journal entry');
      logger.info('  POST /api/ledger/journal-entries/:id/void - Void journal entry');
      logger.info('  GET  /api/ledger/accounts            - Chart of accounts');
    });
  } catch (error) {
    logger.error('Failed to start ERP Gateway:', error);
    process.exit(1);
  }
}

// =============================================================================
// Graceful Shutdown
// =============================================================================
process.on('SIGTERM', async () => {
  logger.info('SIGTERM received, shutting down gracefully...');
  await shutdownCore();
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', async () => {
  logger.info('SIGINT received, shutting down gracefully...');
  await shutdownCore();
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

startServer();

export { app, server };
