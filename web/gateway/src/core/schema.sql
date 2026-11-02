-- =============================================================================
-- ERP Financial Ledger Schema
-- =============================================================================
--
-- This SQL schema defines the core financial tables with strict constraints
-- as required by the ERP_INSTRUCTIONS.md specification.
--
-- Key Design Principles:
--   1. NUMERIC(15,4) for ALL monetary values (never FLOAT/DOUBLE)
--   2. Strict Foreign Keys with ON DELETE behavior
--   3. CHECK constraints for data integrity
--   4. Unique constraints where business logic requires it
--   5. Proper indexes for query performance
--
-- Accounting Logic:
--   - chart_of_accounts: The chart of accounts (COA) defines all financial accounts
--   - journal_entries: Head records for double-entry journal transactions
--   - journal_items: Individual debit/credit lines (must balance per entry)
--   - Account balances are computed from journal_items (not stored redundantly)
--
-- =============================================================================

-- =============================================================================
-- SEQUENCES
-- =============================================================================
-- Sequence for generating unique journal entry numbers (JE-YYYY-NNNNNN)
CREATE SEQUENCE IF NOT EXISTS journal_entry_number_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

-- =============================================================================
-- CHART OF ACCOUNTS
-- =============================================================================
-- The foundation of the double-entry bookkeeping system.
-- Each account has a type that determines how debits/credits affect its balance.
--
-- Balance Rules:
--   Asset/Expense accounts: Balance = OpeningBalance + Debits - Credits
--   Liability/Equity/Revenue accounts: Balance = OpeningBalance + Credits - Debits
--
CREATE TABLE IF NOT EXISTS chart_of_accounts (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(20) NOT NULL,
    name            VARCHAR(200) NOT NULL,
    name_ar         VARCHAR(200),
    type            VARCHAR(20) NOT NULL CHECK (type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')),
    parent_id       INTEGER REFERENCES chart_of_accounts(id) ON DELETE SET NULL,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    opening_balance NUMERIC(15, 4) NOT NULL DEFAULT 0,
    currency_code   VARCHAR(10) NOT NULL DEFAULT 'SAR',
    company_id      INTEGER,
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint: account codes must be unique
    CONSTRAINT uq_account_code UNIQUE (code),

    -- Ensure opening balance is reasonable (not NaN, not Infinity)
    CONSTRAINT chk_opening_balance CHECK (opening_balance > -1000000000 AND opening_balance < 1000000000)
);

-- Indexes for chart_of_accounts
CREATE INDEX IF NOT EXISTS ix_coa_type ON chart_of_accounts(type);
CREATE INDEX IF NOT EXISTS ix_coa_parent ON chart_of_accounts(parent_id);
CREATE INDEX IF NOT EXISTS ix_coa_active ON chart_of_accounts(is_active);
CREATE INDEX IF NOT EXISTS ix_coa_company ON chart_of_accounts(company_id);

-- =============================================================================
-- JOURNAL ENTRIES (Header)
-- =============================================================================
-- Each journal entry represents a balanced financial transaction.
--
-- Status Lifecycle:
--   Draft → Posted → Voided (with reason)
--
-- Immutability Rule:
--   Once status = 'Posted', the entry and its lines CANNOT be modified.
--   Corrections must be done via reversing entries (status = 'Voided').
--
CREATE TABLE IF NOT EXISTS journal_entries (
    id                SERIAL PRIMARY KEY,
    entry_number      VARCHAR(50) NOT NULL,
    entry_date        DATE NOT NULL,
    reference_type    VARCHAR(100),
    reference_id      INTEGER,
    description       TEXT NOT NULL,
    description_en    TEXT,
    status            VARCHAR(20) NOT NULL DEFAULT 'Draft'
                      CHECK (status IN ('Draft', 'Posted', 'Voided')),
    created_by        INTEGER,
    approved_by       INTEGER,
    approved_at       TIMESTAMPTZ,
    voided_by         INTEGER,
    voided_at         TIMESTAMPTZ,
    void_reason       TEXT,
    company_id        INTEGER,
    workflow_state    VARCHAR(50),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint: entry numbers must be unique
    CONSTRAINT uq_entry_number UNIQUE (entry_number),

    -- Voided entries must have a reason
    CONSTRAINT chk_void_reason CHECK (
        (status = 'Voided' AND void_reason IS NOT NULL AND void_reason != '')
        OR status != 'Voided'
    ),

    -- Voided entries must have voided_by and voided_at
    CONSTRAINT chk_void_fields CHECK (
        (status = 'Voided' AND voided_by IS NOT NULL AND voided_at IS NOT NULL)
        OR status != 'Voided'
    )
);

-- Indexes for journal_entries
CREATE INDEX IF NOT EXISTS ix_je_status ON journal_entries(status);
CREATE INDEX IF NOT EXISTS ix_je_date ON journal_entries(entry_date);
CREATE INDEX IF NOT EXISTS ix_je_company ON journal_entries(company_id);
CREATE INDEX IF NOT EXISTS ix_je_reference ON journal_entries(reference_type, reference_id);

-- =============================================================================
-- JOURNAL ITEMS (Lines)
-- =============================================================================
-- Each journal item represents a single debit or credit line within a journal entry.
--
-- Constraints:
--   1. debit >= 0 AND credit >= 0 (no negative values)
--   2. Cannot have both debit > 0 AND credit > 0 on the same line
--   3. At least one of debit or credit must be > 0
--
-- These constraints enforce the fundamental rules of double-entry bookkeeping.
--
CREATE TABLE IF NOT EXISTS journal_items (
    id                SERIAL PRIMARY KEY,
    journal_entry_id  INTEGER NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
    account_id        INTEGER NOT NULL REFERENCES chart_of_accounts(id) ON DELETE RESTRICT,
    description       TEXT,
    debit             NUMERIC(15, 4) NOT NULL DEFAULT 0 CHECK (debit >= 0),
    credit            NUMERIC(15, 4) NOT NULL DEFAULT 0 CHECK (credit >= 0),
    partner_id        INTEGER,
    cost_center_id    INTEGER,
    project_id        INTEGER,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure each line is either a debit or credit (not both, not neither)
    CONSTRAINT chk_debit_credit CHECK (
        (debit > 0 AND credit = 0) OR
        (credit > 0 AND debit = 0)
    ),

    -- Prevent negative amounts
    CONSTRAINT chk_no_negative CHECK (debit >= 0 AND credit >= 0)
);

-- Indexes for journal_items
CREATE INDEX IF NOT EXISTS ix_ji_entry ON journal_items(journal_entry_id);
CREATE INDEX IF NOT EXISTS ix_ji_account ON journal_items(account_id);
CREATE INDEX IF NOT EXISTS ix_ji_partner ON journal_items(partner_id);
CREATE INDEX IF NOT EXISTS ix_ji_cost_center ON journal_items(cost_center_id);
CREATE INDEX IF NOT EXISTS ix_ji_project ON journal_items(project_id);

-- =============================================================================
-- FISCAL PERIODS
-- =============================================================================
-- Defines accounting periods (monthly, quarterly, yearly).
-- Closed periods cannot have new journal entries posted to them.
--
CREATE TABLE IF NOT EXISTS fiscal_periods (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(200) NOT NULL,
    name_en       VARCHAR(200),
    start_date    DATE NOT NULL,
    end_date      DATE NOT NULL,
    is_closed     BOOLEAN NOT NULL DEFAULT false,
    is_locked     BOOLEAN NOT NULL DEFAULT false,
    closed_by     INTEGER,
    closed_at     TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure start_date is before end_date
    CONSTRAINT chk_period_dates CHECK (start_date < end_date),

    -- Ensure no overlapping periods for the same company
    -- (simplified: unique on date range)
    CONSTRAINT uq_fiscal_period UNIQUE (start_date, end_date)
);

-- =============================================================================
-- COST CENTERS
-- =============================================================================
-- For departmental/project-based accounting.
--
CREATE TABLE IF NOT EXISTS cost_centers (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(50) NOT NULL,
    name        VARCHAR(200) NOT NULL,
    name_en     VARCHAR(200),
    parent_id   INTEGER REFERENCES cost_centers(id) ON DELETE SET NULL,
    is_active   BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_cost_center_code UNIQUE (code)
);

-- =============================================================================
-- PARTNERS (Customers & Vendors unified)
-- =============================================================================
-- The ERP_INSTRUCTIONS.md specifies a unified partners table.
-- This is the sub-ledger for Accounts Receivable and Accounts Payable.
--
CREATE TABLE IF NOT EXISTS partners (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    name_ar         VARCHAR(200),
    type            VARCHAR(20) NOT NULL CHECK (type IN ('Customer', 'Vendor')),
    credit_limit    NUMERIC(15, 4) NOT NULL DEFAULT 0,
    balance         NUMERIC(15, 4) NOT NULL DEFAULT 0,
    currency_code   VARCHAR(10) NOT NULL DEFAULT 'SAR',
    email           VARCHAR(200),
    phone           VARCHAR(50),
    address         TEXT,
    tax_id          VARCHAR(100),
    is_active       BOOLEAN NOT NULL DEFAULT true,
    company_id      INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_partners_type ON partners(type);
CREATE INDEX IF NOT EXISTS ix_partners_company ON partners(company_id);

-- =============================================================================
-- INVOICES (Sub-ledger for Sales & Purchases)
-- =============================================================================
-- Unified invoice table for both customer sales and vendor purchases.
--
CREATE TABLE IF NOT EXISTS invoices (
    id              SERIAL PRIMARY KEY,
    invoice_number  VARCHAR(50) NOT NULL,
    partner_id      INTEGER NOT NULL REFERENCES partners(id) ON DELETE RESTRICT,
    invoice_type    VARCHAR(20) NOT NULL CHECK (invoice_type IN ('Customer', 'Vendor')),
    invoice_date    DATE NOT NULL,
    due_date        DATE,
    status          VARCHAR(20) NOT NULL DEFAULT 'Draft'
                    CHECK (status IN ('Draft', 'Submitted', 'Approved', 'Rejected', 'Paid', 'PartiallyPaid', 'Voided')),
    total_amount    NUMERIC(15, 4) NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    tax_amount      NUMERIC(15, 4) NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
    discount_amount NUMERIC(15, 4) NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
    final_amount    NUMERIC(15, 4) NOT NULL DEFAULT 0 CHECK (final_amount >= 0),
    paid_amount     NUMERIC(15, 4) NOT NULL DEFAULT 0 CHECK (paid_amount >= 0),
    currency_code   VARCHAR(10) NOT NULL DEFAULT 'SAR',
    journal_entry_id INTEGER REFERENCES journal_entries(id) ON DELETE SET NULL,
    created_by      INTEGER,
    approved_by     INTEGER,
    approved_at     TIMESTAMPTZ,
    notes           TEXT,
    company_id      INTEGER,
    branch_id       INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique invoice numbers
    CONSTRAINT uq_invoice_number UNIQUE (invoice_number),

    -- Ensure final_amount = total_amount + tax_amount - discount_amount
    CONSTRAINT chk_invoice_amounts CHECK (final_amount >= 0),

    -- Ensure paid_amount doesn't exceed final_amount
    CONSTRAINT chk_paid_amount CHECK (paid_amount <= final_amount)
);

CREATE INDEX IF NOT EXISTS ix_invoices_partner ON invoices(partner_id);
CREATE INDEX IF NOT EXISTS ix_invoices_type ON invoices(invoice_type);
CREATE INDEX IF NOT EXISTS ix_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS ix_invoices_date ON invoices(invoice_date);
CREATE INDEX IF NOT EXISTS ix_invoices_company ON invoices(company_id);

-- =============================================================================
-- STOCK MOVEMENTS (Inventory Transactions)
-- =============================================================================
-- Records all inventory movements (receipts, issues, transfers).
-- Table name matches Python backend's StockMovement model.
--
CREATE TABLE IF NOT EXISTS stock_movements (
    id                    SERIAL PRIMARY KEY,
    product_id            INTEGER NOT NULL,
    warehouse_id          INTEGER NOT NULL,
    quantity              INTEGER NOT NULL CHECK (quantity != 0),
    unit_cost             NUMERIC(15, 4) NOT NULL CHECK (unit_cost >= 0),
    total_cost            NUMERIC(15, 4) NOT NULL CHECK (total_cost >= 0),
    transaction_type      VARCHAR(20) NOT NULL CHECK (transaction_type IN ('Receipt', 'Issue', 'Transfer', 'Adjustment')),
    related_document_type VARCHAR(100),
    related_document_id   INTEGER,
    batch_number          VARCHAR(100),
    description           TEXT,
    journal_entry_id      INTEGER REFERENCES journal_entries(id) ON DELETE SET NULL,
    created_by            INTEGER,
    company_id            INTEGER,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_inv_txn_product ON stock_movements(product_id);
CREATE INDEX IF NOT EXISTS ix_inv_txn_warehouse ON stock_movements(warehouse_id);
CREATE INDEX IF NOT EXISTS ix_inv_txn_type ON stock_movements(transaction_type);
CREATE INDEX IF NOT EXISTS ix_inv_txn_date ON stock_movements(created_at);

-- =============================================================================
-- HR PAYROLL
-- =============================================================================
-- Records employee payroll with proper NUMERIC types for salary components.
-- Table name matches Python backend's HRPayroll model.
--
CREATE TABLE IF NOT EXISTS hr_payroll (
    id                        SERIAL PRIMARY KEY,
    employee_id               INTEGER NOT NULL,
    basic_salary              NUMERIC(15, 4) NOT NULL DEFAULT 0 CHECK (basic_salary >= 0),
    housing_allowance         NUMERIC(15, 4) NOT NULL DEFAULT 0 CHECK (housing_allowance >= 0),
    transportation_allowance  NUMERIC(15, 4) NOT NULL DEFAULT 0 CHECK (transportation_allowance >= 0),
    other_allowances          NUMERIC(15, 4) NOT NULL DEFAULT 0 CHECK (other_allowances >= 0),
    total_allowances          NUMERIC(15, 4) NOT NULL DEFAULT 0 CHECK (total_allowances >= 0),
    overtime                  NUMERIC(15, 4) NOT NULL DEFAULT 0 CHECK (overtime >= 0),
    bonus                     NUMERIC(15, 4) NOT NULL DEFAULT 0 CHECK (bonus >= 0),
    deductions                NUMERIC(15, 4) NOT NULL DEFAULT 0 CHECK (deductions >= 0),
    net_salary                NUMERIC(15, 4) NOT NULL DEFAULT 0,
    period_month              INTEGER NOT NULL CHECK (period_month BETWEEN 1 AND 12),
    period_year               INTEGER NOT NULL CHECK (period_year BETWEEN 2000 AND 2100),
    status                    VARCHAR(20) NOT NULL DEFAULT 'Draft'
                              CHECK (status IN ('Draft', 'Processed', 'Approved', 'Paid', 'Voided')),
    payment_date              DATE,
    journal_entry_id          INTEGER REFERENCES journal_entries(id) ON DELETE SET NULL,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique payroll per employee per period
    CONSTRAINT uq_payroll_period UNIQUE (employee_id, period_month, period_year)
);

CREATE INDEX IF NOT EXISTS ix_payroll_employee ON hr_payroll(employee_id);
CREATE INDEX IF NOT EXISTS ix_payroll_status ON hr_payroll(status);
CREATE INDEX IF NOT EXISTS ix_payroll_period ON hr_payroll(period_year, period_month);

-- =============================================================================
-- SEED DATA: Standard Chart of Accounts
-- =============================================================================
-- Pre-populate the standard chart of accounts for a Saudi ERP system.
-- These accounts are required for the event handlers to function.
--
-- NOTE: This uses ON CONFLICT to be idempotent (safe to run multiple times).
-- =============================================================================

INSERT INTO chart_of_accounts (code, name, name_ar, type, is_active, currency_code)
VALUES
    -- Assets (1xxx)
    ('1110', 'Cash', 'الصندوق', 'Asset', true, 'SAR'),
    ('1120', 'Bank Accounts', 'الحسابات البنكية', 'Asset', true, 'SAR'),
    ('1130', 'Accounts Receivable', 'المدينون', 'Asset', true, 'SAR'),
    ('1131', 'Employee Advances', 'سلف الموظفين', 'Asset', true, 'SAR'),
    ('1210', 'Inventory', 'المخزون', 'Asset', true, 'SAR'),
    ('1220', 'Prepaid Expenses', 'المصروفات المدفوعة مقدماً', 'Asset', true, 'SAR'),
    ('1230', 'Goods Received Not Invoiced', 'البضائع المستلمة غير المفوترة', 'Asset', true, 'SAR'),
    ('1240', 'VAT Input', 'ضريبة القيمة المضافة (مدفوعة)', 'Asset', true, 'SAR'),

    -- Liabilities (2xxx)
    ('2110', 'Accounts Payable', 'الدائنون', 'Liability', true, 'SAR'),
    ('2120', 'VAT Output', 'ضريبة القيمة المضافة (مستحقة)', 'Liability', true, 'SAR'),
    ('2130', 'Salaries Payable', 'الرواتب المستحقة', 'Liability', true, 'SAR'),
    ('2140', 'Accrued Expenses', 'المصروفات المستحقة', 'Liability', true, 'SAR'),

    -- Equity (3xxx)
    ('3100', 'Owner Equity', 'رأس المال', 'Equity', true, 'SAR'),
    ('3200', 'Retained Earnings', 'الأرباح المحتجزة', 'Equity', true, 'SAR'),

    -- Revenue (4xxx)
    ('4100', 'Sales Revenue', 'إيرادات المبيعات', 'Revenue', true, 'SAR'),
    ('4200', 'Sales Returns', 'مرتجعات المبيعات', 'Revenue', true, 'SAR'),
    ('4300', 'Other Income', 'إيرادات أخرى', 'Revenue', true, 'SAR'),

    -- Expenses (5xxx)
    ('5100', 'Cost of Goods Sold', 'تكلفة البضاعة المباعة', 'Expense', true, 'SAR'),
    ('5210', 'Salary Expense', 'مصاريف الرواتب', 'Expense', true, 'SAR'),
    ('5220', 'Bonus Expense', 'مصاريف المكافآت', 'Expense', true, 'SAR'),
    ('5230', 'Allowance Expense', 'مصاريف البدلات', 'Expense', true, 'SAR'),
    ('5310', 'Rent Expense', 'مصاريف الإيجار', 'Expense', true, 'SAR'),
    ('5320', 'Utilities Expense', 'مصاريف المرافق', 'Expense', true, 'SAR'),
    ('5400', 'Depreciation Expense', 'مصاريف الإهلاك', 'Expense', true, 'SAR'),
    ('5500', 'Other Expenses', 'مصاريف أخرى', 'Expense', true, 'SAR')
ON CONFLICT (code) DO NOTHING;

-- =============================================================================
-- TRIGGER: Auto-update updated_at timestamp
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables with updated_at
CREATE TRIGGER update_chart_of_accounts_updated_at
    BEFORE UPDATE ON chart_of_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_partners_updated_at
    BEFORE UPDATE ON partners
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_invoices_updated_at
    BEFORE UPDATE ON invoices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
