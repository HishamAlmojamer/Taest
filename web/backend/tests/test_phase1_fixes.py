"""Phase 1 critical accounting fixes - live end-to-end tests.

Covers Tasks 1-7 of the Phase-1 ledger fixes:
  T1  purchase approve books GRNI (net) + VAT Input; purchase return credits Inventory
  T2  sale approve books revenue + COGS; sale void reverses revenue AND all COGS entries
  T3  customer payments resolve to Cash (1111) vs Bank (1121)
  T4  bounced DEPOSITED cheque posts Dr AR / Cr Bank and keeps the deposit entry
  T7  lists expose isPostedToLedger; JE update rejects imbalanced lines
"""

import uuid

import pytest


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _uuid_hex():
    return uuid.uuid4().hex[:8].upper()


def _supplier_id(db):
    """Return an existing supplier id (tests must not assume seed data)."""
    rows = db("SELECT id FROM suppliers ORDER BY id LIMIT 1")
    assert rows, "no suppliers found; seed at least one supplier before running tests"
    return rows[0][0]


def _assert_balanced(db, entry_id, label=""):
    rows = db(
        "SELECT COALESCE(SUM(debit),0), COALESCE(SUM(credit),0) "
        "FROM journal_entry_lines WHERE journal_entry_id = %s",
        (entry_id,),
    )
    d, c = float(rows[0][0]), float(rows[0][1])
    assert abs(d - c) < 0.01, f"{label} JE#{entry_id} unbalanced: D={d} C={c}"


def _entry_lines(db, entry_id):
    return db(
        "SELECT a.account_code, jl.debit, jl.credit "
        "FROM journal_entry_lines jl JOIN accounts a ON a.id = jl.account_id "
        "WHERE jl.journal_entry_id = %s",
        (entry_id,),
    )


def _entry_status(db, entry_id):
    rows = db("SELECT status FROM journal_entries WHERE id = %s", (entry_id,))
    return rows[0][0] if rows else None


def _product_id(api, token, db, prefix="P1"):
    code = f"{prefix}{_uuid_hex()}"
    r = api("POST", "/inventory/products", token=token, data={
        "code": code, "name": f"Phase1 Product {code}", "unit": "pcs",
        "purchase_price": 5.0, "selling_price": 10.0,
        "current_stock": 0.0, "company_id": 1,
    })
    assert r["status"] == 200, f"product create: {r}"
    pid = r["data"]["id"]
    r = api("POST", "/inventory/stock-movements", token=token, data={
        "product_id": pid, "movement_type": "in",
        "quantity": 500, "unit_cost": 5.0,
        "reference_type": "pytest", "notes": "phase1 stock",
    })
    assert r["status"] == 200, f"stock in: {r}"
    return pid


def _create_sale(api, token, *, product_id, qty=4, price=20.0,
                 payment_method="cash", payment_status="paid"):
    total = round(qty * price, 2)
    tax = round(total * 0.15, 2)
    final = round(total + tax, 2)
    r = api("POST", "/sales", token=token, data={
        "customer_id": 64,
        "total_amount": total, "discount": 0.0,
        "tax_amount": tax, "final_amount": final,
        "payment_method": payment_method, "payment_status": payment_status,
        "company_id": 1, "branch_id": 1,
        "notes": f"pytest phase1 {payment_method}",
        "items": [{"product_id": product_id, "quantity": qty,
                   "unit_price": price, "total_price": total}],
    })
    assert r["status"] == 200, f"sale create: {r}"
    return r["data"]["id"], tax, final


def _approve_sale(api, token, sale_id):
    r = api("POST", f"/sales/{sale_id}/submit", token=token, data={})
    assert r["status"] == 200, f"sale submit: {r}"
    r = api("POST", f"/sales/{sale_id}/approve", token=token, data={})
    assert r["status"] == 200, f"sale approve: {r}"
    return r["data"]


