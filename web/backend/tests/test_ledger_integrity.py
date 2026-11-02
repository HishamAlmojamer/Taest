"""Ledger integrity tests.

These tests run against the live stack (backend :8001, gateway :3001,
Postgres :5432) and assert the core double-entry invariant:

    For every posted journal entry, SUM(debit) == SUM(credit).

The critical regression covered here is the "discount bug": when a sale is
approved, the gateway must post
    Dr AR = finalAmount
    Cr Revenue = finalAmount - taxAmount
    Cr VAT = taxAmount
so the entry balances regardless of whether totalAmount is gross or net.
"""

import pytest


def _supplier_id(db):
    """Return an existing supplier id (tests must not assume seed data)."""
    rows = db("SELECT id FROM suppliers ORDER BY id LIMIT 1")
    assert rows, "no suppliers found; seed at least one supplier before running tests"
    return rows[0][0]


def _create_sale(api, token, *, total_amount, discount, tax_amount, final_amount, product_id, qty=2, price=10.0):
    payload = {
        "customer_id": 64,
        "total_amount": total_amount,
        "discount": discount,
        "final_amount": final_amount,
        "payment_method": "credit",
        "payment_status": "unpaid",
        "company_id": 1,
        "branch_id": 1,
        "tax_amount": tax_amount,
        "notes": "pytest ledger integrity",
        "items": [{"product_id": product_id, "quantity": qty, "unit_price": price, "total_price": qty * price}],
    }
    r = api("POST", "/sales", token=token, data=payload)
    assert r["status"] == 200, f"sale create failed: {r}"
    return r["data"]["id"]


def _approve_sale(api, token, sale_id):
    r = api("POST", f"/sales/{sale_id}/submit", token=token, data={})
    assert r["status"] == 200, f"submit failed: {r}"
    r = api("POST", f"/sales/{sale_id}/approve", token=token, data={})
    assert r["status"] == 200, f"approve failed: {r}"
    return r["data"]


@pytest.fixture(scope="module")
def product_id(api, admin_token, db):
    import uuid

    code = f"TST{uuid.uuid4().hex[:8].upper()}"
    r = api("POST", "/inventory/products", token=admin_token,
            data={"code": code, "name": f"Test Product {code}",
                  "unit": "pcs", "purchase_price": 5.0,
                  "selling_price": 10.0, "current_stock": 0.0, "company_id": 1})
    assert r["status"] == 200, f"product create failed: {r}"
    prod_id = r["data"]["id"]

    r = api("POST", "/inventory/stock-movements", token=admin_token,
            data={"product_id": prod_id, "movement_type": "in",
                  "quantity": 500, "unit_cost": 5.0,
                  "reference_type": "pytest", "notes": "pytest stock"})
    if r["status"] != 200:
        # Fall back to a direct stock bump so approval tests can proceed.
        db("UPDATE products SET current_stock = 500 WHERE id = %s", (prod_id,))
    return prod_id


def test_login_ok(admin_token):
    assert admin_token


def test_all_entries_balanced_in_db(db):
    rows = db(
        """
        SELECT je.entry_number,
               ABS(COALESCE(SUM(jl.debit),0) - COALESCE(SUM(jl.credit),0)) AS diff
        FROM journal_entries je
        LEFT JOIN journal_entry_lines jl ON jl.journal_entry_id = je.id
        WHERE je.status = 'Posted'
        GROUP BY je.id, je.entry_number
        HAVING ABS(COALESCE(SUM(jl.debit),0) - COALESCE(SUM(jl.credit),0)) > 0.01
        """
    )
    assert not rows, f"unbalanced posted entries: {rows}"


def test_net_sale_with_discount_balances_and_approves(api, admin_token, db, product_id):
    """New-style sale: total_amount is already net of discount (frontend behavior)."""
    sale_id = _create_sale(
        api, admin_token,
        total_amount=15.0, discount=5.0, tax_amount=2.25, final_amount=17.25,
        product_id=product_id, qty=2, price=10.0,
    )
    approved = _approve_sale(api, admin_token, sale_id)
    assert approved["workflow_state"] == "approved"
    entry_id = approved.get("journal_entry_id")
    assert entry_id, "approved sale missing journal_entry_id"
    rows = db(
        "SELECT SUM(jl.debit), SUM(jl.credit) FROM journal_entry_lines jl "
        "WHERE jl.journal_entry_id = %s",
        (entry_id,),
    )
    d, c = rows[0]
    assert abs(float(d) - float(c)) < 0.01, f"posted entry {entry_id} unbalanced: d={d} c={c}"


