export interface User {
  id: string;
  username: string;
  email: string;
  fullName: string;
  role: string;
  companyId: string;
  isActive: boolean;
  createdAt: string;
}

export interface Customer {
  id: string;
  name: string;
  nameAr: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  country: string;
  taxNumber: string;
  creditLimit: number;
  balance: number;
  isActive: boolean;
  createdAt: string;
}

export interface Supplier {
  id: string;
  name: string;
  nameAr: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  country: string;
  taxNumber: string;
  paymentTerms: number;
  balance: number;
  isActive: boolean;
  createdAt: string;
}

export interface Product {
  id: string;
  sku: string;
  name: string;
  nameAr: string;
  description: string;
  categoryId: string;
  categoryName: string;
  unit: string;
  costPrice: number;
  sellingPrice: number;
  taxRate: number;
  minStock: number;
  maxStock: number;
  currentStock: number;
  warehouseId: string;
  warehouseName: string;
  isActive: boolean;
  createdAt: string;
}

export interface Category {
  id: string;
  name: string;
  nameAr: string;
  description: string;
  parentId: string | null;
  children?: Category[];
  productCount: number;
  createdAt: string;
}

export interface Warehouse {
  id: string;
  name: string;
  nameAr: string;
  address: string;
  manager: string;
  phone: string;
  isActive: boolean;
  productCount: number;
  createdAt: string;
}

export interface StockMovement {
  id: string;
  type: 'IN' | 'OUT' | 'TRANSFER' | 'ADJUSTMENT';
  productId: string;
  productName: string;
  warehouseId: string;
  warehouseName: string;
  toWarehouseId?: string;
  toWarehouseName?: string;
  quantity: number;
  unitCost: number;
  reference: string;
  notes: string;
  createdBy: string;
  createdAt: string;
}

export interface Sale {
  id: string;
  invoiceNumber: string;
  customerId: string;
  customerName: string;
  date: string;
  dueDate: string;
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'PAID' | 'PARTIALLY_PAID';
  workflowState?: string;
  items: SaleItem[];
  subtotal: number;
  taxAmount: number;
  discount: number;
  total: number;
  finalAmount?: number;
  totalAmount?: number;
  paidAmount: number;
  notes: string;
  createdBy: string;
  approvedBy?: string;
  createdAt: string;
}

export interface SaleItem {
  id: string;
  productId: string;
  productName: string;
  quantity: number;
  unitPrice: number;
  discount: number;
  taxRate: number;
  taxAmount: number;
  total: number;
}

export interface SaleReturn {
  id: string;
  returnNumber: string;
  saleId: string;
  saleInvoiceNumber: string;
  customerId: string;
  customerName: string;
  date: string;
  status: string;
  items: SaleItem[];
  total: number;
  reason: string;
  createdAt: string;
}

export interface Purchase {
  id: string;
  orderNumber: string;
  supplierId: string;
  supplierName: string;
  date: string;
  dueDate: string;
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'RECEIVED' | 'PARTIALLY_RECEIVED';
  items: PurchaseItem[];
  subtotal: number;
  taxAmount: number;
  discount: number;
  total: number;
  paidAmount: number;
  notes: string;
  createdBy: string;
  createdAt: string;
}

export interface PurchaseItem {
  id: string;
  productId: string;
  productName: string;
  quantity: number;
  receivedQuantity: number;
  unitCost: number;
  discount: number;
  taxRate: number;
  taxAmount: number;
  total: number;
}

export interface PurchaseReturn {
  id: string;
  returnNumber: string;
  purchaseId: string;
  purchaseOrderNumber: string;
  supplierId: string;
  supplierName: string;
  date: string;
  status: string;
  items: PurchaseItem[];
  total: number;
  reason: string;
  createdAt: string;
}

export interface Account {
  id: string;
  code: string;
  name: string;
  nameAr: string;
  type: 'ASSET' | 'LIABILITY' | 'EQUITY' | 'REVENUE' | 'EXPENSE';
  parentId: string | null;
  children?: Account[];
  balance: number;
  isActive: boolean;
}

export interface JournalEntry {
  id: string;
  entryNumber: string;
  date: string;
  description: string;
  reference: string;
  status: 'DRAFT' | 'POSTED' | 'REVERSED';
  lines: JournalEntryLine[];
  totalDebit: number;
  totalCredit: number;
  createdBy: string;
  postedBy?: string;
  createdAt: string;
}