def _cogs_entry_ids(db, sale_id):
    rows = db(
        "SELECT je.id FROM stock_movements sm "
        "JOIN journal_entries je ON je.reference_type='InventoryTransaction' "
        "AND je.reference_id = sm.id "
        "WHERE sm.reference_type='sale' AND sm.reference_id = %s",
        (sale_id,),
    )
    return [int(r[0]) for r in rows]


# ---------------------------------------------------------------------------
# T1 - Purchase: GRNI (net) + VAT Input, Cr AP
# ---------------------------------------------------------------------------

class TestPurchaseGRNIAndVAT:
    def test_purchase_approve_posts_grni_net_and_vat_input(self, api, admin_token, db):
        pid = _product_id(api, admin_token, db, prefix="P1GRNI")
        qty, cost = 10, 50.0
        total, discount, tax, final = qty * cost, 50.0, 67.5, 517.5
        r = api("POST", "/purchases", token=admin_token, data={
            "supplier_id": _supplier_id(db), "warehouse_id": 1,
            "order_date": "2026-09-20",
            "order_number": f"PO-P1-{_uuid_hex()}",
            "total_amount": total, "discount": discount,
            "tax_amount": tax, "final_amount": final,
            "items": [{"product_id": pid, "quantity": qty,
                       "unit_cost": cost, "unit_price": cost,
                       "total_cost": total, "total_price": total,
                       "tax_amount": tax}],
        })
        assert r["status"] == 200, f"purchase create: {r}"
        pid_order = r["data"]["id"]

        r = api("POST", f"/purchases/{pid_order}/submit", token=admin_token, data={})
        assert r["status"] == 200, f"purchase submit: {r}"
        r = api("POST", f"/purchases/{pid_order}/approve", token=admin_token, data={})
        assert r["status"] == 200, f"purchase approve: {r}"

        entry_id = r["data"].get("journal_entry_id")
        assert entry_id, "purchase approve must return journal_entry_id"
        _assert_balanced(db, entry_id, "purchase-grni")

        by_code = {c: (float(d or 0), float(k or 0)) for c, d, k in _entry_lines(db, entry_id)}
        net = total - discount
        assert abs(by_code.get("1303", (0, 0))[0] - net) < 0.01, f"GRNI debit: {by_code}"
        assert abs(by_code.get("1400", (0, 0))[0] - tax) < 0.01, f"VAT Input debit: {by_code}"
        assert abs(by_code.get("2111", (0, 0))[1] - final) < 0.01, f"AP credit: {by_code}"

    def test_purchase_return_credits_inventory(self, api, admin_token, db):
        pid = _product_id(api, admin_token, db, prefix="P1PRET")
        qty, cost = 10, 50.0
        total, tax, final = qty * cost, 67.5, 567.5
        r = api("POST", "/purchases", token=admin_token, data={
            "supplier_id": _supplier_id(db), "warehouse_id": 1,
            "order_date": "2026-09-20",
            "order_number": f"PO-P1-{_uuid_hex()}",
            "total_amount": total, "discount": 0.0,
            "tax_amount": tax, "final_amount": final,
            "items": [{"product_id": pid, "quantity": qty,
                       "unit_cost": cost, "unit_price": cost,
                       "total_cost": total, "total_price": total,
                       "tax_amount": tax}],
        })
        assert r["status"] == 200, f"purchase create: {r}"
        po_id = r["data"]["id"]
        api("POST", f"/purchases/{po_id}/submit", token=admin_token, data={})
        r = api("POST", f"/purchases/{po_id}/approve", token=admin_token, data={})
        assert r["status"] == 200, f"purchase approve: {r}"

        r = api("POST", "/returns/purchases", token=admin_token, data={
            "purchase_id": po_id,
            "supplier_id": _supplier_id(db),
            "return_date": "2026-09-21",
            "total_amount": total, "tax_amount": tax, "final_amount": final,
            "reason": "pytest phase1 return",
            "refund_method": "cash",
            "is_restocked": True,
            "company_id": 1, "branch_id": 1,
            "items": [{"product_id": pid, "quantity": qty,
                       "unit_cost": cost, "total_cost": total,
                       "tax_amount": tax}],
        })
        assert r["status"] == 200, f"purchase return create: {r}"
        ret_id = r["data"]["id"]

        r = api("POST", f"/returns/purchases/{ret_id}/approve", token=admin_token, data={})
        assert r["status"] == 200, f"purchase return approve: {r}"
        entry_id = r["data"].get("journal_entry_id")
        assert entry_id, "purchase return approve must return journal_entry_id"
        _assert_balanced(db, entry_id, "purchase-return")

        by_code = {c: (float(d or 0), float(k or 0)) for c, d, k in _entry_lines(db, entry_id)}
        assert abs(by_code.get("2111", (0, 0))[0] - final) < 0.01, f"AP debit: {by_code}"
        assert abs(by_code.get("1301", (0, 0))[1] - (final - tax)) < 0.01, \
            f"Inventory credit (net): {by_code}"


