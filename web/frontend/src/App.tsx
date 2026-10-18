import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { AppLayout } from '@/components/layout/AppLayout';
import { PageLoader as LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';

const LoginPage = lazy(() => import('@/pages/auth/LoginPage'));
const DashboardPage = lazy(() => import('@/pages/dashboard/DashboardPage'));
const SalesListPage = lazy(() => import('@/pages/sales/SalesListPage'));
const SaleFormPage = lazy(() => import('@/pages/sales/SaleFormPage'));
const SaleDetailPage = lazy(() => import('@/pages/sales/SaleDetailPage'));
const PurchasesListPage = lazy(() => import('@/pages/purchases/PurchasesListPage'));
const PurchaseFormPage = lazy(() => import('@/pages/purchases/PurchaseFormPage'));
const ProductsListPage = lazy(() => import('@/pages/inventory/ProductsListPage'));
const ProductFormPage = lazy(() => import('@/pages/inventory/ProductFormPage'));
const CategoriesPage = lazy(() => import('@/pages/inventory/CategoriesPage'));
const WarehousesPage = lazy(() => import('@/pages/inventory/WarehousesPage'));
const StockMovementsPage = lazy(() => import('@/pages/inventory/StockMovementsPage'));
const ChartOfAccountsPage = lazy(() => import('@/pages/accounting/ChartOfAccountsPage'));
const JournalEntriesPage = lazy(() => import('@/pages/accounting/JournalEntriesPage'));
const TrialBalancePage = lazy(() => import('@/pages/accounting/TrialBalancePage'));
const EmployeesPage = lazy(() => import('@/pages/hr/EmployeesPage'));
const DepartmentsPage = lazy(() => import('@/pages/hr/DepartmentsPage'));
const AttendancePage = lazy(() => import('@/pages/hr/AttendancePage'));
const LeavesPage = lazy(() => import('@/pages/hr/LeavesPage'));
const PayrollPage = lazy(() => import('@/pages/hr/PayrollPage'));
const CustomerPaymentsPage = lazy(() => import('@/pages/payments/CustomerPaymentsPage'));
const SupplierPaymentsPage = lazy(() => import('@/pages/payments/SupplierPaymentsPage'));
const BanksPage = lazy(() => import('@/pages/payments/BanksPage'));
const ProjectsListPage = lazy(() => import('@/pages/projects/ProjectsListPage'));
const ProjectDetailPage = lazy(() => import('@/pages/projects/ProjectDetailPage'));
const CustomersPage = lazy(() => import('@/pages/crm/CustomersPage'));
const SuppliersPage = lazy(() => import('@/pages/crm/SuppliersPage'));
const LeadsPage = lazy(() => import('@/pages/crm/LeadsPage'));
const UsersPage = lazy(() => import('@/pages/settings/UsersPage'));
const CompaniesPage = lazy(() => import('@/pages/settings/CompaniesPage'));
const WorkflowPage = lazy(() => import('@/pages/settings/WorkflowPage'));
const SalesReportPage = lazy(() => import('@/pages/reports/SalesReportPage'));
const PurchasesReportPage = lazy(() => import('@/pages/reports/PurchasesReportPage'));
const FinancialReportPage = lazy(() => import('@/pages/reports/FinancialReportPage'));
const FinancialStatementsPage = lazy(() => import('@/pages/accounting/FinancialStatementsPage'));
const FixedAssetsPage = lazy(() => import('@/pages/fixed-assets/FixedAssetsPage'));
const BudgetsPage = lazy(() => import('@/pages/budgets/BudgetsPage'));
const AgingReportsPage = lazy(() => import('@/pages/accounting/AgingReportsPage'));
const BankReconciliationPage = lazy(() => import('@/pages/banking/BankReconciliationPage'));
const AuditLogPage = lazy(() => import('@/pages/settings/AuditLogPage'));

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
          <Route path="purchases" element={<SuspenseWrapper><PurchasesListPage /></SuspenseWrapper>} />
          <Route path="purchases/new" element={<SuspenseWrapper><PurchaseFormPage /></SuspenseWrapper>} />
          <Route path="inventory/products" element={<SuspenseWrapper><ProductsListPage /></SuspenseWrapper>} />
          <Route path="inventory/products/new" element={<SuspenseWrapper><ProductFormPage /></SuspenseWrapper>} />
          <Route path="inventory/categories" element={<SuspenseWrapper><CategoriesPage /></SuspenseWrapper>} />
          <Route path="inventory/warehouses" element={<SuspenseWrapper><WarehousesPage /></SuspenseWrapper>} />
          <Route path="inventory/movements" element={<SuspenseWrapper><StockMovementsPage /></SuspenseWrapper>} />
          <Route path="accounting/accounts" element={<SuspenseWrapper><ChartOfAccountsPage /></SuspenseWrapper>} />
          <Route path="accounting/journal" element={<SuspenseWrapper><JournalEntriesPage /></SuspenseWrapper>} />
          <Route path="accounting/trial-balance" element={<SuspenseWrapper><TrialBalancePage /></SuspenseWrapper>} />
          <Route path="accounting/financial-statements" element={<SuspenseWrapper><FinancialStatementsPage /></SuspenseWrapper>} />
          <Route path="accounting/fixed-assets" element={<SuspenseWrapper><FixedAssetsPage /></SuspenseWrapper>} />
          <Route path="accounting/budgets" element={<SuspenseWrapper><BudgetsPage /></SuspenseWrapper>} />
          <Route path="accounting/aging-reports" element={<SuspenseWrapper><AgingReportsPage /></SuspenseWrapper>} />
          <Route path="hr/employees" element={<SuspenseWrapper><EmployeesPage /></SuspenseWrapper>} />
          <Route path="hr/departments" element={<SuspenseWrapper><DepartmentsPage /></SuspenseWrapper>} />
          <Route path="hr/attendance" element={<SuspenseWrapper><AttendancePage /></SuspenseWrapper>} />
          <Route path="hr/leaves" element={<SuspenseWrapper><LeavesPage /></SuspenseWrapper>} />
          <Route path="hr/payroll" element={<SuspenseWrapper><PayrollPage /></SuspenseWrapper>} />
          <Route path="payments/customers" element={<SuspenseWrapper><CustomerPaymentsPage /></SuspenseWrapper>} />
          <Route path="payments/suppliers" element={<SuspenseWrapper><SupplierPaymentsPage /></SuspenseWrapper>} />
          <Route path="payments/banks" element={<SuspenseWrapper><BanksPage /></SuspenseWrapper>} />
          <Route path="payments/bank-reconciliation" element={<SuspenseWrapper><BankReconciliationPage /></SuspenseWrapper>} />
          <Route path="projects" element={<SuspenseWrapper><ProjectsListPage /></SuspenseWrapper>} />
          <Route path="projects/:id" element={<SuspenseWrapper><ProjectDetailPage /></SuspenseWrapper>} />
          <Route path="crm/customers" element={<SuspenseWrapper><CustomersPage /></SuspenseWrapper>} />
          <Route path="crm/suppliers" element={<SuspenseWrapper><SuppliersPage /></SuspenseWrapper>} />
          <Route path="crm/leads" element={<SuspenseWrapper><LeadsPage /></SuspenseWrapper>} />
          <Route path="settings/users" element={<SuspenseWrapper><UsersPage /></SuspenseWrapper>} />
          <Route path="settings/companies" element={<SuspenseWrapper><CompaniesPage /></SuspenseWrapper>} />
          <Route path="settings/workflow" element={<SuspenseWrapper><WorkflowPage /></SuspenseWrapper>} />
          <Route path="settings/audit-log" element={<SuspenseWrapper><AuditLogPage /></SuspenseWrapper>} />
          <Route path="reports/sales" element={<SuspenseWrapper><SalesReportPage /></SuspenseWrapper>} />
          <Route path="reports/purchases" element={<SuspenseWrapper><PurchasesReportPage /></SuspenseWrapper>} />
          <Route path="reports/financial" element={<SuspenseWrapper><FinancialReportPage /></SuspenseWrapper>} />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </ErrorBoundary>
  );
}
