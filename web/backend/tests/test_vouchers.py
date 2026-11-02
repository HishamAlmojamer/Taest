"""
End-to-end tests for accounting vouchers (سندات القبض والصرف) and the combined
المدينون والدائنون (debtors & creditors) report.

Each test talks to the live backend API (fixtures in conftest) and asserts the
posted ledger effect directly through SQL. Voucher/journal rows are wiped by
the session cleanup fixture; customers/suppliers created here are deleted in a
teardown so repeated runs never accumulate entities.
"""

import pytest


def _create_customer(api, admin_token, db, name="Voucher Test Customer"):
    r = api("POST", "/crm/customers", token=admin_token, data={"name": name, "currency": "SAR"})
    assert r["status"] == 200, r
    return r["data"]["id"]


def _create_supplier(api, admin_token, db, name="Voucher Test Supplier"):
    r = api("POST", "/crm/suppliers", token=admin_token, data={"name": name, "currency": "SAR"})
    assert r["status"] == 200, r
    return r["data"]["id"]


def _cleanup_customer(db, cust_id):
    if not cust_id:
        return
    try:
        db("DELETE FROM customer_loyalty WHERE customer_id=%s", (cust_id,))
    except Exception:
        pass
    db("DELETE FROM customers WHERE id=%s", (cust_id,))


def _cleanup_supplier(db, supp_id):
    if not supp_id:
        return
    try:
        db("DELETE FROM supplier_contacts WHERE supplier_id=%s", (supp_id,))
    except Exception:
        pass
    db("DELETE FROM suppliers WHERE id=%s", (supp_id,))


def _line_codes(db, entry_id):
    """Return {account_code: {'db': float, 'cr': float}} for a posted entry."""
    rows = db(
        "SELECT a.account_code, jl.debit, jl.credit "
        "FROM journal_entry_lines jl JOIN accounts a ON a.id = jl.account_id "
        "WHERE jl.journal_entry_id = %s ORDER BY a.account_code",
        (entry_id,),
    )
    out = {}
    for code, debit, credit in rows:
        out[code] = {"db": float(debit or 0), "cr": float(credit or 0)}
    return out


def test_receipt_voucher_posts_cash_entry(api, db, admin_token):
    cust_id = _create_customer(api, admin_token, db)
    try:
        r = api("POST", "/accounting/vouchers", token=admin_token, data={
            "voucher_type": "RECEIPT", "partner_type": "customer",
            "partner_id": cust_id, "amount": 150.50, "payment_method": "cash",
            "description": "test سند قبض",
        })
        assert r["status"] == 200, r
        v = r["data"]["voucher"]
        assert v["status"] == "Posted"
        assert v["voucher_number"].startswith("RC-")
        assert v["journal_entry_id"]

        je = api("GET", f"/accounting/journal-entries/{v['journal_entry_id']}", token=admin_token)
        assert je["status"] == 200, je
        assert je["data"]["entry_number"].startswith("JE-")
        assert je["data"]["reference_type"] == "ReceiptVoucher"

        codes = _line_codes(db, v["journal_entry_id"])
        assert set(codes) == {"1111", "1201"}
        assert codes["1111"]["db"] == pytest.approx(150.50)
        assert codes["1201"]["cr"] == pytest.approx(150.50)

        bal = db("SELECT current_balance FROM customers WHERE id=%s", (cust_id,))[0][0]
        assert float(bal) == pytest.approx(-150.50)
    finally:
        _cleanup_customer(db, cust_id)


def test_payment_voucher_debits_supplier_via_bank(api, db, admin_token):
    supp_id = _create_supplier(api, admin_token, db)
    try:
        r = api("POST", "/accounting/vouchers", token=admin_token, data={
            "voucher_type": "PAYMENT", "partner_type": "supplier",
            "partner_id": supp_id, "amount": 75.25, "payment_method": "bank",
            "description": "test سند صرف",
        })
        assert r["status"] == 200, r
        v = r["data"]["voucher"]
        assert v["voucher_number"].startswith("PV-")
        assert v["journal_entry_id"]

        codes = _line_codes(db, v["journal_entry_id"])
        assert set(codes) == {"1121", "2111"}
        assert codes["2111"]["db"] == pytest.approx(75.25)
        assert codes["1121"]["cr"] == pytest.approx(75.25)

        bal = db("SELECT current_balance FROM suppliers WHERE id=%s", (supp_id,))[0][0]
        assert float(bal) == pytest.approx(-75.25)
    finally:
        _cleanup_supplier(db, supp_id)


