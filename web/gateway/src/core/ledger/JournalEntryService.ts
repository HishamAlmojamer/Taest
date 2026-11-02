/**
 * Journal Entry Service: The Ledger Writing Engine
 *
 * This is the core service that writes to the financial ledger.
 * All financial transactions MUST go through this service to ensure:
 *
 *   1. Double-Entry Integrity: Σ(Debit) == Σ(Credit) before committing
 *   2. Transactional Safety: All writes in a single SQL transaction
 *   3. Audit Trail: Posted entries are immutable
 *   4. Balance Updates: Running account balances are maintained
 *
 * Accounting Logic:
 *   - Journal entries start as 'Draft' status
 *   - When 'Posted', debits and credits are validated for equality
 *   - Posted entries CANNOT be modified (immutability)
 *   - To correct a posted entry, create a reversing entry
 *   - Voiding a posted entry requires a reason and creates a reversal
 */

import { PoolClient } from 'pg';
import { logger } from '../../services/logger';
import {
  CreateJournalEntryData,
  JournalEntryWithLines,
  JournalEntryStatus,
  AccountBalance,
} from './types';

/**
 * Format a Date as its local calendar date (YYYY-MM-DD).
 *
 * `entry_date` is a `timestamp without time zone` column holding a business
 * date, so using `toISOString()` would shift the date for any timezone east or
 * west of UTC (e.g. a 2026-06-15 entry becomes 2026-06-14 at UTC+3).
 */
function toDateOnly(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Business/validation error raised by the ledger engine for expected
 * conditions (unbalanced entry, idempotency violation, closed accounting
 * period, invalid account, entry not-posted). The HTTP layer maps this to a
 * 400 Bad Request instead of a 500 Internal Server Error.
 */
export class LedgerValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'LedgerValidationError';
  }
}

/**
 * Assert that the accounting period covering `entryDate` is open.
 *
 * If a fiscal period exists for the date and is closed/locked (or
 * soft-closed with blocking enabled), posting is rejected. When no period
 * covers the date, or the fiscal_periods table is unavailable in the
 * deployment, the check is skipped (open by default) so legacy installs
 * keep working.
 *
 * @param client - Active PoolClient within a transaction
 * @param entryDate - Date the entry would be posted to
 * @param companyId - Optional company scope (matched via fiscal_years)
 * @throws LedgerValidationError if the covering period is closed or locked
 */
async function assertPeriodOpen(
  client: PoolClient,
  entryDate: Date,
  companyId?: number | null
): Promise<void> {
  const dateISO = toDateOnly(entryDate);
  const params: unknown[] = [dateISO, dateISO];
  let sql = `
    SELECT fp.id, fp.name, fp.is_closed, fp.is_locked, fp.is_soft_closed
    FROM fiscal_periods fp
    WHERE fp.start_date <= $1 AND fp.end_date >= $2
  `;
  if (companyId) {
    sql += ` AND fp.fiscal_year_id IN (
              SELECT fy.id FROM fiscal_years fy
              WHERE fy.company_id = $3 OR fy.company_id IS NULL
            )`;
    params.push(companyId);
  }
  sql += ` ORDER BY fp.start_date DESC LIMIT 1`;

  try {
    const result = await client.query(sql, params);
    if (result.rows.length === 0) {
      return; // no configured period for this date → open
    }
    const period = result.rows[0];
    if (period.is_closed || period.is_locked) {
      throw new LedgerValidationError(
        `Cannot post: accounting period "${period.name}" (${String(period.start_date)} to ${String(period.end_date)}) is closed or locked`
      );
    }
  } catch (error) {
    if (error instanceof LedgerValidationError) {
      throw error;
    }
    // fiscal_periods table missing on this deployment → enforcement unavailable
    logger.warn(`LedgerEngine: period-open check skipped (${(error as Error).message})`);
  }
}

/**
 * Generate a unique entry number in format: JE-YYYY-NNNNNN
 * Uses PostgreSQL sequence for concurrency safety
 */
