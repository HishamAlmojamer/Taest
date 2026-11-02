import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { AppLayout } from '@/components/layout/AppLayout';
import { PageLoader as LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { ProtectedByPermission } from '@/components/auth/ProtectedByPermission';

const LoginPage = lazy(() => import('@/pages/auth/LoginPage'));
const DashboardPage = lazy(() => import('@/pages/dashboard/DashboardPage'));
const SalesListPage = lazy(() => import('@/pages/sales/SalesListPage'));
const SaleFormPage = lazy(() => import('@/pages/sales/SaleFormPage'));
const SaleDetailPage = lazy(() => import('@/pages/sales/SaleDetailPage'));
const PosPage = lazy(() => import('@/pages/pos/PosPage'));
const PromotionsPage = lazy(() => import('@/pages/promotions/PromotionsPage'));
const NotificationsPage = lazy(() => import('@/pages/notifications/NotificationsPage'));
const ReturnsListPage = lazy(() => import('@/pages/returns/ReturnsListPage'));
const ReturnFormPage = lazy(() => import('@/pages/returns/ReturnFormPage'));
const ReturnDetailPage = lazy(() => import('@/pages/returns/ReturnDetailPage'));
const QuotationsListPage = lazy(() => import('@/pages/quotations/QuotationsListPage'));
const QuotationFormPage = lazy(() => import('@/pages/quotations/QuotationFormPage'));
const QuotationDetailPage = lazy(() => import('@/pages/quotations/QuotationDetailPage'));
const PurchasesListPage = lazy(() => import('@/pages/purchases/PurchasesListPage'));
const PurchaseFormPage = lazy(() => import('@/pages/purchases/PurchaseFormPage'));
const PurchaseDetailPage = lazy(() => import('@/pages/purchases/PurchaseDetailPage'));
const ProductsListPage = lazy(() => import('@/pages/inventory/ProductsListPage'));
const ProductFormPage = lazy(() => import('@/pages/inventory/ProductFormPage'));
const CategoriesPage = lazy(() => import('@/pages/inventory/CategoriesPage'));
const WarehousesPage = lazy(() => import('@/pages/inventory/WarehousesPage'));
const StockMovementsPage = lazy(() => import('@/pages/inventory/StockMovementsPage'));
const ChartOfAccountsPage = lazy(() => import('@/pages/accounting/ChartOfAccountsPage'));
const JournalEntriesPage = lazy(() => import('@/pages/accounting/JournalEntriesPage'));
const TrialBalancePage = lazy(() => import('@/pages/accounting/TrialBalancePage'));
const EmployeesPage = lazy(() => import('@/pages/hr/EmployeesPage'));
const EmployeeDetailPage = lazy(() => import('@/pages/hr/EmployeeDetailPage'));
const DepartmentsPage = lazy(() => import('@/pages/hr/DepartmentsPage'));
const AttendancePage = lazy(() => import('@/pages/hr/AttendancePage'));
const LeavesPage = lazy(() => import('@/pages/hr/LeavesPage'));
const PayrollPage = lazy(() => import('@/pages/hr/PayrollPage'));
const AdvancesPage = lazy(() => import('@/pages/hr/AdvancesPage'));
const PositionsPage = lazy(() => import('@/pages/hr/PositionsPage'));
const ShiftsPage = lazy(() => import('@/pages/hr/ShiftsPage'));
const LeaveTypesPage = lazy(() => import('@/pages/hr/LeaveTypesPage'));
const OvertimePage = lazy(() => import('@/pages/hr/OvertimePage'));
const SalaryAdjustmentsPage = lazy(() => import('@/pages/hr/SalaryAdjustmentsPage'));
const PerformanceReviewsPage = lazy(() => import('@/pages/hr/PerformanceReviewsPage'));
const ContractsPage = lazy(() => import('@/pages/hr/ContractsPage'));
const ResignationsPage = lazy(() => import('@/pages/hr/ResignationsPage'));
const RecruitmentPage = lazy(() => import('@/pages/hr/RecruitmentPage'));
const TrainingPage = lazy(() => import('@/pages/hr/TrainingPage'));
const DocumentsPage = lazy(() => import('@/pages/hr/DocumentsPage'));
const HolidaysPage = lazy(() => import('@/pages/hr/HolidaysPage'));
const HRDashboardPage = lazy(() => import('@/pages/hr/HRDashboardPage'));
const CustomerPaymentsPage = lazy(() => import('@/pages/payments/CustomerPaymentsPage'));
const SupplierPaymentsPage = lazy(() => import('@/pages/payments/SupplierPaymentsPage'));
const BanksPage = lazy(() => import('@/pages/payments/BanksPage'));
const BankDetailPage = lazy(() => import('@/pages/payments/BankDetailPage'));
const ProjectsListPage = lazy(() => import('@/pages/projects/ProjectsListPage'));
const ProjectDetailPage = lazy(() => import('@/pages/projects/ProjectDetailPage'));
const CustomersPage = lazy(() => import('@/pages/crm/CustomersPage'));
const SuppliersPage = lazy(() => import('@/pages/crm/SuppliersPage'));
const LeadsPage = lazy(() => import('@/pages/crm/LeadsPage'));
const CustomerDetailPage = lazy(() => import('@/pages/crm/CustomerDetailPage'));
const OpportunitiesPage = lazy(() => import('@/pages/crm/OpportunitiesPage'));
const FollowUpsPage = lazy(() => import('@/pages/crm/FollowUpsPage'));
const SegmentsPage = lazy(() => import('@/pages/crm/SegmentsPage'));
const CrmDashboardPage = lazy(() => import('@/pages/crm/CrmDashboardPage'));
const CrmTreePage = lazy(() => import('@/pages/crm/CrmTreePage'));
const LoyaltyPage = lazy(() => import('@/pages/crm/LoyaltyPage'));
const UsersPage = lazy(() => import('@/pages/settings/UsersPage'));
const CompaniesPage = lazy(() => import('@/pages/settings/CompaniesPage'));
const WorkflowPage = lazy(() => import('@/pages/settings/WorkflowPage'));
const GeneralSettingsPage = lazy(() => import('@/pages/settings/GeneralSettingsPage'));
const NumberingPage = lazy(() => import('@/pages/settings/NumberingPage'));
const BranchesPage = lazy(() => import('@/pages/settings/BranchesPage'));
const SalesReportPage = lazy(() => import('@/pages/reports/SalesReportPage'));
const PurchasesReportPage = lazy(() => import('@/pages/reports/PurchasesReportPage'));
const FinancialReportPage = lazy(() => import('@/pages/reports/FinancialReportPage'));
const FinancialStatementsPage = lazy(() => import('@/pages/accounting/FinancialStatementsPage'));
const FixedAssetsPage = lazy(() => import('@/pages/fixed-assets/FixedAssetsPage'));
const BudgetsPage = lazy(() => import('@/pages/budgets/BudgetsPage'));
const AgingReportsPage = lazy(() => import('@/pages/accounting/AgingReportsPage'));
const BankReconciliationPage = lazy(() => import('@/pages/banking/BankReconciliationPage'));
const ChequesPage = lazy(() => import('@/pages/cheques/ChequesPage'));
const FiscalPeriodsPage = lazy(() => import('@/pages/accounting/FiscalPeriodsPage'));
const GeneralLedgerPage = lazy(() => import('@/pages/accounting/GeneralLedgerPage'));
const CostCentersPage = lazy(() => import('@/pages/accounting/CostCentersPage'));
const RecurringJETemplatesPage = lazy(() => import('@/pages/accounting/RecurringJETemplatesPage'));
const VouchersPage = lazy(() => import('@/pages/accounting/VouchersPage'));
const DebtorsCreditorsPage = lazy(() => import('@/pages/accounting/DebtorsCreditorsPage'));
const CurrenciesPage = lazy(() => import('@/pages/settings/CurrenciesPage'));
const TaxRatesPage = lazy(() => import('@/pages/settings/TaxRatesPage'));
const AuditLogPage = lazy(() => import('@/pages/settings/AuditLogPage'));
const RolesPage = lazy(() => import('@/pages/settings/RolesPage'));
const AnalyticsPage = lazy(() => import('@/pages/analytics/AnalyticsPage'));

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function SuspenseWrapper({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingSpinner />}>{children}</Suspense>
    </ErrorBoundary>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/login" element={<SuspenseWrapper><LoginPage /></SuspenseWrapper>} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<SuspenseWrapper><DashboardPage /></SuspenseWrapper>} />
          <Route path="sales" element={<SuspenseWrapper><SalesListPage /></SuspenseWrapper>} />
          <Route path="sales/new" element={<SuspenseWrapper><SaleFormPage /></SuspenseWrapper>} />
          <Route path="sales/:id" element={<SuspenseWrapper><SaleDetailPage /></SuspenseWrapper>} />
          <Route path="pos" element={<SuspenseWrapper><PosPage /></SuspenseWrapper>} />
          <Route path="promotions" element={<SuspenseWrapper><PromotionsPage /></SuspenseWrapper>} />
          <Route path="notifications" element={<SuspenseWrapper><NotificationsPage /></SuspenseWrapper>} />
          <Route path="returns/sales" element={<SuspenseWrapper><ReturnsListPage type="sales" /></SuspenseWrapper>} />
          <Route path="returns/sales/new" element={<SuspenseWrapper><ReturnFormPage type="sales" /></SuspenseWrapper>} />
          <Route path="returns/sales/:id" element={<SuspenseWrapper><ReturnDetailPage type="sales" /></SuspenseWrapper>} />
          <Route path="returns/purchases" element={<SuspenseWrapper><ReturnsListPage type="purchase" /></SuspenseWrapper>} />
          <Route path="returns/purchases/new" element={<SuspenseWrapper><ReturnFormPage type="purchase" /></SuspenseWrapper>} />
          <Route path="returns/purchases/:id" element={<SuspenseWrapper><ReturnDetailPage type="purchase" /></SuspenseWrapper>} />
          <Route path="quotations" element={<SuspenseWrapper><QuotationsListPage /></SuspenseWrapper>} />
          <Route path="quotations/new" element={<SuspenseWrapper><QuotationFormPage /></SuspenseWrapper>} />
          <Route path="quotations/:id" element={<SuspenseWrapper><QuotationDetailPage /></SuspenseWrapper>} />
          <Route path="purchases" element={<SuspenseWrapper><PurchasesListPage /></SuspenseWrapper>} />
          <Route path="purchases/new" element={<SuspenseWrapper><PurchaseFormPage /></SuspenseWrapper>} />
          <Route path="purchases/:id" element={<SuspenseWrapper><PurchaseDetailPage /></SuspenseWrapper>} />
          <Route path="inventory/products" element={<SuspenseWrapper><ProductsListPage /></SuspenseWrapper>} />
          <Route path="inventory/products/new" element={<SuspenseWrapper><ProductFormPage /></SuspenseWrapper>} />
          <Route path="inventory/categories" element={<SuspenseWrapper><CategoriesPage /></SuspenseWrapper>} />
          <Route path="inventory/warehouses" element={<SuspenseWrapper><WarehousesPage /></SuspenseWrapper>} />
          <Route path="inventory/movements" element={<SuspenseWrapper><StockMovementsPage /></SuspenseWrapper>} />
          <Route path="accounting/accounts" element={<SuspenseWrapper><ChartOfAccountsPage /></SuspenseWrapper>} />
          <Route path="accounting/journal" element={<ProtectedByPermission permission="VIEW_JOURNAL"><SuspenseWrapper><JournalEntriesPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="accounting/trial-balance" element={<ProtectedByPermission permission="VIEW_JOURNAL"><SuspenseWrapper><TrialBalancePage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="accounting/financial-statements" element={<ProtectedByPermission permission="VIEW_REPORTS"><SuspenseWrapper><FinancialStatementsPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="accounting/fixed-assets" element={<ProtectedByPermission permission="MANAGE_ASSETS"><SuspenseWrapper><FixedAssetsPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="accounting/budgets" element={<ProtectedByPermission permission="MANAGE_BUDGETS"><SuspenseWrapper><BudgetsPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="accounting/aging-reports" element={<SuspenseWrapper><AgingReportsPage /></SuspenseWrapper>} />
          <Route path="accounting/periods" element={<SuspenseWrapper><FiscalPeriodsPage /></SuspenseWrapper>} />
          <Route path="accounting/general-ledger" element={<ProtectedByPermission permission="VIEW_JOURNAL"><SuspenseWrapper><GeneralLedgerPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="accounting/cost-centers" element={<ProtectedByPermission permission="VIEW_JOURNAL"><SuspenseWrapper><CostCentersPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="accounting/recurring-je" element={<ProtectedByPermission permission="VIEW_JOURNAL"><SuspenseWrapper><RecurringJETemplatesPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="accounting/vouchers" element={<ProtectedByPermission permission="VIEW_JOURNAL"><SuspenseWrapper><VouchersPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="accounting/debtors-creditors" element={<ProtectedByPermission permission="VIEW_REPORTS"><SuspenseWrapper><DebtorsCreditorsPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="settings/currencies" element={<SuspenseWrapper><CurrenciesPage /></SuspenseWrapper>} />
          <Route path="settings/tax-rates" element={<SuspenseWrapper><TaxRatesPage /></SuspenseWrapper>} />
          <Route path="hr/employees/:id" element={<SuspenseWrapper><EmployeeDetailPage /></SuspenseWrapper>} />
          <Route path="hr/employees" element={<SuspenseWrapper><EmployeesPage /></SuspenseWrapper>} />
          <Route path="hr/departments" element={<SuspenseWrapper><DepartmentsPage /></SuspenseWrapper>} />
          <Route path="hr/attendance" element={<SuspenseWrapper><AttendancePage /></SuspenseWrapper>} />
          <Route path="hr/leaves" element={<SuspenseWrapper><LeavesPage /></SuspenseWrapper>} />
          <Route path="hr/payroll" element={<SuspenseWrapper><PayrollPage /></SuspenseWrapper>} />
          <Route path="hr/advances" element={<SuspenseWrapper><AdvancesPage /></SuspenseWrapper>} />
          <Route path="hr/positions" element={<SuspenseWrapper><PositionsPage /></SuspenseWrapper>} />
          <Route path="hr/shifts" element={<SuspenseWrapper><ShiftsPage /></SuspenseWrapper>} />
          <Route path="hr/leave-types" element={<SuspenseWrapper><LeaveTypesPage /></SuspenseWrapper>} />
          <Route path="hr/overtime" element={<SuspenseWrapper><OvertimePage /></SuspenseWrapper>} />
          <Route path="hr/salary-adjustments" element={<SuspenseWrapper><SalaryAdjustmentsPage /></SuspenseWrapper>} />
          <Route path="hr/performance-reviews" element={<SuspenseWrapper><PerformanceReviewsPage /></SuspenseWrapper>} />
          <Route path="hr/contracts" element={<SuspenseWrapper><ContractsPage /></SuspenseWrapper>} />
          <Route path="hr/resignations" element={<SuspenseWrapper><ResignationsPage /></SuspenseWrapper>} />
          <Route path="hr/recruitment" element={<SuspenseWrapper><RecruitmentPage /></SuspenseWrapper>} />
          <Route path="hr/training" element={<SuspenseWrapper><TrainingPage /></SuspenseWrapper>} />
          <Route path="hr/documents" element={<SuspenseWrapper><DocumentsPage /></SuspenseWrapper>} />
          <Route path="hr/holidays" element={<SuspenseWrapper><HolidaysPage /></SuspenseWrapper>} />
          <Route path="hr/dashboard" element={<SuspenseWrapper><HRDashboardPage /></SuspenseWrapper>} />
          <Route path="payments/customers" element={<SuspenseWrapper><CustomerPaymentsPage /></SuspenseWrapper>} />
          <Route path="payments/suppliers" element={<SuspenseWrapper><SupplierPaymentsPage /></SuspenseWrapper>} />
          <Route path="payments/banks" element={<SuspenseWrapper><BanksPage /></SuspenseWrapper>} />
          <Route path="payments/banks/:id" element={<SuspenseWrapper><BankDetailPage /></SuspenseWrapper>} />
          <Route path="payments/bank-reconciliation" element={<ProtectedByPermission permission="RECONCILE_BANK"><SuspenseWrapper><BankReconciliationPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="payments/cheques" element={<ProtectedByPermission permission="MANAGE_CHEQUES"><SuspenseWrapper><ChequesPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="projects" element={<SuspenseWrapper><ProjectsListPage /></SuspenseWrapper>} />
          <Route path="projects/:id" element={<SuspenseWrapper><ProjectDetailPage /></SuspenseWrapper>} />
          <Route path="crm/customers" element={<SuspenseWrapper><CustomersPage /></SuspenseWrapper>} />
          <Route path="crm/customers/:id" element={<SuspenseWrapper><CustomerDetailPage /></SuspenseWrapper>} />
          <Route path="crm/suppliers" element={<SuspenseWrapper><SuppliersPage /></SuspenseWrapper>} />
          <Route path="crm/leads" element={<SuspenseWrapper><LeadsPage /></SuspenseWrapper>} />
          <Route path="crm/opportunities" element={<SuspenseWrapper><OpportunitiesPage /></SuspenseWrapper>} />
          <Route path="crm/follow-ups" element={<SuspenseWrapper><FollowUpsPage /></SuspenseWrapper>} />
          <Route path="crm/loyalty" element={<SuspenseWrapper><LoyaltyPage /></SuspenseWrapper>} />
          <Route path="crm/segments" element={<SuspenseWrapper><SegmentsPage /></SuspenseWrapper>} />
          <Route path="crm/dashboard" element={<SuspenseWrapper><CrmDashboardPage /></SuspenseWrapper>} />
          <Route path="crm/tree" element={<SuspenseWrapper><CrmTreePage /></SuspenseWrapper>} />
          <Route path="settings/users" element={<ProtectedByPermission permission="MANAGE_USERS"><SuspenseWrapper><UsersPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="settings/companies" element={<ProtectedByPermission permission="MANAGE_SETTINGS"><SuspenseWrapper><CompaniesPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="settings/general" element={<ProtectedByPermission permission="MANAGE_SETTINGS"><SuspenseWrapper><GeneralSettingsPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="settings/numbering" element={<ProtectedByPermission permission="MANAGE_SETTINGS"><SuspenseWrapper><NumberingPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="settings/branches" element={<ProtectedByPermission permission="MANAGE_SETTINGS"><SuspenseWrapper><BranchesPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="settings/workflow" element={<ProtectedByPermission permission="MANAGE_SETTINGS"><SuspenseWrapper><WorkflowPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="settings/audit-log" element={<ProtectedByPermission permission="MANAGE_SETTINGS"><SuspenseWrapper><AuditLogPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="settings/roles" element={<ProtectedByPermission permission="MANAGE_USERS"><SuspenseWrapper><RolesPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="reports/sales" element={<ProtectedByPermission permission="VIEW_REPORTS"><SuspenseWrapper><SalesReportPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="reports/purchases" element={<ProtectedByPermission permission="VIEW_REPORTS"><SuspenseWrapper><PurchasesReportPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="reports/financial" element={<ProtectedByPermission permission="VIEW_REPORTS"><SuspenseWrapper><FinancialReportPage /></SuspenseWrapper></ProtectedByPermission>} />
          <Route path="analytics" element={<SuspenseWrapper><AnalyticsPage /></SuspenseWrapper>} />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </ErrorBoundary>
  );
}