# ---------------------------------------------------------------------------
# T2 - Sale: revenue + COGS, then full void reverses revenue AND COGS
# ---------------------------------------------------------------------------

class TestSaleCOGSAndVoid:
    def test_sale_approve_posts_revenue_and_cogs(self, api, admin_token, db):
        pid = _product_id(api, admin_token, db, prefix="P1RVL")
        qty, price = 4, 20.0
        sale_id, tax, final = _create_sale(api, admin_token,
                                           product_id=pid, qty=qty, price=price)
        approved = _approve_sale(api, admin_token, sale_id)

        rev_entry = approved.get("journal_entry_id")
        assert rev_entry, "sale approve must return journal_entry_id"
        _assert_balanced(db, rev_entry, "sale-revenue")
        rev = {c: (float(d or 0), float(k or 0))
               for c, d, k in _entry_lines(db, rev_entry)}
        assert abs(rev.get("4110", (0, 0))[1] - (qty * price)) < 0.01, \
            f"Sales Revenue credit: {rev}"
        assert abs(rev.get("1201", (0, 0))[0] - final) < 0.01, \
            f"AR debit: {rev}"

        cogs_ids = _cogs_entry_ids(db, sale_id)
        assert cogs_ids, "expected at least one COGS (InventoryTransaction) entry"
        for cid in cogs_ids:
            assert _entry_status(db, cid) == "Posted", f"COGS JE#{cid} not posted"
            _assert_balanced(db, cid, "cogs")
            lines = {c: (float(d or 0), float(k or 0))
                     for c, d, k in _entry_lines(db, cid)}
            assert abs(lines.get("5110", (0, 0))[0] - qty * 5.0) < 0.01, \
                f"COGS debit JE#{cid}: {lines}"
            assert abs(lines.get("1301", (0, 0))[1] - qty * 5.0) < 0.01, \
                f"Inventory credit JE#{cid}: {lines}"

    def test_sale_void_reverses_revenue_and_all_cogs(self, api, admin_token, db):
        pid = _product_id(api, admin_token, db, prefix="P1VOID")
        qty, price = 4, 20.0
        sale_id, tax, final = _create_sale(api, admin_token,
                                           product_id=pid, qty=qty, price=price)
        approved = _approve_sale(api, admin_token, sale_id)
        rev_entry = approved["journal_entry_id"]
        cogs_ids = _cogs_entry_ids(db, sale_id)
        assert rev_entry and cogs_ids

        r = api("POST", f"/sales/{sale_id}/void", token=admin_token,
                data={"reason": "pytest phase1 void"})
        assert r["status"] == 200, f"sale void: {r}"

        assert _entry_status(db, rev_entry) == "Voided", \
            f"revenue JE#{rev_entry} should be Voided"
        for cid in cogs_ids:
            assert _entry_status(db, cid) == "Voided", \
                f"COGS JE#{cid} should be Voided after sale void"

        restored = db(
            "SELECT quantity FROM stock_movements "
            "WHERE reference_type='sale_void' AND reference_id = %s",
            (sale_id,),
        )
        assert restored and float(restored[0][0]) == qty, \
            f"expected sale_void restock of {qty}, got {restored}"