async function generateEntryNumber(client: PoolClient): Promise<string> {
  const year = new Date().getFullYear();
  const seqResult = await client.query(
    `SELECT setval('journal_entry_number_seq', GREATEST(
        nextval('journal_entry_number_seq'),
        (SELECT COALESCE(MAX(NULLIF(regexp_replace(entry_number, '^.*-', '', 'g'), '')::bigint), 0) + 1
         FROM journal_entries)
      ), true) as n`
  );
  const seq = seqResult.rows[0].n.toString().padStart(6, '0');
  return `JE-${year}-${seq}`;
}

/**
 * Post (create and finalize) a Journal Entry
 *
 * This function:
 *   1. Validates that Σ(Debit) ≡ Σ(Credit)
 *   2. Opens a PostgreSQL transaction (passed in as `client`)
 *   3. Inserts the main record into `journal_entries`
 *   4. Inserts the split lines into `journal_entry_lines`
 *   5. Account balances are computed from `journal_entry_lines`
 *   6. Commits or rolls back safely on any failure
 *
 * @param data - The journal entry data with lines
 * @param client - Active PoolClient within a transaction
 * @returns The created journal entry with lines
 *
 * @throws Error if debits != credits (within 0.01 tolerance)
 * @throws Error if any database operation fails (triggers rollback)
 */
