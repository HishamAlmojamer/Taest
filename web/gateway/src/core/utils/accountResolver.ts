/**
 * Shared Account Resolver Utility
 *
 * Provides a common function to resolve chart of accounts entries by code.
 * Resolves from the canonical `accounts` table (FastAPI chart of accounts).
 * Used by all event handlers to avoid code duplication.
 */

import { PoolClient } from 'pg';

/** Default chart-of-account codes for the cash/bank resolution used below. */
export const CASH_ACCOUNT_CODE = '1111';
export const BANK_ACCOUNT_CODE = '1121';

/** Payment method values that represent physical cash transactions. */
const CASH_PAYMENT_METHODS = /^(cash|cash_on_delivery|cod)/i;

/**
 * Determine whether a payment method should debit/credit the Cash account
 * instead of the Bank account. Anything explicitly cash-like maps to cash;
 * everything else (bank transfer, card, cheque, wallet, ...) maps to bank.
 */
export function isCashPaymentMethod(paymentMethod?: string): boolean {
  if (!paymentMethod) return false;
  const method = paymentMethod.trim().toLowerCase();
  return CASH_PAYMENT_METHODS.test(method) || method.includes('نقد');
}

/**
 * Resolve the Cash (1111) or Bank (1121) account depending on the payment
 * method. Cash-explicit methods resolve to Cash; all others resolve to Bank.
 * Individual bank accounts (via bankAccountId) are NOT resolved here - the
 * standard chart-of-accounts Bank account is used as the fallback.
 */
export async function resolveCashOrBankAccount(
  client: PoolClient,
  paymentMethod?: string,
  companyId?: number
): Promise<{ id: number; code: string; name: string }> {
  const code = isCashPaymentMethod(paymentMethod) ? CASH_ACCOUNT_CODE : BANK_ACCOUNT_CODE;
  return resolveAccount(client, code, companyId);
}

/**
 * Resolve an account by code and optional company ID
 *
 * @param client - Active PoolClient within a transaction
 * @param accountCode - The account code to search for (e.g., '1201')
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
    `SELECT id, account_code AS code, account_name AS name FROM accounts
     WHERE account_code = $1 AND is_active = true
     ${companyId ? 'AND (company_id = $2 OR company_id IS NULL)' : ''}
     LIMIT 1`,
    companyId ? [accountCode, companyId] : [accountCode]
  );

  if (result.rows.length === 0) {
    throw new Error(
      `Account with code "${accountCode}" not found in accounts. ` +
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
    `SELECT id, account_code AS code, account_name AS name FROM accounts
     WHERE account_code = ANY($1) AND is_active = true
     ${companyId ? 'AND (company_id = $2 OR company_id IS NULL)' : ''}
     ORDER BY account_code`,
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
        `Account with code "${code}" not found in accounts. ` +
        `Please ensure the standard chart of accounts is set up.`
      );
    }
  }

  return accountMap;
}
