"""Tests for the newly completed accounting units:
- Excel export/import round-trip (live stack)
- Fiscal period lock / unlock / reopen
- Cost-center allocation rules (preview + apply produce balanced entries)
- FX revaluation preview/post
"""

import json
import uuid
import urllib.request
import urllib.error

import pytest

API_BASE = "http://localhost:8001/api"

XLSX_MAGIC = b"PK\x03\x04"


# ── Raw helpers (binary-safe, bypass JSON-only `api` fixture) ──────────

def _raw(method, path, token=None, data=None, headers=None, timeout=30):
    req_headers = {} if headers is None else dict(headers)
    if token:
        req_headers["Authorization"] = f"Bearer {token}"
    body = None
    if data is not None:
        req_headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode()
    req = urllib.request.Request(API_BASE + path, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            try:
                return resp.status, json.loads(raw)
            except Exception:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def _admin_token():
    status, body = _raw("POST", "/auth/login", data={"username": "admin", "password": "admin123"})
    assert status == 200, f"login failed: {status} {body}"
    return body["access_token"]


# ── Excel exports ───────────────────────────────────────────────────────

EXPORT_ENDPOINTS = [
    ("GET", "/excel/exports/chart-of-accounts"),
    ("GET", "/excel/exports/journal-entries"),
    ("GET", "/excel/exports/trial-balance"),
    ("GET", "/excel/exports/income-statement"),
    ("GET", "/excel/exports/balance-sheet"),
    ("GET", "/excel/exports/cash-flow"),
    ("GET", "/excel/exports/cost-centers"),
    ("GET", "/excel/exports/cost-center-report"),
    ("GET", "/excel/exports/currencies"),
    ("GET", "/excel/exports/tax-rates"),
    ("GET", "/excel/exports/ar-aging"),
    ("GET", "/excel/exports/ap-aging"),
    ("GET", "/excel/templates/chart-of-accounts"),
    ("GET", "/excel/templates/journal-entries"),
]


def test_all_excel_exports_return_workbook_bytes():
    token = _admin_token()
    for method, path in EXPORT_ENDPOINTS:
        status, body = _raw(method, path, token=token)
        assert status == 200, f"{path} failed: {status} {body}"
        assert isinstance(body, bytes), f"{path} did not return binary content"
        assert body.startswith(XLSX_MAGIC), f"{path} returned non-xlsx bytes"


def test_general_ledger_export_requires_account_param():
    token = _admin_token()
    status, body = _raw("GET", "/excel/exports/general-ledger", token=token)
    assert status in (400, 422), f"missing account_id should be rejected, got {status} {body}"


# ── Fiscal period lock / unlock / reopen ────────────────────────────────

@pytest.fixture()
def temp_period(admin_token):
    """Create + cleanup a throw-away fiscal period via the API."""
    name = f"pTST-{uuid.uuid4().hex[:6]}"
    status, created = _raw("POST", "/period-closing/fiscal-periods", token=admin_token, data={
        "name": name,
        "start_date": "2020-01-01",
        "end_date": "2020-12-31",
    })
    assert status == 200, f"create period failed: {status} {created}"
    yield created["id"]
    # Period table has no delete endpoint; hard-delete in DB since it's test data.
    import os
    import psycopg2
    conn = psycopg2.connect(os.getenv("ERP_DB_URL", "postgresql://postgres:postgres@127.0.0.1:5432/warehouse_management"))
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM fiscal_periods WHERE id = %s", (created["id"],))
        conn.commit()
    finally:
        conn.close()


def test_fiscal_period_lock_unlock_roundtrip(temp_period, admin_token):
    pid = temp_period
    status, _ = _raw("POST", f"/period-closing/fiscal-periods/{pid}/lock", token=admin_token, data={})
    assert status == 200
    status, _ = _raw("POST", f"/period-closing/fiscal-periods/{pid}/unlock", token=admin_token, data={})
    assert status == 200
    # Unlocking twice must fail (guards idempotency).
    status, body = _raw("POST", f"/period-closing/fiscal-periods/{pid}/unlock", token=admin_token, data={})
    assert status == 400, f"double unlock should be rejected: {status} {body}"


def test_fiscal_period_close_then_reopen(temp_period, admin_token):
    pid = temp_period
    status, closed = _raw("POST", f"/period-closing/fiscal-periods/{pid}/close", token=admin_token, data={})
    assert status == 200, f"close failed: {status} {closed}"
    status, reopened = _raw("POST", f"/period-closing/fiscal-periods/{pid}/reopen", token=admin_token, data={})
    assert status == 200, f"reopen failed: {status} {reopened}"
    status, body = _raw("POST", f"/period-closing/fiscal-periods/{pid}/reopen", token=admin_token, data={})
    assert status == 400, f"reopen on open period must fail: {status} {body}"


def test_fiscal_period_actions_audited(temp_period, admin_token):
    pid = temp_period
    _raw("POST", f"/period-closing/fiscal-periods/{pid}/lock", token=admin_token, data={})
    _raw("POST", f"/period-closing/fiscal-periods/{pid}/unlock", token=admin_token, data={})
    status, body = _raw("GET", "/audit/logs?entity_type=FiscalPeriod&per_page=100", token=admin_token)
    assert status == 200, f"audit logs failed: {status} {body}"
    logs = body.get("logs") if isinstance(body, dict) else []
    ours = {l["action"] for l in logs if l.get("entity_id") == pid}
    assert {"LOCK", "UNLOCK"} <= ours, f"missing audit actions for period, got {ours}"


# ── Cost-center allocation rules ────────────────────────────────────────
# All fixtures here are self-cleaning: created accounts, cost centers,
# allocation rules and journal entries are hard-deleted again so repeated
# pytest runs never pollute the live books.

def _purge_entry(db, entry_id):
    db("DELETE FROM journal_entry_lines WHERE journal_entry_id = %s", (entry_id,))
    db("DELETE FROM journal_entries WHERE id = %s", (entry_id,))


def _purge_account(db, account_id):
    """Delete any JEs, allocation rules and finally the account itself."""
    je_ids = [r[0] for r in db(
        "SELECT DISTINCT journal_entry_id FROM journal_entry_lines WHERE account_id = %s",
        (account_id,),
    )]
    for je_id in je_ids:
        _purge_entry(db, je_id)
    rule_ids = [r[0] for r in db(
        "SELECT id FROM cost_center_allocation_rules "
        "WHERE source_account_id = %s OR target_account_id = %s",
        (account_id, account_id),
    )]
    for rule_id in rule_ids:
        db("DELETE FROM cost_center_allocation_rule_lines WHERE rule_id = %s", (rule_id,))
        db("DELETE FROM cost_center_allocation_rules WHERE id = %s", (rule_id,))
    db("DELETE FROM accounts WHERE id = %s", (account_id,))


def _purge_cost_center(db, cost_center_id):
    """Delete any rule lines/rules and JEs touching the cost center, then the center."""
    je_ids = [r[0] for r in db(
        "SELECT DISTINCT journal_entry_id FROM journal_entry_lines WHERE cost_center_id = %s",
        (cost_center_id,),
    )]
    for je_id in je_ids:
        _purge_entry(db, je_id)
    rule_ids = [r[0] for r in db(
        "SELECT DISTINCT rule_id FROM cost_center_allocation_rule_lines WHERE cost_center_id = %s",
        (cost_center_id,),
    )]
    for rule_id in rule_ids:
        db("DELETE FROM cost_center_allocation_rule_lines WHERE rule_id = %s", (rule_id,))
        db("DELETE FROM cost_center_allocation_rules WHERE id = %s", (rule_id,))
    db("DELETE FROM cost_centers WHERE id = %s", (cost_center_id,))


@pytest.fixture()
def expense_account(admin_token, db):
    code = f"79{uuid.uuid4().hex[:4].upper()}"
    status, acc = _raw("POST", "/accounting/accounts", token=admin_token, data={
        "account_code": code, "account_name": f"Test Expense {code}", "account_type": "expense",
        "is_control": False, "is_active": True,
    })
    assert status == 200, f"create account failed: {status} {acc}"
    yield acc["id"]
    _purge_account(db, acc["id"])


@pytest.fixture()
def counter_account(admin_token, db):
    """A non-expense account used as the credit side of test entries."""
    code = f"11{uuid.uuid4().hex[:4].upper()}"
    status, acc = _raw("POST", "/accounting/accounts", token=admin_token, data={
        "account_code": code, "account_name": f"Test Bank {code}", "account_type": "asset",
        "is_control": False, "is_active": True,
    })
    assert status == 200, f"create counter account failed: {status} {acc}"
    yield acc["id"]
    _purge_account(db, acc["id"])


@pytest.fixture()
def cost_center(admin_token, db):
    code = f"CC{uuid.uuid4().hex[:4].upper()}"
    status, cc = _raw("POST", "/accounting/cost-centers", token=admin_token, data={"code": code, "name": f"CC {code}"})
    assert status == 200, f"create cost center failed: {status} {cc}"
    yield cc["id"]
    _purge_cost_center(db, cc["id"])


def test_allocation_rule_requires_100_percent(admin_token, expense_account, cost_center):
    status, body = _raw("POST", "/accounting/cost-centers/allocation-rules", token=admin_token, data={
        "name": "bad pct",
        "source_account_id": expense_account,
        "lines": [{"cost_center_id": cost_center, "percentage": 50}],
    })
    assert status == 400, f"sum != 100 must be rejected: {status} {body}"


def test_allocation_rule_preview_and_apply_balanced(api, admin_token, db, expense_account, counter_account, cost_center):
    # 1) Post a source-balance entry (Dr expense account 500).
    r = api("POST", "/accounting/journal-entries", token=admin_token, data={
        "entry_date": "2026-01-10",
        "description": "pytest allocation source",
        "lines": [
            {"account_id": expense_account, "debit": 500, "credit": 0},
            {"account_id": counter_account, "debit": 0, "credit": 500},
        ],
    })
    assert r["status"] == 200, f"create JE failed: {r}"
    entry_id = r["data"]["id"]
    assert db("SELECT id, status FROM journal_entries WHERE id = %s", (entry_id,)), \
        f"created JE {entry_id} is not in the database (create returned {r})"
    r = api("POST", f"/accounting/journal-entries/{entry_id}/post", token=admin_token, data={})
    assert r["status"] == 200, f"post JE failed: {r}"

    # 2) Create an allocation rule 100% -> this cost center.
    r = api("POST", "/accounting/cost-centers/allocation-rules", token=admin_token, data={
        "name": "pytest alloc",
        "source_account_id": expense_account,
        "lines": [{"cost_center_id": cost_center, "percentage": 100}],
    })
    assert r["status"] == 200, f"create rule failed: {r}"
    rule_id = r["data"]["id"]

    # 3) Preview over the window.
    r = api("POST", f"/accounting/cost-centers/allocation-rules/{rule_id}/preview",
            token=admin_token, data={"from_date": "2026-01-01", "to_date": "2026-01-31"})
    assert r["status"] == 200, f"preview failed: {r}"
    preview = r["data"]
    assert abs(float(preview["balance"]) - 500.0) < 0.01, preview
    assert abs(float(preview["total"]) - 500.0) < 0.01, preview

    # 4) Apply and verify a balanced posted entry exists.
    r = api("POST", f"/accounting/cost-centers/allocation-rules/{rule_id}/apply",
            token=admin_token, data={"from_date": "2026-01-01", "to_date": "2026-01-31"})
    assert r["status"] == 200, f"apply failed: {r}"
    db_entry = db(
        "SELECT id FROM journal_entries WHERE reference_type='CostCenterAllocation' "
        "AND reference_id=%s ORDER BY id DESC LIMIT 1",
        (rule_id,),
    )
    assert db_entry, "applied allocation entry not found"
    d, c = db("SELECT SUM(debit), SUM(credit) FROM journal_entry_lines WHERE journal_entry_id=%s", (db_entry[0][0],))[0]
    assert abs(float(d) - float(c)) < 0.01, f"allocation entry unbalanced: d={d} c={c}"


# ── Excel journal import round-trip ─────────────────────────────────────

def test_journal_import_roundtrip(admin_token, db):
    openpyxl = pytest.importorskip("openpyxl")
    from io import BytesIO

    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["entry_reference", "entry_date", "description", "account_code",
               "cost_center_code", "currency_code", "debit", "credit", "counterpart_code"])
    ws.append(["IMP-TST", "2026-03-15", "pytest import", "1111", "", "SAR", "120", "0", ""])
    ws.append(["IMP-TST", "2026-03-15", "pytest import", "4110", "", "SAR", "0", "120", ""])
    buf = BytesIO()
    wb.save(buf)
    blob = buf.getvalue()

    token = _admin_token()
    boundary = uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="imp.xlsx"\r\n'
        f"Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n"
    ).encode() + blob + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        API_BASE + "/excel/imports/journal-entries",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
    assert result["imported"] >= 1, result
    assert result["failed"] == 0, result
    # Cleanup: remove the imported journal entry again (test data only).
    je_ids = [r[0] for r in db(
        "SELECT id FROM journal_entries WHERE reference_type='ExcelImport' AND description='pytest import'"
    )]
    for je_id in je_ids:
        _purge_entry(db, je_id)