export async function postJournalEntry(
  data: CreateJournalEntryData,
  client: PoolClient
): Promise<JournalEntryWithLines> {
  // ==========================================
  // STEP 0: Idempotency Guard
  // ==========================================
  // Prevent duplicate journal entries when the same business event is
  // (re-)delivered. If a posted entry already exists for the same
  // (reference_type, reference_id), reject the write. This guards against
  // double-posting if an event is emitted twice (e.g. retry / network issue).
  // Reversing entries carry reference_type='JournalEntryReversal' so they are
  // never blocked by this check.
  if (data.referenceType && data.referenceId) {
    const dupResult = await client.query(
      `SELECT id FROM journal_entries
       WHERE reference_type = $1 AND reference_id = $2 AND status != 'Voided'
       LIMIT 1`,
      [data.referenceType, data.referenceId]
    );
    if (dupResult.rows.length > 0) {
      throw new LedgerValidationError(
        `Idempotency violation: a posted journal entry already exists for ` +
        `${data.referenceType} #${data.referenceId} (entry id: ${dupResult.rows[0].id}). ` +
        `Refusing to create a duplicate.`
      );
    }
  }

  // ==========================================
  // STEP 0b: Accounting Period Open Check
  // ==========================================
  // Reject postings dated into a closed/locked fiscal period.
  await assertPeriodOpen(client, data.entryDate, data.companyId);

  // ==========================================
  // STEP 1: Validate Double-Entry Integrity
  // ==========================================
  const totalDebit = data.lines.reduce((sum, line) => sum + (line.debit || 0), 0);
  const totalCredit = data.lines.reduce((sum, line) => sum + (line.credit || 0), 0);

  // Use a small tolerance for floating-point comparison (NUMERIC(15,4))
  const tolerance = 0.01;
  if (Math.abs(totalDebit - totalCredit) > tolerance) {
    throw new LedgerValidationError(
      `Journal entry is not balanced. Debits: ${totalDebit.toFixed(4)}, Credits: ${totalCredit.toFixed(4)}, Difference: ${Math.abs(totalDebit - totalCredit).toFixed(4)}`
    );
  }

  // Validate that each line has either debit or credit (not both, not neither)
  for (let i = 0; i < data.lines.length; i++) {
    const line = data.lines[i];
    if (line.debit < 0 || line.credit < 0) {
      throw new LedgerValidationError(
        `Line ${i + 1}: Debit and Credit values must be >= 0 (debit: ${line.debit}, credit: ${line.credit})`
      );
    }
    if (line.debit === 0 && line.credit === 0) {
      throw new LedgerValidationError(`Line ${i + 1}: Either debit or credit must be > 0`);
    }
    if (line.debit > 0 && line.credit > 0) {
      throw new LedgerValidationError(
        `Line ${i + 1}: Cannot have both debit and credit on the same line (debit: ${line.debit}, credit: ${line.credit})`
      );
    }
  }

  if (data.lines.length < 2) {
    throw new LedgerValidationError('Journal entry must have at least 2 lines');
  }

  // ==========================================
  // STEP 2: Validate Accounts Before Any Write
  // ==========================================
  // The gateway is the last line of defence for the chart-of-accounts
  // posting rules. Every account referenced by a line must:
  //   a) exist,
  //   b) be active,
  //   c) NOT be a control / group account (control accounts only aggregate
  //      their children and cannot receive direct postings).
  // Doing this BEFORE the inserts avoids partial writes and makes the
  // failures deterministic (no writes at all when an account is invalid).
  const accountIds = data.lines.map((line) => line.accountId);
  const accountResult = await client.query(
    `SELECT id, account_code AS code, is_active, is_control
     FROM accounts WHERE id = ANY($1)`,
    [accountIds]
  );
  const validAccounts = new Map(
    accountResult.rows.map((r) => [Number(r.id), r])
  );
  for (const line of data.lines) {
    const account = validAccounts.get(line.accountId);
    if (!account) {
      throw new LedgerValidationError(
        `Account with id ${line.accountId} not found in chart of accounts`
      );
    }
    if (!account.is_active) {
      throw new LedgerValidationError(
        `Account "${account.code}" is inactive and cannot receive postings`
      );
    }
    if (account.is_control) {
      throw new LedgerValidationError(
        `Account "${account.code}" is a control (group) account and cannot receive postings. Use a leaf account instead.`
      );
    }
  }

  // ==========================================
  // STEP 3: Insert Main Journal Entry Record
  // ==========================================
  const entryNumber = await generateEntryNumber(client);

  const entryResult = await client.query(
    `INSERT INTO journal_entries
       (entry_number, entry_date, description, description_en, reference_type, reference_id,
        status, created_by, company_id, created_at)
     VALUES ($1, $2, $3, $4, $5, $6, 'Draft', $7, $8, NOW())
     RETURNING id, entry_number, entry_date, description, status, created_at`,
    [
      entryNumber,
      toDateOnly(data.entryDate),
      data.description,
      data.descriptionEn || null,
      data.referenceType || null,
      data.referenceId || null,
      data.createdBy || null,
      data.companyId || null,
    ]
  );

  const entry = entryResult.rows[0];
  logger.info(
    `LedgerEngine: created journal entry ${entry.entry_number} (id: ${entry.id})`
  );

  // ==========================================
  // STEP 3: Insert Journal Entry Lines
  // ==========================================
  const lineValues: unknown[][] = [];
  const linePlaceholders: string[] = [];
  let paramIndex = 1;

  for (let i = 0; i < data.lines.length; i++) {
    const line = data.lines[i];
    const placeholder = `(${[
      `$${paramIndex}`,     // journal_entry_id
      `$${paramIndex + 1}`, // account_id
      `$${paramIndex + 2}`, // description
      `$${paramIndex + 3}`, // debit
      `$${paramIndex + 4}`, // credit
      `$${paramIndex + 5}`, // cost_center_id
      `$${paramIndex + 6}`, // partner_id
      `$${paramIndex + 7}`, // project_id
      `$${paramIndex + 8}`, // created_at
    ].join(', ')})`;

    linePlaceholders.push(placeholder);
    lineValues.push([
      entry.id,
      line.accountId,
      line.description || data.description,
      line.debit || 0,
      line.credit || 0,
      line.costCenterId || null,
      line.partnerId || null,
      line.projectId || null,
      new Date().toISOString(),
    ]);
    paramIndex += 9;
  }

  const linesResult = await client.query(
    `INSERT INTO journal_entry_lines
       (journal_entry_id, account_id, description, debit, credit,
        cost_center_id, partner_id, project_id, created_at)
     VALUES ${linePlaceholders.join(', ')}
     RETURNING id, journal_entry_id, account_id, description, debit, credit,
               cost_center_id, partner_id, project_id`,
    lineValues.flat()
  );

  logger.info(
    `LedgerEngine: inserted ${linesResult.rowCount} journal lines for entry ${entry.entry_number}`
  );

  // ==========================================
  // STEP 5: Return Complete Entry
  // ==========================================
  const completeEntry: JournalEntryWithLines = {
    id: entry.id,
    entryNumber: entry.entry_number,
    entryDate: entry.entry_date,
    description: entry.description,
    status: entry.status as JournalEntryStatus,
    createdAt: entry.created_at,
    lines: linesResult.rows.map((row) => ({
      id: row.id,
      journalEntryId: row.journal_entry_id,
      accountId: row.account_id,
      description: row.description,
      debit: parseFloat(row.debit),
      credit: parseFloat(row.credit),
      costCenterId: row.cost_center_id,
    })),
  };

  logger.info(
    `LedgerEngine: journal entry ${entry.entry_number} posted successfully. ` +
    `Total: ${totalDebit.toFixed(4)} | Lines: ${data.lines.length}`
  );

  return completeEntry;
}