export interface JournalEntryLine {
  id: string;
  accountId: string;
  accountCode: string;
  accountName: string;
  debit: number;
  credit: number;
  description: string;
}

export interface TrialBalanceAccount {
  accountId: number;
  accountCode: string;
  accountName: string;
  accountType: string;
  debit: number;
  credit: number;
  openingBalance: number;
  netBalance: number;
}

export interface TrialBalanceResponse {
  totalDebit: number;
  totalCredit: number;
  isBalanced: boolean;
  accounts: TrialBalanceAccount[];
}

export interface HREmployee {
  id: string;
  employeeNumber: string;
  firstName: string;
  lastName: string;
  firstNameAr: string;
  lastNameAr: string;
  email: string;
  phone: string;
  position: string;
  departmentId: string;
  departmentName: string;
  hireDate: string;
  salary: number;
  status: 'ACTIVE' | 'INACTIVE' | 'ON_LEAVE';
  address: string;
  nationalId: string;
  createdAt: string;
}

export interface HRDepartment {
  id: string;
  name: string;
  nameAr: string;
  managerId: string;
  managerName: string;
  employeeCount: number;
  parentId: string | null;
  createdAt: string;
}

export interface HRPosition {
  id: string;
  title: string;
  titleAr: string;
  departmentId: string;
  departmentName: string;
  minSalary: number;
  maxSalary: number;
  employeeCount: number;
}

export interface HRAttendance {
  id: string;
  employeeId: string;
  employeeName: string;
  date: string;
  clockIn: string;
  clockOut: string;
  status: 'PRESENT' | 'ABSENT' | 'LATE' | 'ON_LEAVE' | 'HALF_DAY';
  hoursWorked: number;
  overtime: number;
  notes: string;
}

export interface HRLeave {
  id: string;
  employeeId: string;
  employeeName: string;
  type: 'ANNUAL' | 'SICK' | 'PERSONAL' | 'MATERNITY' | 'PATERNITY' | 'UNPAID';
  startDate: string;
  endDate: string;
  days: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  reason: string;
  approvedBy?: string;
  createdAt: string;
}

export interface HRPayroll {
  id: string;
  period: string;
  employeeId: string;
  employeeName: string;
  basicSalary: number;
  allowances: number;
  deductions: number;
  overtime: number;
  netSalary: number;
  status: 'DRAFT' | 'PROCESSED' | 'PAID';
  paidDate?: string;
  createdAt: string;
}

export interface CustomerPayment {
  id: string;
  paymentNumber: string;
  customerId: string;
  customerName: string;
  saleId?: string;
  saleInvoiceNumber?: string;
  amount: number;
  method: 'CASH' | 'BANK_TRANSFER' | 'CHECK' | 'CREDIT_CARD';
  bankAccount?: string;
  checkNumber?: string;
  date: string;
  notes: string;
  createdAt: string;
}

export interface SupplierPayment {
  id: string;
  paymentNumber: string;
  supplierId: string;
  supplierName: string;
  purchaseId?: string;
  purchaseOrderNumber?: string;
  amount: number;
  method: 'CASH' | 'BANK_TRANSFER' | 'CHECK' | 'CREDIT_CARD';
  bankAccount?: string;
  checkNumber?: string;
  date: string;
  notes: string;
  createdAt: string;
}

export interface Bank {
  id: string;
  name: string;
  nameAr: string;
  accountNumber: string;
  iban: string;
  balance: number;
  currency: string;
  isActive: boolean;
  createdAt: string;
}

export interface BankTransaction {
  id: string;
  bankId: string;
  bankName: string;
  type: 'DEPOSIT' | 'WITHDRAWAL' | 'TRANSFER' | 'FEE';
  amount: number;
  balance: number;
  description: string;
  reference: string;
  date: string;
  createdAt: string;
}

export interface Project {
  id: string;
  name: string;
  nameAr: string;
  description: string;
  customerId: string;
  customerName: string;
  startDate: string;
  endDate: string;
  budget: number;
  spent: number;
  status: 'PLANNING' | 'IN_PROGRESS' | 'ON_HOLD' | 'COMPLETED' | 'CANCELLED';
  progress: number;
  managerId: string;
  managerName: string;
  tasks: ProjectTask[];
  milestones: ProjectMilestone[];
  createdAt: string;
}

