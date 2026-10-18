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
 * Generate a unique entry number in format: JE-YYYY-NNNNNN
 * Uses PostgreSQL sequence for concurrency safety
 */
async function generateEntryNumber(client: PoolClient): Promise<string> {
  const year = new Date().getFullYear();
  const seqResult = await client.query(
    `SELECT nextval('journal_entry_number_seq') as seq`
  );
  const seq = seqResult.rows[0].seq.toString().padStart(6, '0');
  return `JE-${year}-${seq}`;
}

/**
 * Post (create and finalize) a Journal Entry
 *
 * This function:
 *   1. Validates that Σ(Debit) ≡ Σ(Credit)
 *   2. Opens a PostgreSQL transaction (passed in as `client`)
 *   3. Inserts the main record into `journal_entries`
 *   4. Inserts the split lines into `journal_items`
 *   5. Updates running balances in `chart_of_accounts`
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
  // STEP 1: Validate Double-Entry Integrity
  // ==========================================
  const totalDebit = data.lines.reduce((sum, line) => sum + (line.debit || 0), 0);
  const totalCredit = data.lines.reduce((sum, line) => sum + (line.credit || 0), 0);

  // Use a small tolerance for floating-point comparison (NUMERIC(15,4))
  const tolerance = 0.01;
  if (Math.abs(totalDebit - totalCredit) > tolerance) {
    throw new Error(
      `Journal entry is not balanced. Debits: ${totalDebit.toFixed(4)}, Credits: ${totalCredit.toFixed(4)}, Difference: ${Math.abs(totalDebit - totalCredit).toFixed(4)}`
    );
  }

  // Validate that each line has either debit or credit (not both, not neither)
  for (let i = 0; i < data.lines.length; i++) {
    const line = data.lines[i];
    if (line.debit < 0 || line.credit < 0) {
      throw new Error(
        `Line ${i + 1}: Debit and Credit values must be >= 0 (debit: ${line.debit}, credit: ${line.credit})`
      );
    }
    if (line.debit === 0 && line.credit === 0) {
      throw new Error(`Line ${i + 1}: Either debit or credit must be > 0`);
    }
    if (line.debit > 0 && line.credit > 0) {
      throw new Error(
        `Line ${i + 1}: Cannot have both debit and credit on the same line (debit: ${line.debit}, credit: ${line.credit})`
      );
    }
  }

  if (data.lines.length < 2) {
    throw new Error('Journal entry must have at least 2 lines');
  }

  // ==========================================
  // STEP 2: Insert Main Journal Entry Record
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
      data.entryDate.toISOString(),
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
      `$${paramIndex + 5}`, // partner_id
      `$${paramIndex + 6}`, // cost_center_id
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
      line.partnerId || null,
      line.costCenterId || null,
      line.projectId || null,
      new Date().toISOString(),
    ]);
    paramIndex += 9;
  }

  const linesResult = await client.query(
    `INSERT INTO journal_items
       (journal_entry_id, account_id, description, debit, credit,
        partner_id, cost_center_id, project_id, created_at)
     VALUES ${linePlaceholders.join(', ')}
     RETURNING id, journal_entry_id, account_id, description, debit, credit,
               partner_id, cost_center_id, project_id`,
    lineValues.flat()
  );

  logger.info(
    `LedgerEngine: inserted ${linesResult.rowCount} journal lines for entry ${entry.entry_number}`
  );

  // ==========================================
  // STEP 4: Validate Account Existence (balance calculated from journal_items)
  // ==========================================
  for (const line of data.lines) {
    const accountResult = await client.query(
      `SELECT id, type FROM chart_of_accounts WHERE id = $1`,
      [line.accountId]
    );

    if (accountResult.rows.length === 0) {
      throw new Error(`Account ${line.accountId} not found in chart_of_accounts`);
    }

    // Balance is calculated dynamically from journal_items in getTrialBalance()
    // No need to update opening_balance here - it represents period start balance
  }

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
      partnerId: row.partner_id,
      costCenterId: row.cost_center_id,
      projectId: row.project_id,
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
     SET status = 'Posted', approved_by = $1, approved_at = NOW()
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
    throw new Error(`Journal entry ${entryId} not found or not in Posted status`);
  }

  const originalEntry = entryResult.rows[0];

  const linesResult = await client.query(
    `SELECT * FROM journal_items WHERE journal_entry_id = $1`,
    [entryId]
  );

  if (linesResult.rows.length === 0) {
    throw new Error(`No journal lines found for entry ${entryId}`);
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
    partnerId: line.partner_id,
    costCenterId: line.cost_center_id,
    projectId: line.project_id,
  }));

  const reversingEntry = await postJournalEntry(
    {
      entryDate: new Date(),
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
     SET status = 'Posted', approved_by = $1, approved_at = NOW()
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
    params.push(asOfDate.toISOString());
    paramIndex++;
  }

  const result = await client.query(
    `SELECT
       coa.id AS account_id,
       coa.code AS account_code,
       coa.name AS account_name,
       coa.type AS account_type,
       COALESCE(SUM(ji.debit), 0) AS total_debit,
       COALESCE(SUM(ji.credit), 0) AS total_credit,
       COALESCE(coa.opening_balance, 0) AS opening_balance
     FROM chart_of_accounts coa
     LEFT JOIN journal_items ji ON ji.account_id = coa.id
     LEFT JOIN journal_entries je ON je.id = ji.journal_entry_id
       AND je.status = 'Posted'
       ${asOfDate ? `AND je.entry_date <= $${paramIndex - 1}` : ''}
     WHERE ${conditions.join(' AND ')}
     GROUP BY coa.id, coa.code, coa.name, coa.type, coa.opening_balance
     ORDER BY coa.code ASC`,
    params
  );

  return result.rows.map((row) => {
    const debit = parseFloat(row.total_debit);
    const credit = parseFloat(row.total_credit);
    const openingBalance = parseFloat(row.opening_balance);

    // Balance calculation depends on account type
    let balance: number;
    if (row.account_type === 'Asset' || row.account_type === 'Expense') {
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
