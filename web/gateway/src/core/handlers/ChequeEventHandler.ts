/**
 * Cheque Event Handler: Received / Issued / Deposited / Cleared / Returned
 *
 * Accounting Logic for cheque.received (customer hands us a cheque):
 *
 *   1. DEBIT Cheques on Hand (Asset increases - physical cheque in our possession)
 *      - Account: 1205 - Cheques on Hand
 *      - Amount: cheque amount
 *
 *   2. CREDIT Accounts Receivable (customer's debt is reduced)
 *      - Account: 1201 - Accounts Receivable
 *      - Amount: cheque amount
 *
 * Accounting Logic for cheque.issued (we write a cheque to a supplier):
 *
 *   1. DEBIT Accounts Payable (liability reduced - we owe the supplier less)
 *      - Account: 2111 - Accounts Payable
 *      - Amount: cheque amount
 *
 *   2. CREDIT Cheques Issued (outstanding cheques liability until clearance)
 *      - Account: 2124 - Cheques Issued
 *      - Amount: cheque amount
 *
 * Accounting Logic for cheque.deposited (received cheque handed to the bank):
 *
 *   1. DEBIT Bank (money now in our bank account)
 *      - Account: 1121 - Bank Accounts
 *      - Amount: cheque amount
 *
 *   2. CREDIT Cheques on Hand (cheque no longer physically in our possession)
 *      - Account: 1205 - Cheques on Hand
 *      - Amount: cheque amount
 *
 * Accounting Logic for cheque.cleared (issued cheque cashed by the bank):
 *
 *   1. DEBIT Cheques Issued (outstanding liability settled)
 *      - Account: 2124 - Cheques Issued
 *      - Amount: cheque amount
 *
 *   2. CREDIT Bank (money actually leaves our bank account)
 *      - Account: 1121 - Bank Accounts
 *      - Amount: cheque amount
 *
 * Accounting Logic for cheque.returned (bounced/returned cheque):
 *
 *   - Deposited received cheque bounced (preStatus deposited/under_collection):
 *       Dr. Accounts Receivable (1201)   amount   (customer owes again)
 *       Cr. Bank (1121)                  amount   (bank returned the funds)
 *
 *   - Received cheque returned before deposit (preStatus on_hand):
 *       Reverses the original received entry:
 *       Dr. Accounts Receivable (1201) / Cr. Cheques on Hand (1205)
 *
 *   - Issued cheque returned: reverses the original issued entry
 *     (Dr. Cheques Issued 2124 / Cr. Accounts Payable 2111).
 */

import { PoolClient } from 'pg';
import { BaseEvent, ChequeReturnedPayload } from '../events/types';
import { postAndFinalizeEntry, voidJournalEntry } from '../ledger/JournalEntryService';
import { CreateJournalEntryData, STANDARD_ACCOUNTS } from '../ledger/types';
import { logger } from '../../services/logger';
import { resolveAccounts } from '../utils/accountResolver';

/**
 * Handle the cheque.received event
 *
 * Dr Cheques on Hand / Cr Accounts Receivable.
 */
export async function handleChequeReceived(
  event: BaseEvent<{ chequeId: number; chequeNumber: string; amount: number; customerId?: number; customerName?: string }>,
  client: PoolClient
): Promise<{ entryId: number; entryNumber: string }> {
  const { payload, metadata } = event;

  logger.info(
    `ChequeEventHandler: processing cheque.received ${payload.chequeNumber} ` +
    `(id: ${payload.chequeId}, amount: ${payload.amount})`
  );

  const accountCodes = [
    STANDARD_ACCOUNTS.CHEQUES_ON_HAND.code,
    payload.customerId
      ? STANDARD_ACCOUNTS.ACCOUNTS_RECEIVABLE.code
      : STANDARD_ACCOUNTS.OTHER_RECEIVABLES.code,
  ];
  const accounts = await resolveAccounts(client, accountCodes, metadata.companyId);

  const onHandAccount = accounts.get(STANDARD_ACCOUNTS.CHEQUES_ON_HAND.code)!;
  const counterpart = payload.customerId
    ? accounts.get(STANDARD_ACCOUNTS.ACCOUNTS_RECEIVABLE.code)!
    : accounts.get(STANDARD_ACCOUNTS.OTHER_RECEIVABLES.code)!;

  const lines: CreateJournalEntryData['lines'] = [
    {
      accountId: onHandAccount.id,
      description: `Received cheque ${payload.chequeNumber}`,
      debit: payload.amount,
      credit: 0,
      partnerId: payload.customerId,
    },
    {
      accountId: counterpart.id,
      description: `Received cheque ${payload.chequeNumber} applied to customer`,
      debit: 0,
      credit: payload.amount,
      partnerId: payload.customerId,
    },
  ];

  const journalData: CreateJournalEntryData = {
    entryDate: new Date(),
    description: `Received Cheque - ${payload.chequeNumber}`,
    descriptionEn: `Received Cheque - ${payload.chequeNumber}`,
    referenceType: 'Cheque',
    referenceId: payload.chequeId,
    createdBy: metadata.userId,
    companyId: metadata.companyId,
    lines,
  };

  const journalEntry = await postAndFinalizeEntry(journalData, client, metadata.userId);

  logger.info(
    `ChequeEventHandler: journal entry ${journalEntry.entryNumber} created for received cheque ` +
    `| Dr. Cheques on Hand: ${payload.amount} | Cr. Receivable: ${payload.amount}`
  );

  return { entryId: journalEntry.id, entryNumber: journalEntry.entryNumber };
}

