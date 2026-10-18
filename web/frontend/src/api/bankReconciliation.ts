import { get, post } from './client';

// Bank Reconciliation API
export async function getReconciliations(bankId?: number, status?: string) {
  const params: Record<string, any> = {};
  if (bankId) params.bank_id = bankId;
  if (status) params.status = status;
  return await get<any[]>('/bank-reconciliation/reconciliations', params);
}

export async function createReconciliation(data: any) {
  return await post<any>('/bank-reconciliation/reconciliations', data);
}

export async function getReconciliation(id: number) {
  return await get<any>(`/bank-reconciliation/reconciliations/${id}`);
}

export async function getUnmatchedTransactions(reconciliationId: number) {
  return await get<any[]>(`/bank-reconciliation/reconciliations/${reconciliationId}/unmatched`);
}

export async function matchTransaction(reconciliationId: number, data: any) {
  return await post<any>(`/bank-reconciliation/reconciliations/${reconciliationId}/match`, data);
}

export async function unmatchTransaction(reconciliationId: number, itemId: number) {
  return await post<any>(`/bank-reconciliation/reconciliations/${reconciliationId}/unmatch`, { item_id: itemId });
}

export async function completeReconciliation(reconciliationId: number) {
  return await post<any>(`/bank-reconciliation/reconciliations/${reconciliationId}/complete`);
}

export async function getUnreconciledTransactions(bankId: number) {
  return await get<any[]>('/bank-reconciliation/unreconciled-transactions', { bank_id: bankId });
}