# ── FX revaluation ──────────────────────────────────────────────────────

def test_fx_revaluation_preview(admin_token):
    status, preview = _raw("POST", "/currencies/revaluate/preview", token=admin_token,
                           data={"as_of_date": "2026-09-09"})
    assert status == 200, f"preview failed: {status} {preview}"
    assert "differences" in preview and "net_difference" in preview


def test_fx_revaluation_post_never_crashes(admin_token):
    status, body = _raw("POST", "/currencies/revaluate", token=admin_token,
                        data={"as_of_date": "2026-09-09"})
    # Either nothing to post (200, posted:0) or a posted entry (200) — never a 5xx.
    assert status in (200, 400), f"revaluation post failed: {status} {body}"


# ── Aging statements (Decimal money math) ───────────────────────────────

def _statement_subject(db, table, id_col, code_col):
    """Pick a row that actually has money movements, so the Decimal
    accumulation path is exercised rather than the empty short-circuit."""
    rows = db(
        f"SELECT t.id, t.{code_col} FROM {table} t "
        f"WHERE EXISTS (SELECT 1 FROM {'sales' if table == 'customers' else 'purchases'} x "
        f"WHERE x.{'customer' if table == 'customers' else 'supplier'}_id = t.id) "
        f"ORDER BY t.id LIMIT 1"
    )
    if rows:
        return rows[0]
    return db(f"SELECT id, {code_col} FROM {table} ORDER BY id LIMIT 1")[0]