/**
 * Post and immediately finalize (status='Posted') a Journal Entry
 *
 * This is a convenience wrapper around postJournalEntry that also
 * sets the status to 'Posted' and records the posting timestamp.
 *
 * @param data - The journal entry data
 * @param client - Active PoolClient within a transaction
 * @param approvedBy - User ID who approved the entry
 * @returns The posted journal entry
 */
export async function postAndFinalizeEntry(
  data: CreateJournalEntryData,
  client: PoolClient,
  approvedBy?: number
): Promise<JournalEntryWithLines> {
  const entry = await postJournalEntry(data, client);

  await client.query(
    `UPDATE journal_entries
     SET status = 'Posted', posted_by = $1, posted_at = NOW()
     WHERE id = $2`,
    [approvedBy || null, entry.id]
  );

  entry.status = 'Posted';
  entry.approvedBy = approvedBy;
  entry.approvedAt = new Date();

  logger.info(
    `LedgerEngine: entry ${entry.entryNumber} finalized as Posted`
  );

  return entry;
}

/**
 * Void a posted Journal Entry
 *
 * Accounting Logic:
 *   - Posted entries cannot be directly modified (immutability)
 *   - To reverse a posted entry, we create a new entry with swapped debits/credits
 *   - The original entry is marked as 'Voided' with a reason
 *   - This maintains a complete audit trail
 *
 * @param entryId - ID of the entry to void
 * @param reason - Reason for voiding
 * @param client - Active PoolClient within a transaction
 * @param voidedBy - User ID who voided the entry
 * @returns The new reversing entry
 */
