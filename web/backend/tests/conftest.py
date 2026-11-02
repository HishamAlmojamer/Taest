import os
import subprocess

import pytest

API_BASE = os.getenv("ERP_API_BASE", "http://localhost:8001/api")
GATEWAY_BASE = os.getenv("ERP_GATEWAY_BASE", "http://localhost:3001")
DB_URL = os.getenv(
    "ERP_DB_URL",
    "postgresql://postgres:postgres@127.0.0.1:5432/warehouse_management",
)


@pytest.fixture(scope="session")
def admin_token():
    import urllib.request
    import json
    import time

    body = json.dumps({"username": "admin", "password": "admin123"}).encode()
    last_err = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                API_BASE + "/auth/login",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            return data["access_token"]
        except Exception as exc:
            last_err = exc
            time.sleep(5)
    raise last_err


@pytest.fixture(scope="session")
def api():
    """Returns a small HTTP client helper bound to the live backend."""

    def call(method, path, token=None, data=None, timeout=25):
        import json
        import urllib.request
        import urllib.error

        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        body = json.dumps(data).encode() if data is not None else None
        req = urllib.request.Request(
            API_BASE + path, data=body, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                return {"status": resp.status, "data": json.loads(raw) if raw else None}
        except urllib.error.HTTPError as e:
            raw = e.read()
            try:
                payload = json.loads(raw)
            except Exception:
                payload = raw.decode(errors="replace")
            return {"status": e.code, "data": payload}

    return call


@pytest.fixture(scope="session")
def db():
    """Returns a small helper that runs SQL; each call uses a fresh connection."""
    import urllib.error

    try:
        import psycopg2
    except ImportError:
        pytest.skip("psycopg2 not installed; DB assertions skipped")

    def run(sql, params=None):
        conn = psycopg2.connect(DB_URL)
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                if cur.description:
                    return cur.fetchall()
                return None
        finally:
            conn.commit()
            conn.close()

    return run


def _db_connection():
    import psycopg2

    return psycopg2.connect(DB_URL)


# Tables the live-stack tests create rows in. Cleanup deletes everything with
# id > the value captured at session start (FK order: children before parents).
# Handles the accounting unit fixtures, cheque lifecycle tests and the
# ledger-integrity E2E flows (sales, purchases, returns, payments, products).
_CLEANUP_ORDER = [
    "journal_items",
    "journal_entry_lines",
    "customer_transactions",
    "supplier_transactions",
    "bank_transactions",
    "inventory_transactions",
    "invoices",
    "stock_movements",
    "sale_items",
    "purchase_items",
    "sales_return_items",
    "purchase_return_items",
    "stock_transfer_items",
    "inventory_batches",
    "inventory_count_lines",
    "product_warehouse",
    "customer_payments",
    "supplier_payments",
    "sales_returns",
    "purchase_returns",
    "sales",
    "purchases",
    "cheques",
    "depreciation_entries",
    "fixed_assets",
    "asset_categories",
    "period_closing_entries",
    "accounting_vouchers",
    "cost_center_allocation_rule_lines",
    "cost_center_allocation_rules",
    "cost_centers",
    "banks",
    "products",
    "journal_entries",
    "fiscal_periods",
    "fiscal_years",
]
_USER_CLEANUP = "DELETE FROM users WHERE username LIKE 'rbac\\_%' ESCAPE '\\'"


@pytest.fixture(scope="session", autouse=True)
def _cleanup_session_artifacts():
    """Snapshot max ids at session start; on teardown delete anything the
    test run added, in FK-safe order, so repeated pytest runs never pollute
    the live books. Failures are logged but never fail the test itself."""
    import sys

    try:
        conn = _db_connection()
    except Exception as exc:  # no live stack → skip silently
        print(f"[cleanup] skip, no DB: {exc}", file=sys.stderr)
        yield
        return

    baselines = {}
    try:
        with conn.cursor() as cur:
            for table in _CLEANUP_ORDER:
                try:
                    cur.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table}")
                    baselines[table] = cur.fetchone()[0]
                except Exception:
                    # A missing table aborts the transaction; roll back so the
                    # remaining tables (notably products) still get a baseline.
                    baselines[table] = None
                    conn.rollback()
    finally:
        conn.close()

    yield

    try:
        conn = _db_connection()
        with conn.cursor() as cur:
            for table in _CLEANUP_ORDER:
                base = baselines.get(table)
                if base is None:
                    continue
                try:
                    cur.execute(f"DELETE FROM {table} WHERE id > %s", (base,))
                except Exception as exc:
                    print(f"[cleanup] {table}: {exc}", file=sys.stderr)
                    conn.rollback()
                else:
                    conn.commit()
            try:
                cur.execute(_USER_CLEANUP)
                conn.commit()
            except Exception as exc:
                print(f"[cleanup] users: {exc}", file=sys.stderr)
                conn.rollback()
        conn.close()
    except Exception as exc:
        print(f"[cleanup] failure: {exc}", file=sys.stderr)


def pytest_collection_modifyitems(config, items):
    """Mark tests that need the live stack (backend+gateway+DB) running."""
    pass