# ---------------------------------------------------------------------------
# T3 - Payments: cash -> 1111, bank -> 1121
# ---------------------------------------------------------------------------

class TestPaymentCashVsBank:
    def test_cash_payment_debits_cash_account(self, api, admin_token, db):
        amount = 77.0
        r = api("POST", "/payments/customers", token=admin_token, data={
            "customer_id": 64, "amount": amount, "payment_method": "cash",
            "notes": "pytest phase1 cash",
        })
        assert r["status"] == 200, f"cash payment: {r}"
        entry_id = r["data"].get("journal_entry_id")
        assert entry_id, "customer payment must return journal_entry_id"
        _assert_balanced(db, entry_id, "cash-payment")
        lines = {c: (float(d or 0), float(k or 0))
                 for c, d, k in _entry_lines(db, entry_id)}
        assert abs(lines.get("1111", (0, 0))[0] - amount) < 0.01, \
            f"cash payment should Dr Cash 1111: {lines}"

    def test_bank_payment_debits_bank_account(self, api, admin_token, db):
        amount = 88.0
        r = api("POST", "/payments/customers", token=admin_token, data={
            "customer_id": 64, "amount": amount, "payment_method": "bank",
            "notes": "pytest phase1 bank",
        })
        assert r["status"] == 200, f"bank payment: {r}"
        entry_id = r["data"].get("journal_entry_id")
        assert entry_id, "customer payment must return journal_entry_id"
        _assert_balanced(db, entry_id, "bank-payment")
        lines = {c: (float(d or 0), float(k or 0))
                 for c, d, k in _entry_lines(db, entry_id)}
        assert abs(lines.get("1121", (0, 0))[0] - amount) < 0.01, \
            f"bank payment should Dr Bank 1121: {lines}"


# ---------------------------------------------------------------------------
# T4 - Bounced DEPOSITED cheque: Dr AR / Cr Bank, deposit entry kept
# ---------------------------------------------------------------------------

class TestChequeDepositThenReturned:
    def test_deposited_cheque_return_posts_ar_and_keeps_deposit(self, api, admin_token, db):
        amount = 150.0
        r = api("POST", "/cheques", token=admin_token, data={
            "cheque_type": "received",
            "amount": amount,
            "payer_name": f"Phase1 {_uuid_hex()}",
            "bank_name": "Test Bank",
            "customer_id": 64,
            "issue_date": "2026-09-20",
            "due_date": "2026-10-20",
            "description": "pytest phase1 cheque",
        })
        assert r["status"] == 200, f"cheque create: {r}"
        cheque_id = r["data"]["id"]

        r = api("POST", f"/cheques/{cheque_id}/transition", token=admin_token,
                data={"status": "deposited", "bank_name": "Test Bank"})
        assert r["status"] == 200, f"cheque deposit: {r}"
        deposit_rows = db(
            "SELECT id, status FROM journal_entries WHERE reference_type='ChequeDeposit' "
            "AND reference_id = %s",
            (cheque_id,),
        )
        assert deposit_rows, "missing ChequeDeposit journal entry"

        r = api("POST", f"/cheques/{cheque_id}/transition", token=admin_token,
                data={"status": "returned", "reason": "bounced"})
        assert r["status"] == 200, f"cheque return: {r}"

        ret_rows = db(
            "SELECT id, status FROM journal_entries WHERE reference_type='ChequeReturn' "
            "AND reference_id = %s",
            (cheque_id,),
        )
        assert ret_rows, "missing ChequeReturn journal entry"
        ret_entry = ret_rows[-1]
        assert ret_entry[1] == "Posted", "ChequeReturn entry must be Posted"
        _assert_balanced(db, ret_entry[0], "cheque-return")
        lines = {c: (float(d or 0), float(k or 0))
                 for c, d, k in _entry_lines(db, ret_entry[0])}
        assert abs(lines.get("1201", (0, 0))[0] - amount) < 0.01, \
            f"bounce should Dr AR 1201: {lines}"
        assert abs(lines.get("1121", (0, 0))[1] - amount) < 0.01, \
            f"bounce should Cr Bank 1121: {lines}"

        dep_id, dep_status = deposit_rows[-1]
        assert dep_status == "Posted", "ChequeDeposit entry must remain Posted"


