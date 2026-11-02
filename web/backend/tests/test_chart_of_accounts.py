"""Tests for the hardened chart-of-accounts behaviour:

- account code normalization + case-insensitive uniqueness
- account code charset validation
- type-change / opening-balance-change protection after postings
- parent/control re-flagging when accounts are reparented
- delete protection when an account carries an opening balance
- general-ledger sign convention (credit-side accounts positive)
- journal-entry search + void-by-reason (query param)
- Excel import: in-file parent resolution + type matching + control flagging
"""

import json
import uuid
import urllib.parse
import urllib.request
import urllib.error

import pytest

API_BASE = "http://localhost:8001/api"


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


def _code(prefix, n=4):
    return f"{prefix}{uuid.uuid4().hex[:4].upper()}"


def _create_account(token, code, name, acc_type, **extra):
    data = {
        "account_code": code,
        "account_name": name,
        "account_type": acc_type,
        "is_control": False,
    }
    data.update(extra)
    status, body = _raw("POST", "/accounting/accounts", token=token, data=data)
    assert status == 200, f"create account {code} failed: {status} {body}"
    return body["id"]


def _post_entry(token, db, date, description, lines):
    status, body = _raw("POST", "/accounting/journal-entries", token=token, data={
        "entry_date": date, "description": description, "lines": lines,
    })
    assert status == 200, f"create JE failed: {status} {body}"
    entry_id = body["id"]
    status, body = _raw("POST", f"/accounting/journal-entries/{entry_id}/post", token=token, data={})
    assert status == 200, f"post JE failed: {status} {body}"
    return entry_id


def _qs(params):
    return "?" + urllib.parse.urlencode({k: str(v) for k, v in params.items()})


def _purge_entry(db, entry_id):
    db("DELETE FROM journal_entry_lines WHERE journal_entry_id = %s", (entry_id,))
    db("DELETE FROM journal_entries WHERE id = %s", (entry_id,))


def _purge_account(db, account_id):
    for (je_id,) in db(
        "SELECT DISTINCT journal_entry_id FROM journal_entry_lines WHERE account_id = %s",
        (account_id,),
    ):
        _purge_entry(db, je_id)
    db("DELETE FROM accounts WHERE id = %s", (account_id,))


# ── Code normalization + uniqueness ─────────────────────────────────────

def test_code_is_trimmed_and_uniqueness_is_case_insensitive(admin_token, db):
    code = _code("31")
    full = f"  {code}  "
    status, acc = _raw("POST", "/accounting/accounts", token=admin_token, data={
        "account_code": full, "account_name": "Normalized", "account_type": "liability",
    })
    assert status == 200, f"create with padded code failed: {status} {acc}"
    stored = db("SELECT account_code FROM accounts WHERE id = %s", (acc["id"],))[0][0]
    assert stored == code, f"code not trimmed: {stored!r}"

    status, dup = _raw("POST", "/accounting/accounts", token=admin_token, data={
        "account_code": code.lower(), "account_name": "Dup", "account_type": "liability",
    })
    assert status == 400, f"case-insensitive duplicate must be rejected: {status} {dup}"

    _purge_account(db, acc["id"])


def test_invalid_code_format_rejected(admin_token, db):
    for bad in ["AB CD", "AB@CD", "AB#1"]:
        status, body = _raw("POST", "/accounting/accounts", token=admin_token, data={
            "account_code": bad, "account_name": "Bad", "account_type": "asset",
        })
        assert status == 400, f"code {bad!r} must be rejected: {status} {body}"
    ok = _code("11")
    status, body = _raw("POST", "/accounting/accounts", token=admin_token, data={
        "account_code": ok, "account_name": "Ok", "account_type": "asset",
    })
    assert status == 200, f"valid dotted/slashed code rejected: {status} {body}"
    _purge_account(db, body["id"])


def test_control_account_cannot_carry_opening_balance(admin_token, db):
    code = _code("11")
    status, body = _raw("POST", "/accounting/accounts", token=admin_token, data={
        "account_code": code, "account_name": "Ctrl", "account_type": "asset",
        "is_control": True, "opening_balance": 1000,
    })
    assert status == 400, f"control + opening must be rejected: {status} {body}"


# ── Type / opening-balance change protection after postings ─────────────

