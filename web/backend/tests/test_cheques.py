"""Tests for the Cheques module (live stack).

Lifecycle coverage:
  - create received / issued cheques with auto numbering
  - validation (positive amount, valid type)
  - received lifecycle: on_hand → deposited → cleared
  - invalid transitions rejected
  - bulk deposit of multiple received cheques
  - audit trail rows for transitions
"""

import json
import uuid

import pytest

API_BASE = "http://localhost:8001/api"


def _raw(method, path, token=None, data=None, headers=None, timeout=30):
    import urllib.error
    import urllib.request

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


@pytest.fixture(scope="module")
def token():
    status, body = _raw("POST", "/auth/login", data={"username": "admin", "password": "admin123"})
    assert status == 200, f"login failed: {status} {body}"
    return body["access_token"]


def _make_cheque(token, cheque_type="received", amount=1000, **extra):
    payload = {"cheque_type": cheque_type, "amount": amount, **extra}
    return _raw("POST", "/cheques", token=token, data=payload)


# ── Create ──────────────────────────────────────────────────────────────

def test_cheque_create_received_auto_number(token):
    status, body = _make_cheque(token, "received", 1500, payer_name="Test Payer", description="pytest received")
    assert status == 200, f"expected 200 got {status}: {body}"
    assert body["id"]
    assert body["cheque_number"].startswith("CHQ-")


def test_cheque_create_issued(token):
    status, body = _make_cheque(token, "issued", 2000, payee_name="Test Payee", description="pytest issued")
    assert status == 200, f"expected 200 got {status}: {body}"
    # verify it was persisted with the right type
    status2, item = _raw("GET", f"/cheques/{body['id']}", token=token)
    assert status2 == 200
    assert item["cheque_type"] == "issued"
    assert item["payee_name"] == "Test Payee"
    assert item["status"] == "on_hand"


def test_cheque_create_rejects_zero_amount(token):
    status, body = _make_cheque(token, "received", 0)
    assert status == 400


def test_cheque_create_rejects_negative_amount(token):
    status, body = _make_cheque(token, "received", -5)
    assert status == 400


def test_cheque_create_rejects_invalid_type(token):
    status, body = _make_cheque(token, "third_party", 100)
    assert status == 400


# ── Lifecycle ───────────────────────────────────────────────────────────

def test_cheque_received_lifecycle_deposit_clear(token):
    status, body = _make_cheque(token, "received", 2500, payer_name="Lifecycle Payer")
    assert status == 200
    cid = body["id"]

    # on_hand → deposited
    status, body = _raw("POST", f"/cheques/{cid}/transition", token=token,
                        data={"status": "deposited", "bank_name": "TestBank"})
    assert status == 200, f"deposit failed: {status} {body}"
    assert body["status"] == "deposited"

    # deposited → cleared
    status, body = _raw("POST", f"/cheques/{cid}/transition", token=token,
                        data={"status": "cleared", "clear_date": "2026-09-15"})
    assert status == 200, f"clear failed: {status} {body}"
    assert body["status"] == "cleared"

    # Final persisted state
    status, item = _raw("GET", f"/cheques/{cid}", token=token)
    assert status == 200
    assert item["status"] == "cleared"
    assert item["clear_date"]


def test_cheque_issued_lifecycle_stop(token):
    status, body = _make_cheque(token, "issued", 800, payee_name="Stopped Payee")
    assert status == 200
    cid = body["id"]

    status, body = _raw("POST", f"/cheques/{cid}/transition", token=token,
                        data={"status": "stopped", "reason": "pytest stop"})
    assert status == 200
    assert body["status"] == "stopped"


def test_cheque_invalid_transition_rejected(token):
    status, body = _make_cheque(token, "issued", 500, payee_name="Invalid Tx Party")
    assert status == 200
    cid = body["id"]

    # stopped → cleared is not allowed
    status, body = _raw("POST", f"/cheques/{cid}/transition", token=token, data={"status": "stopped"})
    assert status == 200

    status, body = _raw("POST", f"/cheques/{cid}/transition", token=token, data={"status": "cleared"})
    assert status == 400


def test_cheque_missing_returns_404(token):
    status, body = _raw("GET", "/cheques/99999999", token=token)
    assert status == 404


# ── Bulk deposit ────────────────────────────────────────────────────────

def test_cheque_bulk_deposit(token):
    # Create a bank to deposit into
    bank_status, bank_body = _raw("POST", "/payments/banks", token=token,
                                  data={"bank_name": f"Bulk Test {uuid.uuid4().hex[:4]}", "account_name": "bulk",
                                        "account_number": f"BK{uuid.uuid4().hex[:8]}", "is_active": True})
    assert bank_status in (200, 201), f"bank create failed: {bank_status} {bank_body}"
    bank_id = bank_body.get("id")

    ids = []
    for _ in range(2):
        s, b = _make_cheque(token, "received", 300, payer_name="Bulk Payer")
        assert s == 200
        ids.append(b["id"])

    status, body = _raw("POST", "/cheques/bulk-deposit", token=token,
                        data={"cheque_ids": ids, "bank_id": bank_id})
    assert status == 200, f"bulk deposit failed: {status} {body}"
    assert body["deposited"] == 2

    # Verify all are now deposited
    for cid in ids:
        s, item = _raw("GET", f"/cheques/{cid}", token=token)
        assert s == 200
        assert item["status"] == "deposited"


# ── Audit ───────────────────────────────────────────────────────────────

def test_cheque_transitions_audited(token):
    s, body = _make_cheque(token, "received", 450, payer_name="Audit Payer")
    assert s == 200
    cid = body["id"]

    for status_val in ("deposited",):
        s, _ = _raw("POST", f"/cheques/{cid}/transition", token=token, data={"status": status_val})
        assert s == 200

    status, audit = _raw("GET", "/audit/logs?entity_type=Cheque&per_page=50", token=token)
    assert status == 200
    logs = audit.get("logs") or []
    assert any(log.get("entity_id") == cid and log.get("action") == "TRANSITION_DEPOSITED" for log in logs)


# ── Summary ─────────────────────────────────────────────────────────────

def test_cheque_summary_counts(token):
    status, body = _raw("GET", "/cheques/summary/counts", token=token)
    assert status == 200
    assert isinstance(body.get("received", {}), dict)
    assert isinstance(body.get("issued", {}), dict)