def test_gross_style_discount_sale_balances_and_approves(api, admin_token, db, product_id):
    """Legacy-style sale: total_amount is gross, discount separate (final = total + tax - discount)."""
    total, discount, tax, final = 4063.88, 66.19, 530.07, 3600.00
    sale_id = _create_sale(
        api, admin_token,
        total_amount=total, discount=discount, tax_amount=tax, final_amount=final,
        product_id=product_id, qty=4, price=10.0,
    )
    approved = _approve_sale(api, admin_token, sale_id)
    assert approved["workflow_state"] == "approved"
    rows = db(
        "SELECT SUM(jl.debit), SUM(jl.credit) FROM journal_entry_lines jl "
        "WHERE jl.journal_entry_id = %s",
        (approved["journal_entry_id"],),
    )
    d, c = rows[0]
    assert abs(float(d) - float(c)) < 0.01
    # Revenue line must be net of VAT: final - tax = 3600 - 530.07
    rev_rows = db(
        """
        SELECT jl.debit, jl.credit, a.account_code
        FROM journal_entry_lines jl
        JOIN accounts a ON a.id = jl.account_id
        WHERE jl.journal_entry_id = %s AND a.account_code = '4110'
        """,
        (approved["journal_entry_id"],),
    )
    assert rev_rows
    credit = float(rev_rows[0][1])
    assert abs(credit - (final - tax)) < 0.01, f"revenue should be net of VAT: {credit}"


def test_negative_amounts_rejected(api, admin_token):
    payload = {
        "customer_id": 64,
        "total_amount": -5.0, "discount": 1.0, "final_amount": -4.0,
        "payment_method": "cash", "payment_status": "paid",
        "company_id": 1, "branch_id": 1, "tax_amount": 0,
        "items": [],
    }
    r = api("POST", "/sales", token=admin_token, data=payload)
    assert r["status"] == 400, f"negative amounts must be rejected: {r}"


def test_approve_twice_is_rejected(api, admin_token, product_id):
    sale_id = _create_sale(
        api, admin_token,
        total_amount=20.0, discount=0, tax_amount=0, final_amount=20.0,
        product_id=product_id, qty=1, price=20.0,
    )
    _approve_sale(api, admin_token, sale_id)
    r = api("POST", f"/sales/{sale_id}/approve", token=admin_token, data={})
    assert r["status"] == 400


def test_trial_balance_endpoint(api, admin_token):
    r = api("GET", "/accounting/trial-balance?per_page=500", token=admin_token)
    assert r["status"] == 200, f"trial balance failed: {r}"
    d = r["data"]
    total_dr = float(d.get("total_debit", 0))
    total_cr = float(d.get("total_credit", 0))
    assert d.get("is_balanced") is True, (
        f"trial balance reports unbalanced: dr={total_dr} cr={total_cr}"
    )
    assert abs(total_dr - total_cr) < 0.01


def _assert_balanced(db, entry_id, label):
    assert entry_id, f"{label}: missing journal_entry_id"
    rows = db(
        "SELECT SUM(jl.debit), SUM(jl.credit) FROM journal_entry_lines jl "
        "WHERE jl.journal_entry_id = %s",
        (entry_id,),
    )
    d, c = rows[0]
    assert abs(float(d) - float(c)) < 0.01, f"{label} entry {entry_id} unbalanced: d={d} c={c}"
    return entry_id


def test_customer_payment_posts_balanced_entry(api, admin_token, db):
    """payment.received: Dr Bank / Cr AR = amount."""
    r = api("POST", "/payments/customers", token=admin_token, data={
        "customer_id": 64, "amount": 250.0,
        "payment_method": "cash", "reference_number": "PY-TEST-CUST",
    })
    assert r["status"] == 200, f"customer payment failed: {r}"
    _assert_balanced(db, r["data"].get("journal_entry_id"), "customer payment")
    # Verify the payment row was linked within the backend transaction.
    rows = db(
        "SELECT journal_entry_id FROM customer_payments WHERE id = %s",
        (r["data"]["id"],),
    )
    assert rows and rows[0][0] == r["data"]["journal_entry_id"], (
        "customer_payments.journal_entry_id not linked"
    )