def test_type_change_blocked_after_posted_lines(admin_token, db):
    a = _create_account(admin_token, _code("79"), "Je A", "expense")
    b = _create_account(admin_token, _code("11"), "Je B", "asset")
    try:
        _post_entry(admin_token, db, "2026-01-10", "pytest type-lock", [
            {"account_id": a, "debit": 100, "credit": 0},
            {"account_id": b, "debit": 0, "credit": 100},
        ])
        status, body = _raw("PUT", f"/accounting/accounts/{a}", token=admin_token, data={
            "account_code": _code("11"), "account_name": "Je A", "account_type": "asset",
        })
        assert status == 400, f"type change with posted lines must be blocked: {status} {body}"
    finally:
        _purge_account(db, b)
        _purge_account(db, a)


def test_opening_balance_change_blocked_after_postings(admin_token, db):
    a = _create_account(admin_token, _code("11"), "Opening A", "asset")
    b = _create_account(admin_token, _code("79"), "Opening B", "expense")
    try:
        _post_entry(admin_token, db, "2026-01-10", "pytest opening-lock", [
            {"account_id": a, "debit": 100, "credit": 0},
            {"account_id": b, "debit": 0, "credit": 100},
        ])
        status, body = _raw("PUT", f"/accounting/accounts/{a}", token=admin_token, data={
            "account_code": _code("11"), "account_name": "Opening A", "account_type": "asset",
            "opening_balance": 5000,
        })
        assert status == 400, f"opening change with posted lines must be blocked: {status} {body}"
    finally:
        _purge_account(db, b)
        _purge_account(db, a)


# ── Reparenting re-flags control on parents ─────────────────────────────

def test_reparent_flags_new_parent_and_unflags_old(admin_token, db):
    p = _create_account(admin_token, _code("11"), "Parent P", "asset")
    m = _create_account(admin_token, _code("11"), "Parent M", "asset")
    c = _create_account(admin_token, _code("11"), "Child C", "asset", parent_id=p)
    try:
        old_flag = db("SELECT is_control FROM accounts WHERE id = %s", (p,))[0][0]
        assert old_flag is True, "parent must be flagged control after receiving a child"

        status, body = _raw("PUT", f"/accounting/accounts/{c}", token=admin_token, data={
            "account_code": _code("11"), "account_name": "Child C", "account_type": "asset",
            "parent_id": m,
        })
        assert status == 200, f"reparent failed: {status} {body}"

        m_flag = db("SELECT is_control FROM accounts WHERE id = %s", (m,))[0][0]
        p_flag = db("SELECT is_control FROM accounts WHERE id = %s", (p,))[0][0]
        assert m_flag is True, "new parent must be flagged control"
        assert p_flag is False, "old parent with no children must be unflagged control"
    finally:
        for acc_id in (c, m, p):
            _purge_account(db, acc_id)


def test_delete_blocked_when_opening_balance_present(admin_token, db):
    acc_id = _create_account(admin_token, _code("11"), "Has Opening", "asset", opening_balance=2500)
    try:
        status, body = _raw("DELETE", f"/accounting/accounts/{acc_id}", token=admin_token)
        assert status == 400, f"delete with opening balance must be blocked: {status} {body}"
    finally:
        db("DELETE FROM accounts WHERE id = %s", (acc_id,))


# ── General-ledger sign convention + journal search + void ──────────────

def test_general_ledger_credit_side_account_positive(admin_token, db):
    liab = _create_account(admin_token, _code("21"), "Liability GL", "liability")
    asset = _create_account(admin_token, _code("11"), "Asset GL", "asset")
    try:
        _post_entry(admin_token, db, "2026-01-10", "pytest gl sign", [
            {"account_id": asset, "debit": 250, "credit": 0},
            {"account_id": liab, "debit": 0, "credit": 250},
        ])
        status, body = _raw("GET", "/accounting/general-ledger" + _qs(
            {"account_id": liab, "from_date": "2026-01-01", "to_date": "2026-01-31"}),
                            token=admin_token)
        assert status == 200, f"GL failed: {status} {body}"
        txns = body["transactions"]
        assert txns, "no GL transactions"
        running = float(txns[-1]["running_balance"])
        closing = float(body["closing_balance"])
        assert abs(running - 250.0) < 0.01, f"liability running must be +250, got {running}"
        assert abs(closing - 250.0) < 0.01, f"liability closing must be +250, got {closing}"
    finally:
        _purge_account(db, asset)
        _purge_account(db, liab)


