import os
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from app.config import settings
from app.database import engine, async_session_factory, Base
from app.services.bootstrap_data import seed_default_data
from app.routers import (
    auth, sales, purchases, inventory, accounting,
    hr, payments, projects, crm, reports,
    settings as settings_router,
    currencies, taxes, period_closing, financial_statements,
    fixed_assets, budgets, aging_reports, bank_reconciliation,
    audit,
    returns, quotations,
    promotions, notifications,
    excel, cheques, workflow, analytics,
    vouchers,
)

logger = logging.getLogger(__name__)

CORS_ORIGINS = settings.cors_origins


async def _bootstrap_admin() -> None:
    """Create the first administrator on a fresh database (idempotent).

    Only runs when BOOTSTRAP_ADMIN_USERNAME/PASSWORD are provided. Existing
    users are never modified, so it is safe to keep these env vars configured.
    """
    username = settings.BOOTSTRAP_ADMIN_USERNAME
    password = settings.BOOTSTRAP_ADMIN_PASSWORD
    if not username or not password:
        return

    from app.models.user import User
    from app.utils.security import hash_password

    async with async_session_factory() as session:
        existing = (
            await session.execute(select(User.id).where(User.username == username))
        ).scalar_one_or_none()
        if existing is not None:
            return
        role_id = (
            await session.execute(text("SELECT id FROM roles WHERE name = 'admin' LIMIT 1"))
        ).scalar_one_or_none()
        session.add(
            User(
                username=username,
                password=hash_password(password),
                full_name=settings.BOOTSTRAP_ADMIN_FULL_NAME,
                role="admin",
                role_id=role_id,
                is_active=True,
                created_at=datetime.now(UTC).replace(tzinfo=None),
            )
        )
        await session.commit()
        logger.warning("Bootstrapped admin user '%s'", username)