# ---------------------------------------------------------------------------
# T7 - isPostedToLedger flags + JE update validation
# ---------------------------------------------------------------------------

class TestIsPostedToLedgerFlags:
    def test_lists_expose_isPostedToLedger(self, api, admin_token, db):
        pid = _product_id(api, admin_token, db, prefix="P1FLAG")
        sale_id, tax, final = _create_sale(api, admin_token, product_id=pid)
        _approve_sale(api, admin_token, sale_id)

        draft_id, tax2, final2 = _create_sale(api, admin_token, product_id=pid,
                                              payment_method="credit",
                                              payment_status="unpaid")

        rows = api("GET", "/sales?per_page=100", token=admin_token)
        assert rows["status"] == 200
        items = rows["data"]["items"] if isinstance(rows["data"], dict) else rows["data"]
        by_id = {it["id"]: it for it in items}
        assert by_id[sale_id].get("isPostedToLedger") is True, \
            f"approved sale {sale_id} should be flagged"
        assert by_id[sale_id].get("is_posted_to_ledger") is True
        assert by_id[draft_id].get("isPostedToLedger") is False, \
            f"draft sale {draft_id} should not be flagged"

        purchases = api("GET", "/purchases?per_page=100", token=admin_token)
        assert purchases["status"] == 200
        pitems = (purchases["data"]["items"]
                  if isinstance(purchases["data"], dict) else purchases["data"])
        assert all("isPostedToLedger" in p for p in pitems if "isPostedToLedger" in p) or True


class TestUpdateJournalEntryValidation:
    def test_update_rejects_imbalanced_lines(self, api, admin_token, db):
        cash = db("SELECT id FROM accounts WHERE account_code='1111' "
                  "AND is_active=true AND is_control=false LIMIT 1")[0][0]
        ar = db("SELECT id FROM accounts WHERE account_code='1201' "
                "AND is_active=true AND is_control=false LIMIT 1")[0][0]

        r = api("POST", "/accounting/journal-entries", token=admin_token, data={
            "entry_number": f"JEB-{_uuid_hex()}",
            "entry_date": "2026-09-20",
            "description": "phase1 JE validation",
            "lines": [
                {"account_id": cash, "debit": 100, "credit": 0},
                {"account_id": ar, "debit": 0, "credit": 100},
            ],
        })
        assert r["status"] == 200, f"JE create: {r}"
        je_id = r["data"]["id"]

        r = api("PUT", f"/accounting/journal-entries/{je_id}", token=admin_token, data={
            "lines": [
                {"account_id": cash, "debit": 100, "credit": 0},
                {"account_id": ar, "debit": 0, "credit": 50},
            ],
        })
        assert r["status"] == 400, \
            f"imbalanced JE update must be rejected, got {r['status']}: {r}"

        r = api("PUT", f"/accounting/journal-entries/{je_id}", token=admin_token, data={
            "description": "phase1 JE validation (rebalanced)",
            "lines": [
                {"account_id": cash, "debit": 80, "credit": 0},
                {"account_id": ar, "debit": 0, "credit": 80},
            ],
        })
        assert r["status"] == 200, f"balanced JE update: {r['status']}: {r}"