/**
 * Handle the cheque.issued event
 *
 * Dr Accounts Payable / Cr Cheques Issued.
 */
export async function handleChequeIssued(
  event: BaseEvent<{ chequeId: number; chequeNumber: string; amount: number; supplierId?: number; supplierName?: string }>,
  client: PoolClient
): Promise<{ entryId: number; entryNumber: string }> {
  const { payload, metadata } = event;

  logger.info(
    `ChequeEventHandler: processing cheque.issued ${payload.chequeNumber} ` +
    `(id: ${payload.chequeId}, amount: ${payload.amount})`
  );

  const accountCodes = [
    STANDARD_ACCOUNTS.ACCOUNTS_PAYABLE.code,
    STANDARD_ACCOUNTS.CHEQUES_ISSUED.code,
  ];
  const accounts = await resolveAccounts(client, accountCodes, metadata.companyId);

  const apAccount = accounts.get(STANDARD_ACCOUNTS.ACCOUNTS_PAYABLE.code)!;
  const issuedAccount = accounts.get(STANDARD_ACCOUNTS.CHEQUES_ISSUED.code)!;

  const lines: CreateJournalEntryData['lines'] = [
    {
      accountId: apAccount.id,
      description: `Issued cheque ${payload.chequeNumber}`,
      debit: payload.amount,
      credit: 0,
      partnerId: payload.supplierId,
    },
    {
      accountId: issuedAccount.id,
      description: `Outstanding cheque ${payload.chequeNumber}`,
      debit: 0,
      credit: payload.amount,
      partnerId: payload.supplierId,
    },
  ];

  const journalData: CreateJournalEntryData = {
    entryDate: new Date(),
    description: `Issued Cheque - ${payload.chequeNumber}`,
    descriptionEn: `Issued Cheque - ${payload.chequeNumber}`,
    referenceType: 'Cheque',
    referenceId: payload.chequeId,
    createdBy: metadata.userId,
    companyId: metadata.companyId,
    lines,
  };

  const journalEntry = await postAndFinalizeEntry(journalData, client, metadata.userId);

  logger.info(
    `ChequeEventHandler: journal entry ${journalEntry.entryNumber} created for issued cheque ` +
    `| Dr. AP: ${payload.amount} | Cr. Cheques Issued: ${payload.amount}`
  );

  return { entryId: journalEntry.id, entryNumber: journalEntry.entryNumber };
}

/**
 * Handle the cheque.deposited event (received cheques only)
 *
 * Dr Bank / Cr Cheques on Hand.
 */
export async function handleChequeDeposited(
  event: BaseEvent<{ chequeId: number; chequeNumber: string; amount: number; bankId?: number; bankName?: string }>,
  client: PoolClient
): Promise<{ entryId: number; entryNumber: string }> {
  const { payload, metadata } = event;

  logger.info(
    `ChequeEventHandler: processing cheque.deposited ${payload.chequeNumber} ` +
    `(id: ${payload.chequeId}, amount: ${payload.amount})`
  );

  const accountCodes = [
    STANDARD_ACCOUNTS.BANK.code,
    STANDARD_ACCOUNTS.CHEQUES_ON_HAND.code,
  ];
  const accounts = await resolveAccounts(client, accountCodes, metadata.companyId);

  const bankAccount = accounts.get(STANDARD_ACCOUNTS.BANK.code)!;
  const onHandAccount = accounts.get(STANDARD_ACCOUNTS.CHEQUES_ON_HAND.code)!;

  const lines: CreateJournalEntryData['lines'] = [
    {
      accountId: bankAccount.id,
      description: `Deposited cheque ${payload.chequeNumber} to bank`,
      debit: payload.amount,
      credit: 0,
    },
    {
      accountId: onHandAccount.id,
      description: `Cheque ${payload.chequeNumber} no longer on hand`,
      debit: 0,
      credit: payload.amount,
    },
  ];

  const journalData: CreateJournalEntryData = {
    entryDate: new Date(),
    description: `Deposited Cheque - ${payload.chequeNumber}`,
    descriptionEn: `Deposited Cheque - ${payload.chequeNumber}`,
    referenceType: 'ChequeDeposit',
    referenceId: payload.chequeId,
    createdBy: metadata.userId,
    companyId: metadata.companyId,
    lines,
  };

  const journalEntry = await postAndFinalizeEntry(journalData, client, metadata.userId);

  logger.info(
    `ChequeEventHandler: journal entry ${journalEntry.entryNumber} created for deposited cheque ` +
    `| Dr. Bank: ${payload.amount} | Cr. Cheques on Hand: ${payload.amount}`
  );

  return { entryId: journalEntry.id, entryNumber: journalEntry.entryNumber };
}