def test_void_voucher_creates_reversal_and_restores_balance(api, db, admin_token):
    cust_id = _create_customer(api, admin_token, db)
    try:
        r = api("POST", "/accounting/vouchers", token=admin_token, data={
            "voucher_type": "RECEIPT", "partner_type": "customer",
            "partner_id": cust_id, "amount": 90.00, "payment_method": "cash",
        })
        assert r["status"] == 200, r
        v = r["data"]["voucher"]
        assert float(db("SELECT current_balance FROM customers WHERE id=%s", (cust_id,))[0][0]) == pytest.approx(-90.00)

        vr = api("POST", f"/accounting/vouchers/{v['id']}/void?reason=test%20void", token=admin_token)
        assert vr["status"] == 200, vr
        assert vr["data"]["voucher"]["status"] == "Voided"
        rev_id = vr["data"]["reversal_entry_id"]
        assert rev_id

        rev_je = api("GET", f"/accounting/journal-entries/{rev_id}", token=admin_token)
        assert rev_je["status"] == 200, rev_je
        assert rev_je["data"]["reference_type"] == "VoucherReversal"

        # Reversal swaps debit/credit compared with the original entry.
        orig = _line_codes(db, v["journal_entry_id"])
        rev_lines = db(
            "SELECT account_id, debit, credit FROM journal_entry_lines WHERE journal_entry_id=%s", (rev_id,)
        )
        assert len(rev_lines) == 2
        rev_tot = sum((float(x[1] or 0) - float(x[2] or 0)) for x in rev_lines)
        assert abs(rev_tot) < 1e-6
        # Customer balance restored to zero.
        bal = float(db("SELECT current_balance FROM customers WHERE id=%s", (cust_id,))[0][0])
        assert abs(bal) < 1e-6
    finally:
        _cleanup_customer(db, cust_id)


def test_voucher_void_requires_reason(api, db, admin_token):
    cust_id = _create_customer(api, admin_token, db)
    try:
        r = api("POST", "/accounting/vouchers", token=admin_token, data={
            "voucher_type": "RECEIPT", "partner_type": "customer",
            "partner_id": cust_id, "amount": 10.00, "payment_method": "cash",
        })
        assert r["status"] == 200, r
        v = r["data"]["voucher"]
        vr = api("POST", f"/accounting/vouchers/{v['id']}/void?reason=", token=admin_token)
        assert vr["status"] in (400, 422), vr
    finally:
        try:
            db("DELETE FROM customer_loyalty WHERE customer_id=%s", (cust_id,))
            db("DELETE FROM customers WHERE id=%s", (cust_id,))
        except Exception:
            pass


def test_debtors_creditors_report(api, db, admin_token):
    cust_id = _create_customer(api, admin_token, db)
    supp_id = _create_supplier(api, admin_token, db)
    try:
        db("UPDATE customers SET current_balance = 350.75 WHERE id=%s", (cust_id,))
        db("UPDATE suppliers SET current_balance = 125.50 WHERE id=%s", (supp_id,))

        r = api("GET", "/aging-reports/debtors-creditors", token=admin_token)
        assert r["status"] == 200, r
        d = r["data"]
        assert "debtors" in d and "creditors" in d and "ledger" in d

        debtor_ids = [x["id"] for x in d["debtors"]["items"]]
        assert cust_id in debtor_ids
        row = next(x for x in d["debtors"]["items"] if x["id"] == cust_id)
        assert row["outstanding"] == pytest.approx(350.75)

        creditor_ids = [x["id"] for x in d["creditors"]["items"]]
        assert supp_id in creditor_ids

        assert d["ledger"]["ar_balance"] is not None
        assert d["ledger"]["ap_balance"] is not None
        # Debtors total == sum of items; creditors total == sum of items.
        assert d["debtors"]["total"] == pytest.approx(sum(x["outstanding"] for x in d["debtors"]["items"]))
        assert d["creditors"]["total"] == pytest.approx(sum(x["outstanding"] for x in d["creditors"]["items"]))
    finally:
        _cleanup_customer(db, cust_id)
        _cleanup_supplier(db, supp_id)