export interface ProjectTask {
  id: string;
  projectId: string;
  title: string;
  description: string;
  assigneeId: string;
  assigneeName: string;
  status: 'TODO' | 'IN_PROGRESS' | 'REVIEW' | 'DONE';
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  dueDate: string;
  estimatedHours: number;
  actualHours: number;
  createdAt: string;
}

export interface ProjectMilestone {
  id: string;
  projectId: string;
  title: string;
  dueDate: string;
  status: 'PENDING' | 'ACHIEVED' | 'MISSED';
  amount: number;
}

export interface Lead {
  id: string;
  name: string;
  company: string;
  email: string;
  phone: string;
  source: string;
  status: 'NEW' | 'CONTACTED' | 'QUALIFIED' | 'PROPOSAL' | 'NEGOTIATION' | 'WON' | 'LOST';
  value: number;
  assignedTo: string;
  assignedToName: string;
  notes: string;
  followups: Followup[];
  createdAt: string;
}

export interface Followup {
  id: string;
  leadId: string;
  type: 'CALL' | 'EMAIL' | 'MEETING' | 'NOTE';
  description: string;
  date: string;
  nextFollowup?: string;
  createdBy: string;
  createdAt: string;
}

export interface Company {
  id: string;
  name: string;
  nameAr: string;
  taxNumber: string;
  commercialRegister: string;
  address: string;
  phone: string;
  email: string;
  website: string;
  logo: string;
}

export interface WorkflowRule {
  id: string;
  name: string;
  nameAr: string;
  module: string;
  action: string;
  condition: string;
  approverRole: string;
  isActive: boolean;
  createdAt: string;
}

export interface SalesReport {
  totalSales: number;
  totalReturns: number;
  netSales: number;
  salesByMonth: { month: string; amount: number }[];
  salesByCategory: { category: string; amount: number }[];
  topProducts: { name: string; quantity: number; amount: number }[];
  topCustomers: { name: string; amount: number }[];
}

export interface PurchasesReport {
  totalPurchases: number;
  totalReturns: number;
  netPurchases: number;
  purchasesByMonth: { month: string; amount: number }[];
  topSuppliers: { name: string; amount: number }[];
}

