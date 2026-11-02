export interface User {
  id: string;
  username: string;
  email: string;
  fullName: string;
  role: string;
  roleId?: number | null;
  companyId: string;
  isActive: boolean;
  createdAt: string;
  permissions?: string[];
}

export interface FiscalYearOption {
  id: number;
  name: string;
  startDate: string;
  endDate: string;
  isClosed: boolean;
  isLocked: boolean;
}

export interface BranchOption {
  id: number;
  name: string;
  code: string;
  companyId: number;
}

export interface Branch {
  id: number;
  companyId: number;
  code: string;
  name: string;
  nameEn?: string;
  address?: string;
  phone?: string;
  email?: string;
  manager?: string;
  isActive: boolean;
}

export interface SettingOption {
  value: string;
  label: string;
}

export interface AppSetting {
  key: string;
  value: string;
  description: string;
  group: string;
  dataType?: string;
  options?: SettingOption[] | null;
  isVisible?: boolean;
  updatedAt: string;
}

export interface LoginContext {
  fiscalPeriods: FiscalYearOption[];
  branches: BranchOption[];
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
  id: number;
  code?: string | null;
  name: string;
  nameEn?: string | null;
  barcode?: string | null;
  categoryId?: number | null;
  categoryName?: string | null;
  unitId?: number | null;
  currencyId?: number | null;
  unit: string;
  purchasePrice: number;
  sellingPrice: number;
  lastPurchasePrice?: number | null;
  currentStock: number;
  minStock: number;
  maxStock: number;
  reorderPoint?: number;
  location?: string | null;
  valuationMethod?: string | null;
  weight?: number | null;
  taxPercent: number;
  brand?: string | null;
  description?: string | null;
  isActive?: boolean | null;
  companyId?: number | null;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface ProductInput {
  code: string;
  name: string;
  nameEn?: string;
  description?: string;
  categoryId?: number;
  unitId?: number;
  currencyId?: number;
  unit: string;
  purchasePrice: number;
  sellingPrice: number;
  currentStock?: number;
  minStock?: number;
  maxStock?: number;
  reorderPoint?: number;
  location?: string;
  valuationMethod?: string;
  weight?: number;
  taxPercent?: number;
  barcode?: string;
  brand?: string;
  companyId?: number;
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
  movementNumber?: string;
  movementType: 'in' | 'out' | 'adjustment';
  productId: string;
  productName?: string;
  warehouseId?: string;
  warehouseName?: string;
  quantity: number;
  unitCost?: number;
  referenceType?: string;
  referenceId?: string;
  notes?: string;
  createdBy?: string;
  createdAt: string;
}

export interface StockMovementInput {
  productId: number;
  movementType: 'in' | 'out' | 'adjustment';
  quantity: number;
  unitCost?: number;
  warehouseId?: number;
  notes?: string;
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
  saleId?: string;
  saleInvoiceNumber?: string;
  customerId?: string;
  customerName?: string;
  returnDate?: string;
  date?: string;
  totalAmount: number;
  taxAmount: number;
  finalAmount: number;
  status: string;
  reason?: string;
  refundMethod?: string;
  branchId?: number;
  companyId?: number;
  notes?: string;
  isRestocked?: boolean;
  items: SaleReturnItem[];
  createdAt: string;
}

export interface SaleReturnItem {
  id: string;
  productId?: string;
  productName?: string;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
  taxAmount: number;
  reason?: string;
}

export interface PurchaseReturn {
  id: string;
  returnNumber: string;
  purchaseId?: string;
  purchaseOrderNumber?: string;
  supplierId?: string;
  supplierName?: string;
  returnDate?: string;
  date?: string;
  totalAmount: number;
  taxAmount: number;
  finalAmount: number;
  status: string;
  reason?: string;
  refundMethod?: string;
  branchId?: number;
  companyId?: number;
  notes?: string;
  isRestocked?: boolean;
  items: PurchaseReturnItem[];
  createdAt: string;
}

export interface PurchaseReturnItem {
  id: string;
  productId?: string;
  productName?: string;
  quantity: number;
  unitCost: number;
  totalCost: number;
  taxAmount: number;
  reason?: string;
}

export interface QuotationItem {
  id?: string;
  productId?: string;
  productName?: string;
  quantity: number;
  unitPrice: number;
  discount?: number;
  taxPercent?: number;
  taxAmount?: number;
  totalPrice: number;
}

export interface Quotation {
  id: string;
  quotationNumber: string;
  customerId?: string;
  customerName?: string;
  quotationDate?: string;
  validUntil?: string;
  status: string;
  totalAmount: number;
  taxAmount: number;
  discount: number;
  finalAmount: number;
  currencyCode?: string;
  paymentTerms?: string;
  notes?: string;
  saleId?: string;
  branchId?: number;
  companyId?: number;
  items: QuotationItem[];
  createdAt?: string;
}

// Promotions Types
export interface Promotion {
  id: number;
  code?: string;
  name: string;
  description?: string;
  promoType: 'percentage' | 'fixed';
  discountValue: number;
  appliesTo: 'all' | 'category' | 'product';
  targetId?: number | null;
  targetName?: string;
  minPurchase: number;
  maxDiscount?: number | null;
  startDate?: string;
  endDate?: string;
  status: 'draft' | 'active' | 'paused' | 'scheduled' | 'expired';
  isActive: boolean;
  usageLimit?: number | null;
  usedCount: number;
  priority: number;
  companyId?: number;
  branchId?: number;
  createdAt?: string;
}

// Notifications Types
export interface AppNotification {
  id: number;
  userId?: number | null;
  title: string;
  message?: string;
  notificationType: string;
  link?: string;
  isRead: boolean;
  readAt?: string;
  companyId?: number;
  createdAt?: string;
}

export interface Purchase {
  id: string;
  orderNumber: string;
  invoiceNumber: string;
  supplierId: string;
  supplierName: string;
  date: string;
  dueDate: string;
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'VOIDED';
  workflowState: string;
  paymentStatus: string;
  journalEntryId?: number | null;
  items: PurchaseItem[];
  subtotal: number;
  taxAmount: number;
  discount: number;
  total: number;
  finalAmount: number;
  totalAmount: number;
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

export interface Account {
  id: number;
  code: string;
  name: string;
  nameEn?: string;
  nameAr?: string;
  type: 'ASSET' | 'LIABILITY' | 'EQUITY' | 'REVENUE' | 'EXPENSE';
  parentId?: number | null;
  isControl?: boolean;
  isActive?: boolean;
  balance?: number;
  cumulativeBalance?: number;
  openingBalance?: number;
  notes?: string;
  currencyId?: number | null;
  children?: Account[];
}

export interface AccountCreateData {
  account_code: string;
  account_name: string;
  account_name_en?: string;
  account_name_ar?: string;
  account_type: string;
  parent_id?: number | null;
  is_control?: boolean;
  currency_id?: number | null;
  opening_balance?: number;
  notes?: string;
}

export interface JournalEntry {
  id: string;
  entryNumber: string;
  entryDate: string;
  description: string;
  reference: string;
  referenceType?: string;
  referenceId?: number;
  fiscalPeriodId?: number;
  status: 'Draft' | 'Posted' | 'Voided';
  lines: JournalEntryLine[];
  totalDebit: number;
  totalCredit: number;
  createdBy: string;
  postedBy?: string;
  postedAt?: string;
  voidedBy?: string;
  voidedAt?: string;
  voidReason?: string;
  createdAt: string;
}

export interface JournalEntryLine {
  id: string;
  accountId: string;
  accountCode?: string;
  accountName?: string;
  debit: number;
  credit: number;
  description: string;
  costCenterId?: number;
  costCenterCode?: string;
  costCenterName?: string;
  partnerId?: number;
  projectId?: number;
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

export interface GLAccountInfo {
  id: number;
  code: string;
  name: string;
  nameEn?: string;
  type: string;
  openingBalance: number;
}

export interface GLTransaction {
  id: number;
  entryNumber: string;
  entryDate: string;
  description: string;
  reference?: string;
  partnerId?: number;
  projectId?: number;
  partnerName?: string;
  projectName?: string;
  debit: number;
  credit: number;
  runningBalance: number;
  status: string;
}

export interface GeneralLedgerResponse {
  account: GLAccountInfo;
  fromDate: string;
  toDate: string;
  openingBalanceForPeriod: number;
  closingBalance: number;
  totalDebit: number;
  totalCredit: number;
  page: number;
  perPage: number;
  total: number;
  pages: number;
  transactions: GLTransaction[];
}

export interface CostCenter {
  id: number;
  code: string;
  name: string;
  name_en?: string;
  parent_id?: number;
  is_active?: boolean;
  created_at?: string;
}

export interface RecurringJETemplate {
  id: number;
  name: string;
  name_en?: string;
  description?: string;
  frequency: string;
  next_run_date?: string;
  last_run_date?: string;
  is_active?: boolean;
  template_data?: string;
  created_at?: string;
  updated_at?: string;
}

export interface RecurringJEPreviewLine {
  account_id: number;
  description?: string;
  debit: number;
  credit: number;
  partner_id?: number;
  project_id?: number;
  currency_id?: number;
  currency_rate?: number;
}

export interface RecurringJEPreview {
  template_id: number;
  name: string;
  entry_number: string;
  entry_date: string;
  description: string;
  lines: RecurringJEPreviewLine[];
  total_debit: number;
  total_credit: number;
  balanced: boolean;
  next_run_date?: string;
}

export interface HREmployee {
  id: number;
  code: string;
  full_name: string;
  full_name_en?: string;
  email?: string;
  phone?: string;
  mobile?: string;
  address?: string;
  gender?: string;
  birth_date?: string;
  nationality?: string;
  marital_status?: string;
  department_id?: number;
  departmentName?: string;
  position_id?: number;
  positionName?: string;
  manager_id?: number;
  managerName?: string;
  hire_date?: string;
  employment_status?: string;
  salary_type?: string;
  basic_salary?: number;
  housing_allowance?: number;
  transportation_allowance?: number;
  other_allowances?: number;
  total_salary?: number;
  bank_name?: string;
  bank_account?: string;
  iban?: string;
  id_type?: string;
  id_number?: string;
  id_expiry?: string;
  passport_number?: string;
  passport_expiry?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  health_insurance_provider?: string;
  health_insurance_number?: string;
  notes?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface HRDepartment {
  id: number;
  code: string;
  name: string;
  name_en?: string;
  description?: string;
  manager_id?: number;
  managerName?: string;
  parent_id?: number | null;
  employeeCount: number;
  children?: HRDepartment[];
  is_active?: boolean;
  created_at?: string;
}

export interface HRPosition {
  id: number;
  code: string;
  name: string;
  nameEn?: string;
  departmentId?: number;
  description?: string;
  minSalary?: number;
  maxSalary?: number;
  isActive?: boolean;
  createdAt?: string;
}

export interface HRAttendance {
  id: number;
  employee_id: number;
  employee_name?: string;
  date: string;
  check_in?: string;
  check_out?: string;
  status?: string;
  notes?: string;
  created_at?: string;
}

export interface HRLeave {
  id: number;
  employee_id: number;
  employee_name?: string;
  leave_type: string;
  start_date: string;
  end_date: string;
  days_count: number;
  reason?: string;
  status?: string;
  approved_by?: number;
  created_at?: string;
}

export interface HRPayroll {
  id: number;
  employee_id: number;
  employee_name?: string;
  period: string;
  period_from: string;
  period_to: string;
  basic_salary: number;
  allowances?: number;
  total_allowances?: number;
  overtime: number;
  bonus?: number;
  deductions: number;
  advance_deduction?: number;
  net_salary: number;
  status: string;
  payment_date?: string;
  payment_method?: string;
  journal_entry_id?: number;
  created_at?: string;
}

export interface HRAdvance {
  id: number;
  employee_id: number;
  employee_name?: string;
  employee_code?: string;
  advance_type: string;
  amount: number;
  installments?: number;
  monthly_deduction?: number;
  request_date?: string;
  reason?: string;
  status?: string;
  approved_by?: number;
  payment_method?: string;
  payment_date?: string;
  journal_entry_id?: number;
  notes?: string;
  created_at?: string;
}

export interface HRShift {
  id: number;
  code: string;
  name: string;
  nameEn?: string;
  startTime: string;
  endTime: string;
  breakMinutes?: number;
  workingHours: number;
  isActive?: boolean;
  createdAt?: string;
}

export interface HRLeaveType {
  id: number;
  code: string;
  name: string;
  nameEn?: string;
  daysPerYear: number;
  isPaid: boolean;
  maxConsecutiveDays?: number;
  requiresApproval: boolean;
  isActive?: boolean;
  createdAt?: string;
}

export interface HRLeaveBalance {
  id: number;
  employeeId: number;
  employeeName?: string;
  leaveTypeId: number;
  leaveTypeName?: string;
  year: number;
  daysEntitled: number;
  daysUsed: number;
  daysRemaining: number;
  notes?: string;
}

export interface HROvertime {
  id: number;
  employeeId: number;
  employeeName?: string;
  date: string;
  hours: number;
  rateMultiplier: number;
  amount: number;
  reason?: string;
  status?: string;
  approvedBy?: number;
}

export interface HRBonus {
  id: number;
  employeeId: number;
  employeeName?: string;
  bonusType: string;
  amount: number;
  period?: string;
  description?: string;
  status?: string;
  approvedBy?: number;
}

export interface HRPerformanceReview {
  id: number;
  employeeId: number;
  employeeName?: string;
  reviewerId?: number;
  reviewerName?: string;
  reviewDate: string;
  reviewPeriod?: string;
  rating: number;
  overallRating?: number;
  goalsAchieved?: string;
  strengths?: string;
  improvements?: string;
  recommendations?: string;
  status?: string;
  nextReviewDate?: string;
}

export interface HRContract {
  id: number;
  employeeId: number;
  employeeName?: string;
  contractType?: string;
  startDate: string;
  endDate?: string;
  probationEndDate?: string;
  basicSalary: number;
  allowances: number;
  isActive?: boolean;
  status?: string;
  notes?: string;
}

export interface HRResignation {
  id: number;
  employeeId: number;
  employeeName?: string;
  resignDate: string;
  lastWorkingDay?: string;
  reason?: string;
  status?: string;
  approvedBy?: number;
  notes?: string;
}

export interface HRJobPosting {
  id: number;
  positionId?: number;
  title: string;
  departmentId?: number;
  departmentName?: string;
  description?: string;
  requirements?: string;
  vacancies: number;
  salaryMin?: number;
  salaryMax?: number;
  location?: string;
  employmentType?: string;
  status?: string;
  postedDate?: string;
  deadline?: string;
  candidatesCount?: number;
}

export interface HRCandidate {
  id: number;
  jobPostingId?: number;
  jobTitle?: string;
  name: string;
  email?: string;
  phone?: string;
  resumeText?: string;
  status?: string;
  appliedDate?: string;
  rating?: number;
  source?: string;
  notes?: string;
}

export interface HRTraining {
  id: number;
  employeeId: number;
  employeeName?: string;
  courseName: string;
  provider?: string;
  startDate: string;
  endDate?: string;
  cost?: number;
  certificate?: boolean;
  status?: string;
  notes?: string;
}

export interface HRDocument {
  id: number;
  employeeId: number;
  employeeName?: string;
  documentType?: string;
  title: string;
  fileName?: string;
  filePath?: string;
  issueDate?: string;
  expiryDate?: string;
  notes?: string;
}

export interface HRHoliday {
  id: number;
  name: string;
  date: string;
  isRecurring?: boolean;
  type?: string;
  isActive?: boolean;
}

export interface HRReportsSummary {
  activeEmployees: number;
  totalEmployees: number;
  departments: number;
  pendingLeaves: number;
  pendingOvertime: number;
  pendingResignations: number;
  openJobs: number;
  openCandidates: number;
  newCandidates: number;
  trainingPlanned: number;
  draftPayroll: number;
  approvedAdvances: number;
  payrollPaidTotal: number;
  employeesByDepartment: { department: string; count: number }[];
  employeesByGender: { gender: string; count: number }[];
  leaveSummary: { leaveType: string; count: number; days: number }[];
  genderDistribution: { label: string; value: number }[];
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
  defaultCurrency?: string;
  fiscalYearStart?: string;
  dateFormat?: string;
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
  totalReturns: number;
  netSales: number;
  salesByHour: { hour: number; amount: number }[];
  salesByMonth: { month: string; amount: number }[];
  recentSales: Sale[];
  paymentMethods: { name: string; value: number }[];
  topProducts: { name: string; quantity: number; amount: number }[];
  topCustomers: { name: string; amount: number }[];
  approvalPending: number;
  paidCount: number;
  unpaidCount: number;
  vsYesterday?: { sales: number; invoices: number; customers: number } | null;
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
  | 'MANAGE_CHEQUES'
  | 'VIEW_AGING_REPORTS'
  | 'MANAGE_INVENTORY'
  | 'VIEW_INVENTORY'
  | 'MANAGE_HR'
  | 'VIEW_HR'
  | 'MANAGE_CRM'
  | 'VIEW_CRM';

export type UserRole = 'admin' | 'accountant' | 'viewer' | 'manager';

export interface UserPermissions {
  role: UserRole;
  permissions: Permission[];
}

export interface PermissionItem {
  id: number;
  code: string;
  name: string;
  nameEn?: string;
  module?: string;
  description?: string;
}

export interface RoleItem {
  id: number;
  name: string;
  nameEn?: string;
  description?: string;
  isActive: boolean;
  createdAt?: string;
  permissions: PermissionItem[];
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