async def _warn_default_admin_password() -> None:
    if not settings.is_production:
        return
    from app.models.user import User
    from app.utils.security import verify_password

    async with async_session_factory() as session:
        admins = (
            await session.execute(select(User).where(User.role == "admin"))
        ).scalars().all()
    for admin in admins:
        if verify_password("admin123", admin.password):
            logger.critical(
                "SECURITY: admin user '%s' still uses the default password 'admin123'; change it now",
                admin.username,
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Additive migrations for existing databases (create_all does not alter tables)
        await conn.execute(text("ALTER TABLE sales ADD COLUMN IF NOT EXISTS fiscal_period_id INTEGER;"))
        await conn.execute(text("ALTER TABLE sales ADD COLUMN IF NOT EXISTS voided_by INTEGER;"))
        await conn.execute(text("ALTER TABLE sales ADD COLUMN IF NOT EXISTS voided_at TIMESTAMP;"))
        await conn.execute(text("ALTER TABLE sales ADD COLUMN IF NOT EXISTS void_reason TEXT;"))
        await conn.execute(text("ALTER TABLE purchases ADD COLUMN IF NOT EXISTS fiscal_period_id INTEGER;"))
        await conn.execute(text('ALTER TABLE fiscal_periods ADD COLUMN IF NOT EXISTS fiscal_year_id INTEGER;'))
        await conn.execute(text('ALTER TABLE fiscal_periods ADD COLUMN IF NOT EXISTS is_soft_closed BOOLEAN DEFAULT FALSE;'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_fiscal_periods_year ON fiscal_periods(fiscal_year_id);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_fiscal_periods_dates ON fiscal_periods(start_date, end_date);'))
        await conn.execute(text('ALTER TABLE app_settings ADD COLUMN IF NOT EXISTS data_type TEXT;'))
        await conn.execute(text('ALTER TABLE app_settings ADD COLUMN IF NOT EXISTS options TEXT;'))
        await conn.execute(text('ALTER TABLE app_settings ADD COLUMN IF NOT EXISTS is_visible BOOLEAN DEFAULT TRUE;'))
        await conn.execute(text('ALTER TABLE journal_entry_lines ADD COLUMN IF NOT EXISTS partner_id INTEGER;'))
        await conn.execute(text('ALTER TABLE journal_entry_lines ADD COLUMN IF NOT EXISTS project_id INTEGER;'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_jel_partner_id ON journal_entry_lines(partner_id);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_jel_project_id ON journal_entry_lines(project_id);'))
        # Additive migrations for the legacy notifications table (columns added by the new module)
        await conn.execute(text('ALTER TABLE notifications ADD COLUMN IF NOT EXISTS read_at TIMESTAMP;'))
        await conn.execute(text('ALTER TABLE notifications ADD COLUMN IF NOT EXISTS company_id INTEGER;'))
        await conn.execute(text('ALTER TABLE notifications ADD COLUMN IF NOT EXISTS created_by INTEGER;'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_notifications_created ON notifications(created_at);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_notifications_company ON notifications(company_id);'))
        await conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS currency_id INTEGER;"))
        await conn.execute(text("ALTER TABLE accounts ADD COLUMN IF NOT EXISTS account_name_ar VARCHAR(200);"))
        await conn.execute(text("ALTER TABLE accounts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;"))
        await conn.execute(text("ALTER TABLE accounts ADD COLUMN IF NOT EXISTS company_id INTEGER;"))
        await _run_crm_migrations(conn)
        await _ensure_rbac_columns(conn)
        await _seed_opportunity_stages(conn)
        await _seed_rbac(conn)
        await _seed_numbering(conn)
        await _run_cheques_migrations(conn)
        await seed_default_data(
            conn,
            settings.BOOTSTRAP_COMPANY_NAME,
            settings.BOOTSTRAP_BRANCH_NAME,
        )
    # The FK-constraint step is best-effort and MUST run in its own transaction:
    # a failed ALTER poison the asyncpg transaction and would otherwise roll
    # back all the additive migrations above (e.g. losing partner_id/project_id).
    try:
        async with engine.begin() as conn:
            await _add_fk_constraints(conn)
    except Exception as e:
        logger.warning("FK constraint step failed (non-fatal): %s", e)
    # Reset pool so asyncpg drops cached prepared statements
    # (migrations may have added columns to existing tables)
    await engine.dispose()
    logger.info("Database tables created/verified")

    await _bootstrap_admin()
    await _warn_default_admin_password()

    # Start the recurring journal entry scheduler unless disabled.
    # The scheduler is an optional background task: if it cannot be started
    # (e.g. a missing optional dependency), log a warning instead of crashing
    # the whole application on startup.
    scheduler_task = None
    if os.getenv("DISABLE_RECURRING_SCHEDULER", "0").lower() not in ("1", "true", "yes"):
        try:
            from app.services.recurring_scheduler import scheduler_loop
            scheduler_task = asyncio.create_task(scheduler_loop())
            logger.info("Recurring JE scheduler task started")
        except Exception as e:
            logger.warning("Recurring JE scheduler could not be started (continuing without it): %s", e)

    yield
    if scheduler_task is not None:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        logger.info("Recurring JE scheduler stopped")
    await engine.dispose()


async def _run_crm_migrations(conn):
    """Add CRM columns to pre-existing operational tables (idempotent)."""
    migrations = [
        # customers
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS name_ar VARCHAR(200);",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS mobile VARCHAR(50);",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS national_id TEXT;",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS website TEXT;",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS fax TEXT;",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS notes TEXT;",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'SAR';",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS price_list TEXT;",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS salesperson_id INTEGER;",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS segment_id INTEGER;",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS industry TEXT;",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS created_by INTEGER;",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS birthdate DATE;",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS gender VARCHAR(10);",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS city TEXT;",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS region TEXT;",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS country TEXT;",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS postal_code TEXT;",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS last_interaction_at TIMESTAMP;",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS parent_id INTEGER;",
        "CREATE INDEX IF NOT EXISTS ix_customers_segment_id ON customers(segment_id);",
        "CREATE INDEX IF NOT EXISTS ix_customers_parent_id ON customers(parent_id);",
        # suppliers
        "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS name_ar VARCHAR(200);",
        "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS tax_id TEXT;",
        "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS website TEXT;",
        "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS fax TEXT;",
        "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS notes TEXT;",
        "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'SAR';",
        "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS industry TEXT;",
        "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;",
        "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS payment_terms TEXT;",
        "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS bank_name TEXT;",
        "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS bank_account TEXT;",
        "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS iban TEXT;",
        "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS city TEXT;",
        "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS created_by INTEGER;",
        "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS parent_id INTEGER;",
        "CREATE INDEX IF NOT EXISTS ix_suppliers_parent_id ON suppliers(parent_id);",
        # leads
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS lead_score INTEGER DEFAULT 0;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS expected_close_date DATE;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS next_follow_up DATE;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS industry TEXT;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS city TEXT;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS tags TEXT;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS budget NUMERIC(15,4);",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS created_by INTEGER;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS converted_customer_id INTEGER;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS converted_opportunity_id INTEGER;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS converted_at TIMESTAMP;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS lost_reason TEXT;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS won_amount NUMERIC(15,4);",
    ]
    for statement in migrations:
        await conn.execute(text(statement))


async def _run_cheques_migrations(conn):
    """Create/verify the cheques table and its columns (idempotent)."""
    migrations = [
        """
        CREATE TABLE IF NOT EXISTS cheques (
            id SERIAL PRIMARY KEY,
            cheque_number VARCHAR(100) NOT NULL,
            cheque_type VARCHAR(20) NOT NULL,
            amount NUMERIC(15,4) NOT NULL,
            currency_code VARCHAR(10) DEFAULT 'SAR',
            exchange_rate NUMERIC(15,4) DEFAULT 1.0,
            payer_name TEXT,
            payee_name TEXT,
            customer_id INTEGER,
            supplier_id INTEGER,
            bank_id INTEGER,
            bank_name TEXT,
            bank_branch TEXT,
            issue_date TIMESTAMP,
            due_date TIMESTAMP,
            deposit_date TIMESTAMP,
            clear_date TIMESTAMP,
            status VARCHAR(30) DEFAULT 'on_hand',
            status_reason TEXT,
            replaced_by_cheque_id INTEGER,
            journal_entry_id INTEGER,
            reversal_entry_id INTEGER,
            reference_type VARCHAR(100),
            reference_id INTEGER,
            description TEXT,
            created_by INTEGER,
            updated_by INTEGER,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            company_id INTEGER
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_cheques_status ON cheques(status);",
        "CREATE INDEX IF NOT EXISTS ix_cheques_cheque_type ON cheques(cheque_type);",
        "CREATE INDEX IF NOT EXISTS ix_cheques_bank_id ON cheques(bank_id);",
        "CREATE INDEX IF NOT EXISTS ix_cheques_company_id ON cheques(company_id);",
    ]
    for statement in migrations:
        await conn.execute(text(statement))

    # Additive permission seed — the main _seed_rbac only runs once, so this
    # guarantees MANAGE_CHEQUES exists even on pre-seeded databases, and is
    # granted to admin + accountant roles.
    await conn.execute(text(
        """
        INSERT INTO permissions (code, name, name_en, module, display_name, category, is_active)
        SELECT 'MANAGE_CHEQUES', 'إدارة الشيكات', 'Manage Cheques', 'admin', 'Manage Cheques', 'admin', true
        WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE code = 'MANAGE_CHEQUES')
        """
    ))
    await conn.execute(text(
        """
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name IN ('admin', 'accountant')
          AND p.code = 'MANAGE_CHEQUES'
          AND NOT EXISTS (
              SELECT 1 FROM role_permissions rp WHERE rp.role_id = r.id AND rp.permission_id = p.id
          )
        """
    ))

    # Additive permissions for RBAC-gated modules not present in the original seed.
    rbac_extra = [
        ("MANAGE_PROJECTS", 'admin', 'accountant'),
        ("VIEW_PROJECTS", 'admin', 'accountant', 'viewer'),
        ("MANAGE_PROMOTIONS", 'admin', 'accountant'),
        ("CREATE_QUOTATION", 'admin', 'accountant', 'sales_rep'),
        ("EDIT_QUOTATION", 'admin', 'accountant', 'sales_rep'),
        ("DELETE_QUOTATION", 'admin'),
    ]
    for code, *roles in rbac_extra:
        await conn.execute(text(
            f"""
            INSERT INTO permissions (code, name, name_en, module, display_name, category, is_active)
            SELECT '{code}', '{code}', '{code}', 'rbac', '{code}', 'rbac', true
            WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE code = '{code}')
            """
        ))
        role_list = ", ".join(f"'{r}'" for r in roles)
        await conn.execute(text(
            f"""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r, permissions p
            WHERE r.name IN ({role_list})
              AND p.code = '{code}'
              AND NOT EXISTS (
                  SELECT 1 FROM role_permissions rp WHERE rp.role_id = r.id AND rp.permission_id = p.id
              )
            """
        ))

    # Cheque ledger accounts — the ledger engine (gateway) resolves Cheques on
    # Hand (1205) and Cheques Issued (2124) by code, so ensure they exist even
    # on pre-seeded databases (idempotent, additive — never wipes data).
    await conn.execute(text(
        """
        INSERT INTO accounts (account_code, account_name, account_name_en, account_name_ar, account_type, parent_id, is_control, is_active, opening_balance, created_at, updated_at)
        SELECT '1205', 'شيكات تحت التحصيل', 'Cheques on Hand', 'شيكات تحت التحصيل', 'asset', p.id, false, true, 0, NOW(), NOW()
        FROM accounts p
        WHERE p.account_code = '1200'
          AND NOT EXISTS (SELECT 1 FROM accounts WHERE account_code = '1205')
        """
    ))
    await conn.execute(text(
        """
        INSERT INTO accounts (account_code, account_name, account_name_en, account_name_ar, account_type, parent_id, is_control, is_active, opening_balance, created_at, updated_at)
        SELECT '2124', 'شيكات مسحوبة', 'Cheques Issued', 'شيكات مسحوبة', 'liability', p.id, false, true, 0, NOW(), NOW()
        FROM accounts p
        WHERE p.account_code = '2100'
          AND NOT EXISTS (SELECT 1 FROM accounts WHERE account_code = '2124')
        """
    ))


async def _seed_opportunity_stages(conn):
    """Seed a default sales pipeline if no stages exist."""
    result = await conn.execute(text("SELECT COUNT(*) AS n FROM opportunity_stages"))
    count = result.scalar() or 0
    if count > 0:
        return
    await conn.execute(text(
        """
        INSERT INTO opportunity_stages (name, name_ar, position, probability, is_won, is_lost, color)
        VALUES
          ('new', 'جديد', 1, 10, false, false, '#0ea5e9'),
          ('qualified', 'مؤهل', 2, 30, false, false, '#6366f1'),
          ('proposal', 'عرض سعر', 3, 50, false, false, '#f59e0b'),
          ('negotiation', 'تفاوض', 4, 75, false, false, '#f97316'),
          ('won', 'تم الفوز', 5, 100, true, false, '#10b981'),
          ('lost', 'خسارة', 6, 0, false, true, '#ef4444')
        """
    ))
    logger.info("Seeded default opportunity stages")


async def _seed_rbac(conn):
    """Seed default permissions and roles if none exist or data is corrupt."""
    result = await conn.execute(text("SELECT COUNT(*) AS n FROM permissions WHERE code IS NOT NULL"))
    count = result.scalar() or 0
    if count > 0:
        return

    # Clear stale data with NULL codes
    await conn.execute(text("DELETE FROM role_permissions"))
    await conn.execute(text("DELETE FROM permissions"))
    await conn.execute(text("DELETE FROM roles"))

    permissions_data = [
        # Sales
        ("CREATE_SALE", "إنشاء فواتير مبيعات", "Create Sales", "sales"),
        ("EDIT_SALE", "تعديل فواتير مبيعات", "Edit Sales", "sales"),
        ("DELETE_SALE", "حذف فواتير مبيعات", "Delete Sales", "sales"),
        ("APPROVE_SALE", "اعتماد فواتير مبيعات", "Approve Sales", "sales"),
        ("VIEW_SALE", "عرض فواتير مبيعات", "View Sales", "sales"),
        # Purchases
        ("CREATE_PURCHASE", "إنشاء أوامر شراء", "Create Purchases", "purchases"),
        ("EDIT_PURCHASE", "تعديل أوامر شراء", "Edit Purchases", "purchases"),
        ("DELETE_PURCHASE", "حذف أوامر شراء", "Delete Purchases", "purchases"),
        ("APPROVE_PURCHASE", "اعتماد أوامر شراء", "Approve Purchases", "purchases"),
        ("VIEW_PURCHASE", "عرض أوامر شراء", "View Purchases", "purchases"),
        # Accounting / Journal
        ("CREATE_JOURNAL", "إنشاء قيود يومية", "Create Journal Entries", "accounting"),
        ("EDIT_JOURNAL", "تعديل قيود يومية", "Edit Journal Entries", "accounting"),
        ("DELETE_JOURNAL", "حذف قيود يومية", "Delete Journal Entries", "accounting"),
        ("POST_JOURNAL", "ترحيل قيود يومية", "Post Journal Entries", "accounting"),
        ("VIEW_JOURNAL", "عرض القيود اليومية", "View Journal Entries", "accounting"),
        # Reports
        ("VIEW_REPORTS", "عرض التقارير", "View Reports", "reports"),
        # Admin
        ("MANAGE_USERS", "إدارة المستخدمين", "Manage Users", "admin"),
        ("MANAGE_SETTINGS", "إدارة الإعدادات", "Manage Settings", "admin"),
        ("MANAGE_ASSETS", "إدارة الأصول الثابتة", "Manage Fixed Assets", "admin"),
        ("MANAGE_BUDGETS", "إدارة الميزانيات", "Manage Budgets", "admin"),
        ("RECONCILE_BANK", "التسوية البنكية", "Bank Reconciliation", "admin"),
        ("MANAGE_CHEQUES", "إدارة الشيكات", "Manage Cheques", "admin"),
        ("VIEW_AGING_REPORTS", "عرض تقارير أعمار الذمم", "View Aging Reports", "reports"),
        # Inventory
        ("MANAGE_INVENTORY", "إدارة المخزون", "Manage Inventory", "inventory"),
        ("VIEW_INVENTORY", "عرض المخزون", "View Inventory", "inventory"),
        # HR
        ("MANAGE_HR", "إدارة الموارد البشرية", "Manage HR", "hr"),
        ("VIEW_HR", "عرض بيانات الموارد البشرية", "View HR", "hr"),
        # CRM
        ("MANAGE_CRM", "إدارة علاقات العملاء", "Manage CRM", "crm"),
        ("VIEW_CRM", "عرض علاقات العملاء", "View CRM", "crm"),
    ]

    for code, name, name_en, module in permissions_data:
        await conn.execute(text(
            "INSERT INTO permissions (code, name, name_en, module, display_name, category, is_active) "
            "VALUES (:code, :name, :name_en, :module, :display, :category, true)"
        ), {"code": code, "name": name, "name_en": name_en, "module": module, "display": name_en, "category": module})

    logger.info(f"Seeded {len(permissions_data)} permissions")

    # Seed default roles
    roles_data = [
        ("admin", "مدير النظام", "Full system administrator with all permissions"),
        ("accountant", "محاسب", "Accounting access with limited admin"),
        ("sales_rep", "مندوب مبيعات", "Sales representative"),
        ("viewer", "مشاهد", "Read-only access"),
    ]
    for name, name_en, description in roles_data:
        await conn.execute(text(
            "INSERT INTO roles (name, name_en, description, is_active, created_at) VALUES (:name, :name_en, :desc, true, NOW())"
        ), {"name": name, "name_en": name_en, "desc": description})

    logger.info("Seeded default roles")

    # Assign all permissions to admin role
    await conn.execute(text(
        """
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name = 'admin'
        """
    ))

    # Assign accounting permissions to accountant role
    await conn.execute(text(
        """
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name = 'accountant'
          AND p.code IN ('VIEW_SALE','CREATE_SALE','EDIT_SALE','VIEW_PURCHASE','CREATE_PURCHASE','EDIT_PURCHASE',
                          'VIEW_JOURNAL','CREATE_JOURNAL','EDIT_JOURNAL','POST_JOURNAL',
                          'VIEW_REPORTS','MANAGE_ASSETS','MANAGE_BUDGETS','RECONCILE_BANK','MANAGE_CHEQUES','VIEW_AGING_REPORTS',
                          'MANAGE_INVENTORY','VIEW_INVENTORY','VIEW_HR','VIEW_CRM')
        """
    ))

    # Assign sales permissions to sales_rep role
    await conn.execute(text(
        """
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name = 'sales_rep'
          AND p.code IN ('VIEW_SALE','CREATE_SALE','EDIT_SALE','VIEW_PURCHASE',
                          'VIEW_REPORTS','VIEW_INVENTORY','VIEW_CRM','MANAGE_CRM')
        """
    ))

    # Assign view-only permissions to viewer role
    await conn.execute(text(
        """
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name = 'viewer'
          AND p.code IN ('VIEW_SALE','VIEW_PURCHASE','VIEW_JOURNAL','VIEW_REPORTS',
                          'VIEW_AGING_REPORTS','VIEW_INVENTORY','VIEW_HR','VIEW_CRM')
        """
    ))

    logger.info("Seeded role-permission assignments")


async def _seed_numbering(conn):
    """Seed configurable document numbering sequences if none exist."""
    result = await conn.execute(text("SELECT COUNT(*) AS n FROM document_numbering"))
    count = result.scalar() or 0
    if count > 0:
        return

    now = datetime.now(UTC).replace(tzinfo=None)
    docs = [
        # doc_type, name, name_ar, prefix, zero_padding, include_year
        ("SALE", "Sales Invoice", "فاتورة مبيعات", "INV", 6, True),
        ("PURCHASE", "Purchase Order", "أمر شراء", "PO", 6, True),
        ("CREDIT_NOTE", "Credit Note", "إشعار دائن", "CN", 6, True),
        ("CUSTOMER_PAYMENT", "Customer Receipt", "سند قبض", "RC", 6, True),
        ("SUPPLIER_PAYMENT", "Supplier Payment", "سند دفع", "PV", 6, True),
        ("QUOTATION", "Quotation", "عرض سعر", "QU", 6, True),
        ("STOCK_TRANSFER", "Stock Transfer", "تحويل مخزني", "ST", 6, True),
        ("SALES_RETURN", "Sales Return", "مرتجع مبيعات", "SR", 6, True),
        ("PURCHASE_RETURN", "Purchase Return", "مرتجع مشتريات", "PR", 6, True),
        ("CHEQUE", "Cheque", "شيك", "CHQ", 6, True),
    ]
    for doc_type, name, name_ar, prefix, padding, include_year in docs:
        await conn.execute(text(
            """
            INSERT INTO document_numbering
                (doc_type, name, name_ar, prefix, suffix, zero_padding, include_year,
                 separator, period, next_value, is_active, created_at, updated_at)
            VALUES (:doc_type, :name, :name_ar, :prefix, NULL, :padding, :include_year,
                    '-', 'YEAR', 1, true, :now, :now)
            """
        ), {
            "doc_type": doc_type, "name": name, "name_ar": name_ar,
            "prefix": prefix, "padding": padding, "include_year": bool(include_year),
            "now": now,
        })
    logger.info("Seeded default document numbering sequences")


async def _ensure_rbac_columns(conn):
    """Ensure permissions and roles tables have all required columns."""
    migrations = [
        "ALTER TABLE permissions ADD COLUMN IF NOT EXISTS code VARCHAR(100);",
        "ALTER TABLE permissions ADD COLUMN IF NOT EXISTS name VARCHAR(200);",
        "ALTER TABLE permissions ADD COLUMN IF NOT EXISTS name_en VARCHAR(200);",
        "ALTER TABLE permissions ADD COLUMN IF NOT EXISTS module VARCHAR(50);",
        "ALTER TABLE permissions ADD COLUMN IF NOT EXISTS description TEXT;",
        "ALTER TABLE permissions ALTER COLUMN display_name DROP NOT NULL;",
        "ALTER TABLE permissions ALTER COLUMN category DROP NOT NULL;",
        "ALTER TABLE permissions ALTER COLUMN is_active DROP NOT NULL;",
        "ALTER TABLE permissions ALTER COLUMN name DROP NOT NULL;",
        "ALTER TABLE roles ADD COLUMN IF NOT EXISTS name_en VARCHAR(100);",
        "ALTER TABLE roles ADD COLUMN IF NOT EXISTS description TEXT;",
        "ALTER TABLE roles ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;",
        "ALTER TABLE roles ADD COLUMN IF NOT EXISTS created_at TIMESTAMP;",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_permissions_code ON permissions(code);",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_roles_name ON roles(name);",
    ]
    for statement in migrations:
        try:
            await conn.execute(text(statement))
        except Exception as e:
            logger.warning("RBAC migration failed (%s): %s", statement[:80], e)
    logger.info("Verified RBAC columns")


async def _add_fk_constraints(conn):
    """Add foreign key constraints to existing tables (idempotent).

    Each statement runs in its own SAVEPOINT so a single failure (e.g. a
    constraint that already exists on a legacy table) does NOT abort the
    surrounding transaction and break every subsequent ALTER.
    """
    constraints = [
        ("sale_items", "sale_id", "sales(id)"),
        ("sale_items", "product_id", "products(id)"),
        ("purchase_items", "purchase_id", "purchases(id)"),
        ("purchase_items", "product_id", "products(id)"),
        ("journal_entry_lines", "journal_entry_id", "journal_entries(id)"),
        ("journal_entry_lines", "account_id", "accounts(id)"),
    ]
    for table, column, ref in constraints:
        fk_name = f"fk_{table}_{column}"
        try:
            async with conn.begin_nested():
                await conn.execute(text(
                    f"ALTER TABLE {table} ADD CONSTRAINT {fk_name} "
                    f"FOREIGN KEY ({column}) REFERENCES {ref} NOT VALID;"
                ))
        except Exception as e:
            logger.warning("FK constraint skipped (%s.%s): %s", table, column, e)

    logger.info("Verified FK constraints")

    # Add unique constraint on journal entry numbers
    try:
        async with conn.begin_nested():
            await conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_journal_entries_entry_number ON journal_entries(entry_number);"
            ))
    except Exception as e:
        logger.warning("Journal entry number index skipped: %s", e)


app = FastAPI(
    title=settings.APP_NAME,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(sales.router, prefix="/api/sales", tags=["Sales"])
app.include_router(purchases.router, prefix="/api/purchases", tags=["Purchases"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["Inventory"])
app.include_router(accounting.router, prefix="/api/accounting", tags=["Accounting"])
app.include_router(hr.router, prefix="/api/hr", tags=["HR"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(crm.router, prefix="/api/crm", tags=["CRM"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["Settings"])
app.include_router(currencies.router, prefix="/api/currencies", tags=["Currencies"])
app.include_router(taxes.router, prefix="/api/taxes", tags=["Taxes"])
app.include_router(period_closing.router, prefix="/api/period-closing", tags=["Period Closing"])
app.include_router(financial_statements.router, prefix="/api/financial-statements", tags=["Financial Statements"])
app.include_router(fixed_assets.router, prefix="/api/fixed-assets", tags=["Fixed Assets"])
app.include_router(budgets.router, prefix="/api/budgets", tags=["Budgets"])
app.include_router(aging_reports.router, prefix="/api/aging-reports", tags=["Aging Reports"])
app.include_router(bank_reconciliation.router, prefix="/api/bank-reconciliation", tags=["Bank Reconciliation"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
app.include_router(returns.router, prefix="/api/returns", tags=["Returns"])
app.include_router(quotations.router, prefix="/api/quotations", tags=["Quotations"])
app.include_router(promotions.router, prefix="/api/promotions", tags=["Promotions"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(excel.router, prefix="/api/excel", tags=["Excel Import/Export"])
app.include_router(cheques.router, prefix="/api/cheques", tags=["Cheques"])
app.include_router(workflow.router, prefix="/api/workflow", tags=["Workflow"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(vouchers.router, prefix="/api/accounting", tags=["Accounting Vouchers"])


@app.get("/api/health")
async def health():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Health check failed: database unreachable: %s", exc)
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ok", "app": settings.APP_NAME, "database": "connected"}
