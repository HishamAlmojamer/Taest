import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routers import (
    auth, sales, purchases, inventory, accounting,
    hr, payments, projects, crm, reports,
    settings as settings_router,
    currencies, taxes, period_closing, financial_statements,
    fixed_assets, budgets, aging_reports, bank_reconciliation,
    audit,
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")
    yield
    await engine.dispose()

app = FastAPI(title=settings.APP_NAME, docs_url="/docs", redoc_url="/redoc", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