def test_supplier_payment_posts_balanced_entry(api, admin_token, db):
    """payment.made: Dr AP / Cr Bank = amount."""
    r = api("POST", "/payments/suppliers", token=admin_token, data={
        "supplier_id": 5, "amount": 180.0,
        "payment_method": "cash", "reference_number": "PY-TEST-SUPP",
    })
    assert r["status"] == 200, f"supplier payment failed: {r}"
    _assert_balanced(db, r["data"].get("journal_entry_id"), "supplier payment")
    rows = db(
        "SELECT journal_entry_id FROM supplier_payments WHERE id = %s",
        (r["data"]["id"],),
    )
    assert rows and rows[0][0] == r["data"]["journal_entry_id"], (
        "supplier_payments.journal_entry_id not linked"
    )


def test_sales_return_posts_balanced_entry(api, admin_token, db, product_id):
    """sales.return.approved: Dr Sales Returns + VAT Output / Cr AR = final."""
    r = api("POST", "/returns/sales", token=admin_token, data={
        "sale_id": None, "customer_id": 64, "reason": "pytest",
        "refund_method": "cash", "is_restocked": False,
        "tax_amount": 0.5, "total_amount": 10.0, "final_amount": 10.5,
        "items": [{"product_id": product_id, "quantity": 1,
                   "unit_price": 10.0, "total_price": 10.0, "tax_amount": 0.5}],
    })
    assert r["status"] == 200, f"sales return create failed: {r}"
    rid = r["data"]["id"]
    rr = api("POST", f"/returns/sales/{rid}/approve", token=admin_token, data={})
    assert rr["status"] == 200, f"sales return approve failed: {rr}"
    _assert_balanced(db, rr["data"].get("journal_entry_id"), "sales return")
    assert rr["data"]["message"] == "Sales return approved"


def test_purchase_return_posts_balanced_entry(api, admin_token, db, product_id):
    """purchase.return.approved: Dr AP / Cr COGS + VAT Input = final."""
    r = api("POST", "/returns/purchases", token=admin_token, data={
        "purchase_id": None, "supplier_id": 5, "reason": "pytest",
        "refund_method": "cash", "is_restocked": False,
        "tax_amount": 0.8, "total_amount": 20.0, "final_amount": 20.8,
        "items": [{"product_id": product_id, "quantity": 2,
                   "unit_cost": 10.0, "total_cost": 20.0, "tax_amount": 0.8}],
    })
    assert r["status"] == 200, f"purchase return create failed: {r}"
    rid = r["data"]["id"]
    rr = api("POST", f"/returns/purchases/{rid}/approve", token=admin_token, data={})
    assert rr["status"] == 200, f"purchase return approve failed: {rr}"
    _assert_balanced(db, rr["data"].get("journal_entry_id"), "purchase return")


def test_zero_amount_payment_is_rejected(api, admin_token):
    r = api("POST", "/payments/customers", token=admin_token, data={
        "customer_id": 64, "amount": 0, "payment_method": "cash",
    })
    assert r["status"] == 400, f"zero payment must be rejected: {r}"


def test_global_ledger_still_balanced_after_all_flows(db):
    total_dr = db("SELECT COALESCE(SUM(debit),0) FROM journal_entry_lines")[0][0]
    total_cr = db("SELECT COALESCE(SUM(credit),0) FROM journal_entry_lines")[0][0]
    assert abs(float(total_dr) - float(total_cr)) < 0.01, (
        f"global ledger drifted: dr={total_dr} cr={total_cr}"
    )


def test_purchase_with_discount_posts_balanced_entry(api, admin_token, db, product_id):
    """purchase.order.approved with legacy-style gross total & discount:
    Dr Inventory = final - VAT (net of VAT), Dr VAT Input = tax,
    Cr AP = final. Must balance regardless of discount convention."""
    import uuid

    po = api("POST", "/purchases", token=admin_token, data={
        "supplier_id": _supplier_id(db), "warehouse_id": 1, "order_date": "2026-09-08",
        "order_number": "PO-TEST-" + uuid.uuid4().hex[:6].upper(),
        "total_amount": 290.5, "discount": 20.0, "tax_amount": 15.08,
        "final_amount": 270.0,
        "items": [{"product_id": product_id, "quantity": 1,
                   "unit_cost": 290.5, "unit_price": 290.5,
                   "total_cost": 290.5, "total_price": 290.5,
                   "tax_amount": 15.08}],
    })
    assert po["status"] == 200, f"purchase create failed: {po}"
    oid = po["data"]["id"]

    r = api("POST", f"/purchases/{oid}/submit", token=admin_token, data={})
    assert r["status"] == 200, f"submit failed: {r}"
    r = api("POST", f"/purchases/{oid}/approve", token=admin_token, data={})
    assert r["status"] == 200, f"approve failed: {r}"
    entry_id = r["data"].get("journal_entry_id")
    assert entry_id, "approved purchase missing journal_entry_id"
    _assert_balanced(db, entry_id, "purchase order")

    # GRNI line (1303) must be net of VAT (final - tax) so the entry balances
    # even when total is gross and a discount applies. Inventory (1301) is only
    # debited on goods receipt, not on purchase approval (Phase-1 GRNI model).
    rows = db(
        """
        SELECT jl.debit, jl.credit
        FROM journal_entry_lines jl
        JOIN accounts a ON a.id = jl.account_id
        WHERE jl.journal_entry_id = %s AND a.account_code = '1303'
        """,
        (entry_id,),
    )
    assert rows, "purchase entry missing GRNI line"
    debit = float(rows[0][0])
    assert abs(debit - (270.0 - 15.08)) < 0.01, (
        f"GRNI should be net of VAT: {debit}"
    )