export interface FinancialReport {
  revenue: number;
  expenses: number;
  netIncome: number;
  assets: number;
  liabilities: number;
  equity: number;
  incomeByMonth: { month: string; revenue: number; expenses: number }[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  perPage: number;
  pages: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  accessToken: string;
  refreshToken: string;
  user: User;
}

export interface PaginationParams {
  page?: number;
  pageSize?: number;
  search?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  [key: string]: unknown;
}

export interface DailyReport {
  date: string;
  totalSales: number;
  totalInvoices: number;
  totalCustomers: number;
  salesByHour: { hour: number; amount: number }[];
  recentSales: Sale[];
}

// Fixed Assets Types
export interface AssetCategory {
  id: number;
  name: string;
  description: string;
  depreciation_method: 'STRAIGHT_LINE' | 'DECLINING_BALANCE';
  useful_life_months: number;
  salvage_value_percent: number;
  account_id: number;
}

export interface FixedAsset {
  id: number;
  code: string;
  name: string;
  category_id: number;
  category_name: string;
  purchase_date: string;
  purchase_cost: number;
  accumulated_depreciation: number;
  current_value: number;
  useful_life_months: number;
  salvage_value: number;
  depreciation_method: string;
  status: 'ACTIVE' | 'FULLY_DEPRECIATED' | 'DISPOSED';
  location: string;
  notes: string;
  account_id: number;
  depreciation_account_id: number;
  created_at: string;
}

export interface DepreciationEntry {
  id: number;
  asset_id: number;
  asset_name: string;
  depreciation_date: string;
  depreciation_amount: number;
  accumulated_depreciation: number;
  book_value: number;
  journal_entry_id: number;
}

// Budget Types
export interface GLBudget {
  id: number;
  account_id: number;
  account_code: string;
  account_name: string;
  fiscal_period_id: number;
  budget_amount: number;
  notes: string;
  approved_by: number;
  approved_at: string;
  status: 'DRAFT' | 'APPROVED';
  created_at: string;
}

export interface BudgetVsActual {
  budget_id: number;
  account_id: number;
  account_code: string;
  account_name: string;
  budget_amount: number;
  actual_amount: number;
  variance: number;
  variance_percent: number;
  is_over_budget: boolean;
}

export interface BudgetAlert {
  budget_id: number;
  account_id: number;
  account_code: string;
  account_name: string;
  budget_amount: number;
  actual_amount: number;
  usage_percent: number;
  remaining: number;
  severity: 'WARNING' | 'CRITICAL';
}

// Bank Reconciliation Types
export interface BankReconciliation {
  id: number;
  bank_id: number;
  bank_name: string;
  statement_date: string;
  bank_balance: number;
  book_balance: number;
  difference: number;
  status: 'DRAFT' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  notes: string;
  reconciled_by: number;
  reconciled_at: string;
  completed_at: string;
  items: BankReconciliationItem[];
  created_at: string;
}

export interface BankReconciliationItem {
  id: number;
  reconciliation_id: number;
  journal_entry_id: number;
  transaction_type: 'DEPOSIT' | 'WITHDRAWAL' | 'TRANSFER' | 'FEE';
  amount: number;
  transaction_date: string;
  description: string;
  reference: string;
  status: 'MATCHED' | 'UNMATCHED' | 'EXCLUDED';
}

// Aging Report Types
export interface AgingReport {
  total: number;
  current: number;
  days_31_60: number;
  days_61_90: number;
  over_90: number;
  customers?: AgingCustomer[];
  suppliers?: AgingSupplier[];
}

export interface AgingCustomer {
  customer_id: number;
  customer_name: string;
  total: number;
  current: number;
  days_31_60: number;
  days_61_90: number;
  over_90: number;
}

export interface AgingSupplier {
  supplier_id: number;
  supplier_name: string;
  total: number;
  current: number;
  days_31_60: number;
  days_61_90: number;
  over_90: number;
}

export interface CustomerStatement {
  customer_id: number;
  customer_name: string;
  opening_balance: number;
  closing_balance: number;
  total_debit: number;
  total_credit: number;
  transactions: StatementTransaction[];
}

export interface SupplierStatement {
  supplier_id: number;
  supplier_name: string;
  opening_balance: number;
  closing_balance: number;
  total_debit: number;
  total_credit: number;
  transactions: StatementTransaction[];
}

export interface StatementTransaction {
  date: string;
  reference: string;
  description: string;
  debit: number;
  credit: number;
  balance: number;
}

// Currency Types
export interface Currency {
  id: number;
  code: string;
  name: string;
  symbol: string;
  is_base: boolean;
  is_active: boolean;
}

export interface ExchangeRate {
  id: number;
  from_currency_id: number;
  to_currency_id: number;
  rate: number;
  effective_date: string;
  created_at: string;
}

// Tax Types
export interface TaxRate {
  id: number;
  name: string;
  rate: number;
  type: 'PERCENTAGE' | 'FIXED';
  is_inclusive: boolean;
  account_id: number;
  is_active: boolean;
  created_at: string;
}

// Period Closing Types
export interface FiscalPeriod {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
  status: 'OPEN' | 'CLOSED' | 'LOCKED';
  closed_by: number;
  closed_at: string;
  created_at: string;
}

// Permissions Types
export type Permission = 
  | 'CREATE_SALE'
  | 'EDIT_SALE'
  | 'DELETE_SALE'
  | 'APPROVE_SALE'
  | 'VIEW_SALE'
  | 'CREATE_PURCHASE'
  | 'EDIT_PURCHASE'
  | 'DELETE_PURCHASE'
  | 'APPROVE_PURCHASE'
  | 'VIEW_PURCHASE'
  | 'CREATE_JOURNAL'
  | 'EDIT_JOURNAL'
  | 'DELETE_JOURNAL'
  | 'POST_JOURNAL'
  | 'VIEW_JOURNAL'
  | 'VIEW_REPORTS'
  | 'MANAGE_USERS'
  | 'MANAGE_SETTINGS'
  | 'MANAGE_ASSETS'
  | 'MANAGE_BUDGETS'
  | 'RECONCILE_BANK'
  | 'VIEW_AGING_REPORTS';

export type UserRole = 'admin' | 'accountant' | 'viewer' | 'manager';

export interface UserPermissions {
  role: UserRole;
  permissions: Permission[];
}

// Audit Log Types
export interface AuditLog {
  id: number;
  user_id: number;
  user_name: string;
  action: string;
  entity_type: string;
  entity_id: number;
  old_value: any;
  new_value: any;
  ip_address: string;
  user_agent: string;
  created_at: string;
}
