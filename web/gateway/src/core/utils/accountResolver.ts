/**
 * Shared Account Resolver Utility
 *
 * Provides a common function to resolve chart of accounts entries by code.
 * Used by all event handlers to avoid code duplication.
 */

import { PoolClient } from 'pg';

/**
 * Resolve an account by code and optional company ID
 *
 * @param client - Active PoolClient within a transaction
 * @param accountCode - The account code to search for (e.g., '1130')
 * @param companyId - Optional company ID for multi-company support
 * @returns The account record with id, code, and name
 * @throws Error if account not found
 */
export async function resolveAccount(
  client: PoolClient,
  accountCode: string,
  companyId?: number
): Promise<{ id: number; code: string; name: string }> {
  const result = await client.query(
    `SELECT id, code, name FROM chart_of_accounts
     WHERE code = $1 AND is_active = true
     ${companyId ? 'AND (company_id = $2 OR company_id IS NULL)' : ''}
     LIMIT 1`,
    companyId ? [accountCode, companyId] : [accountCode]
  );

  if (result.rows.length === 0) {
    throw new Error(
      `Account with code "${accountCode}" not found in chart_of_accounts. ` +
      `Please ensure the standard chart of accounts is set up.`
    );
  }

  return result.rows[0];
}

/**
 * Resolve multiple accounts by codes in a single query for performance
 *
 * @param client - Active PoolClient within a transaction
 * @param accountCodes - Array of account codes to resolve
 * @param companyId - Optional company ID for multi-company support
 * @returns Map of account code to account record
 */
export async function resolveAccounts(
  client: PoolClient,
  accountCodes: string[],
  companyId?: number
): Promise<Map<string, { id: number; code: string; name: string }>> {
  const result = await client.query(
    `SELECT id, code, name FROM chart_of_accounts
     WHERE code = ANY($1) AND is_active = true
     ${companyId ? 'AND (company_id = $2 OR company_id IS NULL)' : ''}
     ORDER BY code`,
    companyId ? [accountCodes, companyId] : [accountCodes]
  );

  const accountMap = new Map<string, { id: number; code: string; name: string }>();
  for (const row of result.rows) {
    accountMap.set(row.code, { id: row.id, code: row.code, name: row.name });
  }

  // Validate all requested accounts were found
  for (const code of accountCodes) {
    if (!accountMap.has(code)) {
      throw new Error(
        `Account with code "${code}" not found in chart_of_accounts. ` +
        `Please ensure the standard chart of accounts is set up.`
      );
    }
  }

  return accountMap;
}