/**
 * Handle the cheque.cleared event (issued cheques only)
 *
 * Dr Cheques Issued / Cr Bank.
 */
export async function handleChequeCleared(
  event: BaseEvent<{ chequeId: number; chequeNumber: string; amount: number; chequeType: string }>,
  client: PoolClient
): Promise<{ entryId: number; entryNumber: string } | undefined> {
  const { payload, metadata } = event;

  if (payload.chequeType !== 'issued') {
    logger.info(
      `ChequeEventHandler: cheque.cleared for ${payload.chequeType} cheque ${payload.chequeNumber} - no ledger effect`
    );
    return undefined;
  }

  logger.info(
    `ChequeEventHandler: processing cheque.cleared ${payload.chequeNumber} ` +
    `(id: ${payload.chequeId}, amount: ${payload.amount})`
  );

  const accountCodes = [
    STANDARD_ACCOUNTS.CHEQUES_ISSUED.code,
    STANDARD_ACCOUNTS.BANK.code,
  ];
  const accounts = await resolveAccounts(client, accountCodes, metadata.companyId);

  const issuedAccount = accounts.get(STANDARD_ACCOUNTS.CHEQUES_ISSUED.code)!;
  const bankAccount = accounts.get(STANDARD_ACCOUNTS.BANK.code)!;

  const lines: CreateJournalEntryData['lines'] = [
    {
      accountId: issuedAccount.id,
      description: `Cleared cheque ${payload.chequeNumber} - outstanding liability settled`,
      debit: payload.amount,
      credit: 0,
    },
    {
      accountId: bankAccount.id,
      description: `Cleared cheque ${payload.chequeNumber} debited from bank`,
      debit: 0,
      credit: payload.amount,
    },
  ];

  const journalData: CreateJournalEntryData = {
    entryDate: new Date(),
    description: `Cleared Cheque - ${payload.chequeNumber}`,
    descriptionEn: `Cleared Cheque - ${payload.chequeNumber}`,
    referenceType: 'ChequeClear',
    referenceId: payload.chequeId,
    createdBy: metadata.userId,
    companyId: metadata.companyId,
    lines,
  };

  const journalEntry = await postAndFinalizeEntry(journalData, client, metadata.userId);

  logger.info(
    `ChequeEventHandler: journal entry ${journalEntry.entryNumber} created for cleared cheque ` +
    `| Dr. Cheques Issued: ${payload.amount} | Cr. Bank: ${payload.amount}`
  );

  return { entryId: journalEntry.id, entryNumber: journalEntry.entryNumber };
}

/**
 * Handle the cheque.returned event (bounced / returned / replaced)
 *
 * Correct accounting depends on what happened before the return:
 *
 *  - Received cheque DEPOSITED then bounced:
 *      The bank claws the money back, so the deposit is corrected by
 *        Dr. Accounts Receivable (1201)   amount   (customer owes us again)
 *        Cr. Bank (1121)                  amount   (bank returned the funds)
 *      A NEW entry is posted here; the deposit entry stays (audit trail of
 *      the money moving in and out of the bank). We do NOT void the deposit,
 *      which would credit Cheques on Hand for a worthless cheque and leave
 *      the customer's receivable cleared.
 *
 *  - Received cheque returned BEFORE deposit:
 *      The physical cheque is handed back to the customer, so the original
 *      received entry (Dr Cheques on Hand / Cr AR) is reversed:
 *        Dr. Accounts Receivable (1201) / Cr. Cheques on Hand (1205)
 *
 *  - Issued cheque returned (stopped / replaced / bounced):
 *      The original issued entry (Dr AP / Cr Cheques Issued) is reversed.
 */