def test_login_lockout_after_failed_attempts(db):
    """5 failed logins lock the account; correct password is rejected while locked,
    and succeeds again after the lock is cleared."""
    import urllib.request
    import json
    import os

    api_base = os.getenv("ERP_API_BASE", "http://localhost:8001/api")

    def raw_login(pw):
        body = json.dumps({"username": "admin", "password": pw}).encode()
        req = urllib.request.Request(
            api_base + "/auth/login", data=body,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp.read()
                return resp.status
        except urllib.error.HTTPError as e:
            return e.code

    try:
        # Reset the counter so the test is deterministic.
        db("UPDATE users SET failed_login_attempts=0, locked_until=NULL WHERE username='admin'")
        for _ in range(5):
            assert raw_login("wrong-password") == 401
        assert raw_login("admin123") == 401, "correct password must be rejected while locked"
        # Simulate lock expiry / admin unlock.
        db("UPDATE users SET failed_login_attempts=0, locked_until=NULL WHERE username='admin'")
        assert raw_login("admin123") == 200
    finally:
        db("UPDATE users SET failed_login_attempts=0, locked_until=NULL WHERE username='admin'")


def test_rbac_denies_viewer_sensitive_writes(api, db):
    """RBAC: a viewer-role user must be refused on sensitive write endpoints
    (create sale, create journal, create user, bank reconcile) with 403."""
    import urllib.request
    import urllib.error
    import json
    import os
    import uuid

    api_base = os.getenv("ERP_API_BASE", "http://localhost:8001/api")

    # Admin creates a viewer-role test user (admin has MANAGE_USERS).
    uname = "rbac_" + uuid.uuid4().hex[:8]
    # Obtain an admin token via a fresh login.
    body = json.dumps({"username": "admin", "password": "admin123"}).encode()
    req = urllib.request.Request(
        api_base + "/auth/login", data=body,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        admin_tok = json.loads(resp.read())["access_token"]

    r = api("POST", "/settings/users", token=admin_tok, data={
        "username": uname, "password": "viewerpass1", "full_name": "RBAC viewer",
        "role": "viewer",
    })
    assert r["status"] == 200, f"failed to create viewer: {r}"

    body = json.dumps({"username": uname, "password": "viewerpass1"}).encode()
    req = urllib.request.Request(
        api_base + "/auth/login", data=body,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        viewer_tok = json.loads(resp.read())["access_token"]

    sensitive = [
        ("POST", "/sales", {"customer_id": 64, "items": []}),
        ("POST", "/purchases", {"supplier_id": _supplier_id(db), "items": []}),
        ("POST", "/settings/users", {"username": "nope", "role": "admin"}),
        ("POST", "/settings/companies", {"name": "nope"}),
        ("POST", "/accounting/journal-entries",
         {"entry_date": "2026-09-08", "lines": []}),
        ("POST", "/payments/customers", {"customer_id": 64, "amount": 1}),
        ("POST", "/bank-reconciliation/reconciliations", {"bank_id": 1}),
    ]
    for method, path, payload in sensitive:
        resp = api(method, path, token=viewer_tok, data=payload)
        assert resp["status"] == 403, (
            f"viewer should be denied {method} {path}, got {resp['status']}: {resp['data']}"
        )
    # Cleanup: deactivate the test viewer user.
    db("UPDATE users SET is_active=false WHERE username=%s", (uname,))