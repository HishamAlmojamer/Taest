import { get } from './client';

export interface AnalyticsSummary {
  currency: string;
  revenueMonth: number;
  expensesMonth: number;
  netProfitMonth: number;
  revenueYear: number;
  expensesYear: number;
  netProfitYear: number;
  bankBalance: number;
  receivables: number;
  payables: number;
  pendingSales: number;
  pendingPurchases: number;
  asOf: string;
}

export interface CashFlowProjection {
  month: string;
  forecastIn: number;
  forecastOut: number;
  net: number;
  closingBalance: number;
  knownReceivables: number;
  knownPayables: number;
}

export interface CashFlowForecast {
  currency: string;
  startingBalance: number;
  averageMonthlyIn: number;
  averageMonthlyOut: number;
  projections: CashFlowProjection[];
}

export interface Anomaly {
  type: string | null;
  severity: string;
  entryId: number;
  entryNumber: string;
  entryDate: string;
  description: string;
  amount: number;
  reason: string | null;
}

export interface AnomalyResult {
  notes: string;
  anomalies: Anomaly[];
}

export interface DuplicateGroup {
  entity: string;
  date: string | null;
  amount: number;
  method?: string | null;
  count: number;
  ids: number[];
}

export interface DuplicateResult {
  journalEntries: DuplicateGroup[];
  customerPayments: DuplicateGroup[];
}

export interface AccountSuggestion {
  id: number;
  code: string;
  name: string;
  nameEn: string | null;
  nameAr: string | null;
  type: string;
  score: number;
}

export interface ReconciliationSuggestion {
  bankTransactionId: number;
  bank: number;
  amount: number;
  type: string;
  transactionDate: string | null;
  description: string | null;
  reference: string | null;
  suggested: {
    journalEntryId: number;
    entryNumber: string;
    entryDate: string;
    accountId: number;
  } | null;
}

export const getAnalyticsSummary = () => get<AnalyticsSummary>('/analytics/summary');
export const getCashFlowForecast = (months = 6) => get<CashFlowForecast>('/analytics/cash-flow-forecast', { months });
export const getAnomalies = (days = 90) => get<AnomalyResult>('/analytics/anomalies', { days });
export const getDuplicates = (days = 120) => get<DuplicateResult>('/analytics/duplicates', { days });
export const getAccountSuggestions = (text: string, type?: string, limit = 8) =>
  get<{ query: string; suggestions: AccountSuggestion[] }>('/analytics/account-suggestions', { text, type, limit });
export const getReconciliationSuggestions = (days = 60) =>
  get<{ suggestionCount: number; suggestions: ReconciliationSuggestion[] }>('/analytics/reconciliation-suggestions', { days });