export async function handleChequeReturned(
  event: BaseEvent<ChequeReturnedPayload>,
  client: PoolClient
): Promise<{ entryId: number; entryNumber: string } | undefined> {
  const { payload, metadata } = event;

  const isReceived = payload.chequeType === 'received';
  const wasDeposited =
    payload.preStatus === 'deposited' || payload.preStatus === 'under_collection';

  logger.info(
    `ChequeEventHandler: processing cheque.returned ${payload.chequeNumber} ` +
    `(id: ${payload.chequeId}, type: ${payload.chequeType}, preStatus: ${payload.preStatus}, ` +
    `original entry: ${payload.originalEntryId})`
  );

  // ── Case 1: received cheque bounced AFTER deposit ────────────────────────
  // Dr AR (reinstate the customer's debt) / Cr Bank (funds clawed back).
  if (isReceived && wasDeposited) {
    const accountCodes = [
      STANDARD_ACCOUNTS.ACCOUNTS_RECEIVABLE.code,
      STANDARD_ACCOUNTS.BANK.code,
    ];
    const accounts = await resolveAccounts(client, accountCodes, metadata.companyId);

    const lines: CreateJournalEntryData['lines'] = [
      {
        accountId: accounts.get(STANDARD_ACCOUNTS.ACCOUNTS_RECEIVABLE.code)!.id,
        description: `Bounced deposited cheque ${payload.chequeNumber} - receivable reinstated`,
        debit: payload.amount,
        credit: 0,
      },
      {
        accountId: accounts.get(STANDARD_ACCOUNTS.BANK.code)!.id,
        description: `Bounced deposited cheque ${payload.chequeNumber} - bank returned funds`,
        debit: 0,
        credit: payload.amount,
      },
    ];

    const journalData: CreateJournalEntryData = {
      entryDate: new Date(),
      description: `Returned (bounced) Cheque - ${payload.chequeNumber}`,
      descriptionEn: `Returned (bounced) Cheque - ${payload.chequeNumber}`,
      referenceType: 'ChequeReturn',
      referenceId: payload.chequeId,
      createdBy: metadata.userId,
      companyId: metadata.companyId,
      lines,
    };

    const journalEntry = await postAndFinalizeEntry(journalData, client, metadata.userId);

    logger.info(
      `ChequeEventHandler: bounced deposited cheque ${payload.chequeNumber} corrected ` +
      `| Dr. AR: ${payload.amount} | Cr. Bank: ${payload.amount}`
    );

    return { entryId: journalEntry.id, entryNumber: journalEntry.entryNumber };
  }

  // ── Case 2: reverse the original entry (pre-deposit return / issued) ────
  // Prefer a full reversal of the original entry (keeps a clean audit trail).
  if (payload.originalEntryId) {
    const reversingEntry = await voidJournalEntry(
      payload.originalEntryId,
      `Returned cheque ${payload.chequeNumber}: ${payload.reason || 'returned'}`,
      client,
      metadata.userId
    );
    return { entryId: reversingEntry.id, entryNumber: reversingEntry.entryNumber };
  }

  // ── Case 3: fallback (no original entry id) ──────────────────────────────
  // issued  -> Dr Cheques Issued / Cr AP   (reverse the issued posting)
  // received pre-deposit -> Dr AR / Cr Cheques on Hand
  const accountCodes = isReceived
    ? [STANDARD_ACCOUNTS.ACCOUNTS_RECEIVABLE.code, STANDARD_ACCOUNTS.CHEQUES_ON_HAND.code]
    : [STANDARD_ACCOUNTS.CHEQUES_ISSUED.code, STANDARD_ACCOUNTS.ACCOUNTS_PAYABLE.code];
  const accounts = await resolveAccounts(client, accountCodes, metadata.companyId);

  const debitAccount = isReceived
    ? accounts.get(STANDARD_ACCOUNTS.ACCOUNTS_RECEIVABLE.code)!
    : accounts.get(STANDARD_ACCOUNTS.CHEQUES_ISSUED.code)!;
  const creditAccount = isReceived
    ? accounts.get(STANDARD_ACCOUNTS.CHEQUES_ON_HAND.code)!
    : accounts.get(STANDARD_ACCOUNTS.ACCOUNTS_PAYABLE.code)!;

  const lines: CreateJournalEntryData['lines'] = [
    {
      accountId: debitAccount.id,
      description: `Returned cheque ${payload.chequeNumber} reversal`,
      debit: payload.amount,
      credit: 0,
    },
    {
      accountId: creditAccount.id,
      description: `Returned cheque ${payload.chequeNumber} reversal`,
      debit: 0,
      credit: payload.amount,
    },
  ];

  const journalData: CreateJournalEntryData = {
    entryDate: new Date(),
    description: `Returned Cheque - ${payload.chequeNumber}`,
    descriptionEn: `Returned Cheque - ${payload.chequeNumber}`,
    referenceType: 'ChequeReturn',
    referenceId: payload.chequeId,
    createdBy: metadata.userId,
    companyId: metadata.companyId,
    lines,
  };

  const journalEntry = await postAndFinalizeEntry(journalData, client, metadata.userId);

  logger.info(
    `ChequeEventHandler: reversing entry ${journalEntry.entryNumber} created for returned cheque `
  );

  return { entryId: journalEntry.id, entryNumber: journalEntry.entryNumber };
}