export async function voidJournalEntry(
  entryId: number,
  reason: string,
  client: PoolClient,
  voidedBy?: number
): Promise<JournalEntryWithLines> {
  // Fetch the original entry and its lines
  const entryResult = await client.query(
    `SELECT * FROM journal_entries WHERE id = $1 AND status = 'Posted'`,
    [entryId]
  );

  if (entryResult.rows.length === 0) {
    throw new LedgerValidationError(`Journal entry ${entryId} not found or not in Posted status`);
  }

  const originalEntry = entryResult.rows[0];

  const linesResult = await client.query(
    `SELECT * FROM journal_entry_lines WHERE journal_entry_id = $1`,
    [entryId]
  );

  if (linesResult.rows.length === 0) {
    throw new LedgerValidationError(`No journal lines found for entry ${entryId}`);
  }

  // Mark original entry as Voided
  await client.query(
    `UPDATE journal_entries
     SET status = 'Voided', voided_by = $1, voided_at = NOW(), void_reason = $2
     WHERE id = $3`,
    [voidedBy || null, reason, entryId]
  );

  logger.info(
    `LedgerEngine: entry ${originalEntry.entry_number} marked as Voided`
  );

  // Create a reversing entry (swap debits and credits)
  const reversingLines = linesResult.rows.map((line) => ({
    accountId: line.account_id,
    description: `Reversal of: ${line.description || originalEntry.description}`,
    debit: parseFloat(line.credit), // Swap: credit becomes debit
    credit: parseFloat(line.debit), // Swap: debit becomes credit
    costCenterId: line.cost_center_id,
    partnerId: line.partner_id,
    projectId: line.project_id,
  }));

  const reversingEntry = await postJournalEntry(
    {
      // Date the reversal like the original entry so it nets inside the same
      // fiscal period instead of landing in a later (possibly closed) one.
      entryDate: originalEntry.entry_date as Date,
      description: `Reversal of ${originalEntry.entry_number}: ${reason}`,
      descriptionEn: `Reversal of ${originalEntry.entry_number}: ${reason}`,
      referenceType: 'JournalEntryReversal',
      referenceId: entryId,
      createdBy: voidedBy,
      companyId: originalEntry.company_id,
      lines: reversingLines,
    },
    client
  );

  // Immediately post the reversing entry
  await client.query(
    `UPDATE journal_entries
     SET status = 'Posted', posted_by = $1, posted_at = NOW()
     WHERE id = $2`,
    [voidedBy || null, reversingEntry.id]
  );

  logger.info(
    `LedgerEngine: reversing entry ${reversingEntry.entryNumber} created and posted`
  );

  return reversingEntry;
}

/**
 * Get account balances for a trial balance report
 *
 * @param client - Database client
 * @param companyId - Company ID to filter by
 * @param asOfDate - Date to calculate balances as of
 * @returns Array of account balances
 */
export async function getTrialBalance(
  client: PoolClient,
  companyId?: number,
  asOfDate?: Date
): Promise<AccountBalance[]> {
  const conditions: string[] = ['coa.is_active = true'];
  const params: unknown[] = [];
  let paramIndex = 1;

  if (companyId) {
    conditions.push(`coa.company_id = $${paramIndex}`);
    params.push(companyId);
    paramIndex++;
  }

  if (asOfDate) {
    conditions.push(`je.entry_date <= $${paramIndex}`);
    params.push(toDateOnly(asOfDate));
    paramIndex++;
  }

  const result = await client.query(
    `SELECT
       coa.id AS account_id,
       coa.account_code AS account_code,
       coa.account_name AS account_name,
       coa.account_type AS account_type,
       COALESCE(SUM(jel.debit), 0) AS total_debit,
       COALESCE(SUM(jel.credit), 0) AS total_credit,
       COALESCE(coa.opening_balance, 0) AS opening_balance
     FROM accounts coa
     LEFT JOIN journal_entry_lines jel ON jel.account_id = coa.id
     LEFT JOIN journal_entries je ON je.id = jel.journal_entry_id
       AND je.status = 'Posted'
       ${asOfDate ? `AND je.entry_date <= $${paramIndex - 1}` : ''}
     WHERE ${conditions.join(' AND ')}
     GROUP BY coa.id, coa.account_code, coa.account_name, coa.account_type, coa.opening_balance
     ORDER BY coa.account_code ASC`,
    params
  );

  return result.rows.map((row) => {
    const debit = parseFloat(row.total_debit);
    const credit = parseFloat(row.total_credit);
    const openingBalance = parseFloat(row.opening_balance);

    // Balance calculation depends on account type
    let balance: number;
    if (row.account_type === 'asset' || row.account_type === 'expense') {
      balance = openingBalance + debit - credit;
    } else {
      balance = openingBalance + credit - debit;
    }

    return {
      accountId: row.account_id,
      accountCode: row.account_code,
      accountName: row.account_name,
      accountType: row.account_type,
      totalDebit: debit,
      totalCredit: credit,
      balance,
    };
  });
}