@pytest.mark.parametrize("endpoint,table,code_col", [
    ("customer-statement", "customers", "code"),
    ("supplier-statement", "suppliers", "code"),
])
def test_aging_statement_handles_decimal_amounts(admin_token, db, endpoint, table, code_col):
    """Regression: running balance started at 0.0 and was accumulated with
    Numeric columns, raising TypeError (HTTP 500) for any subject with
    transactions. Money math must stay Decimal throughout."""
    subject_id, _ = _statement_subject(db, table, "id", code_col)
    assert subject_id is not None, f"no row in {table} to test against"

    status, body = _raw("GET", f"/aging-reports/{endpoint}/{subject_id}",
                        token=admin_token, timeout=30)
    assert status == 200, f"{endpoint} returned {status}: {body}"

    assert body["period"]["start"] and body["period"]["end"]
    assert isinstance(body["closing_balance"], (int, float))
    for txn in body["transactions"]:
        assert isinstance(txn["balance"], (int, float)), txn
        assert txn["type"] in ("SALE", "PAYMENT", "PURCHASE"), txn


def test_aging_statement_unknown_subject_returns_404(admin_token):
    status, _ = _raw("GET", "/aging-reports/customer-statement/99999999", token=admin_token)
    assert status == 404, f"expected 404 for unknown customer, got {status}"