def test_journal_search_and_void_by_query_reason(admin_token, db):
    a = _create_account(admin_token, _code("11"), "Search A", "asset")
    b = _create_account(admin_token, _code("79"), "Search B", "expense")
    try:
        marker = f"pytest-search-{uuid.uuid4().hex[:6]}"
        status, body = _raw("POST", "/accounting/journal-entries", token=admin_token, data={
            "entry_date": "2026-01-10", "description": marker,
            "lines": [
                {"account_id": a, "debit": 60, "credit": 0},
                {"account_id": b, "debit": 0, "credit": 60},
            ],
        })
        assert status == 200, f"create JE failed: {status} {body}"
        entry_id = body["id"]
        entry_number = body["entry_number"]

        status, body = _raw("GET", "/accounting/journal-entries?search=" + marker, token=admin_token)
        assert status == 200, f"search failed: {status} {body}"
        assert any(str(it["entry_number"]) == entry_number for it in body["items"]), "search by description found nothing"

        status, body = _raw("GET", f"/accounting/journal-entries?search={entry_number}", token=admin_token)
        assert status == 200, f"search by number failed: {status} {body}"
        assert any(str(it["entry_number"]) == entry_number for it in body["items"]), "search by number found nothing"

        status, body = _raw("POST", f"/accounting/journal-entries/{entry_id}/post", token=admin_token, data={})
        assert status == 200, f"post failed: {status} {body}"

        status, body = _raw("POST", f"/accounting/journal-entries/{entry_id}/void?reason={urllib.parse.quote('test reason')}",
                            token=admin_token, data={})
        assert status == 200, f"void via query reason failed: {status} {body}"
        from_db = db("SELECT status FROM journal_entries WHERE id = %s", (entry_id,))[0][0]
        assert from_db == "Voided", f"unexpected status after void: {from_db}"
        reversal_count = db(
            "SELECT COUNT(*) FROM journal_entries WHERE reference_type='JournalEntryReversal' AND reference_id=%s",
            (entry_id,),
        )[0][0]
        assert reversal_count >= 1, "void must create a reversing entry"
    finally:
        for (je_id,) in db("SELECT id FROM journal_entries WHERE description = %s", (marker,)):
            _purge_entry(db, je_id)
        _purge_account(db, b)
        _purge_account(db, a)


# ── Excel import: in-file parents, types, control flagging ──────────────

def test_import_supports_in_file_parents(admin_token, db):
    openpyxl = pytest.importorskip("openpyxl")
    from io import BytesIO
    from openpyxl import Workbook

    token = _admin_token()
    parent_code = _code("11")
    child_code = _code("11")
    sibling_code = _code("11")

    wb = Workbook()
    ws = wb.active
    ws.append(["code", "name", "type", "parent_code", "is_control", "opening_balance"])
    ws.append([parent_code, "Imported Parent", "asset", "", "FALSE", "0"])
    ws.append([child_code, "Imported Child", "asset", parent_code, "FALSE", "100"])
    ws.append([sibling_code, "Type Mismatch", "expense", parent_code, "FALSE", "0"])
    buf = BytesIO()
    wb.save(buf)
    blob = buf.getvalue()

    boundary = uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="chart.xlsx"\r\n'
        f"Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n"
    ).encode() + blob + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        API_BASE + "/excel/imports/chart-of-accounts",
        data=body, method="POST",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())

    try:
        assert result["imported"] == 2, f"expected 2 imported, got {result}"
        assert result["failed"] == 1, f"expected 1 rejected (type mismatch), got {result}"
        assert any("يجب أن يطابق" in e["error"] for e in result["errors"]), f"mismatch error missing: {result['errors']}"

        rows = db(
            "SELECT account_code, is_control, COALESCE(parent_id,0), opening_balance FROM accounts "
            "WHERE account_code = ANY(%s)", ([parent_code, child_code],),
        )
        by_code = {r[0]: r for r in rows}
        assert parent_code in by_code and child_code in by_code, f"imported rows missing: {by_code}"
        assert by_code[parent_code][1] is True, "in-file parent must be flagged control"
        assert by_code[parent_code][2] == 0, "parent must be a root"
        assert by_code[child_code][1] is False, "leaf must not be control"
        parent_id = db("SELECT id FROM accounts WHERE account_code = %s", (parent_code,))[0][0]
        assert by_code[child_code][2] == parent_id, "child must link to imported parent"
        assert float(by_code[child_code][3]) == 100.0, "leaf opening balance must be kept"
    finally:
        db("DELETE FROM accounts WHERE account_code = ANY(%s)", ([child_code, parent_code, sibling_code],))