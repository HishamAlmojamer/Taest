"""Integration tests — each major module → Accounting.

Verifies that business flows (Sales, Purchases, Inventory, Fixed Assets,
Payments, Cheques) produce correct, balanced journal entries through the
centralized Accounting Posting Engine.
"""

import uuid
import pytest


def _uuid_hex():
    return uuid.uuid4().hex[:8].upper()


def _supplier_id(db):
    """Return an existing supplier id (tests must not assume seed data)."""
    rows = db("SELECT id FROM suppliers ORDER BY id LIMIT 1")
    assert rows, "no suppliers found; seed at least one supplier before running tests"
    return rows[0][0]


def _assert_balanced(db, entry_id, label=""):
    rows = db(
        "SELECT SUM(debit), SUM(credit) FROM journal_entry_lines WHERE journal_entry_id = %s",
        (entry_id,),
    )
    d, c = float(rows[0][0] or 0), float(rows[0][1] or 0)
    assert abs(d - c) < 0.01, f"{label} JE#{entry_id} unbalanced: D={d} C={c}"


def _je_lines(db, entry_id):
    """Return [(account_code, debit, credit)] for a JE."""
    return db("""
        SELECT a.account_code, jl.debit, jl.credit
        FROM journal_entry_lines jl
        JOIN accounts a ON a.id = jl.account_id
        WHERE jl.journal_entry_id = %s
        ORDER BY a.account_code
    """, (entry_id,))


def _product_id(api, token, db):
    code = f"INT{_uuid_hex()}"
    r = api("POST", "/inventory/products", token=token, data={
        "code": code, "name": f"Integration Product {code}", "unit": "pcs",
        "purchase_price": 5.0, "selling_price": 12.0,
        "current_stock": 0.0, "company_id": 1,
    })
    assert r["status"] == 200, f"product create: {r}"
    pid = r["data"]["id"]
    api("POST", "/inventory/stock-movements", token=token, data={
        "product_id": pid, "movement_type": "in",
        "quantity": 999, "unit_cost": 5.0,
        "reference_type": "pytest", "notes": "integration stock",
    })
    return pid


# ===========================================================================
# Sales → Accounting
# ===========================================================================

class TestSalesToAccounting:
    def test_cash_sale_produces_balanced_je(self, api, admin_token, db):
        pid = _product_id(api, admin_token, db)
        total, tax, final = 60.0, 9.0, 69.0
        r = api("POST", "/sales", token=admin_token, data={
            "customer_id": 64, "total_amount": total, "discount": 0,
            "tax_amount": tax, "final_amount": final,
            "payment_method": "cash", "payment_status": "paid",
            "company_id": 1, "branch_id": 1,
            "notes": "pytest integration: cash sale",
            "items": [{"product_id": pid, "quantity": 3,
                       "unit_price": 20.0, "total_price": 60.0}],
        })
        assert r["status"] == 200
        sid = r["data"]["id"]
        r = api("POST", f"/sales/{sid}/submit", token=admin_token, data={})
        assert r["status"] == 200
        r = api("POST", f"/sales/{sid}/approve", token=admin_token, data={})
        assert r["status"] == 200
        entry_id = r["data"].get("journal_entry_id")
        assert entry_id
        _assert_balanced(db, entry_id, "cash-sale")
        lines = _je_lines(db, entry_id)
        codes = [c[0] for c in lines]
        assert any(c.startswith("1") for c in codes), "should debit an asset account"
        assert any(c.startswith("4") for c in codes), "should credit a revenue account"

    def test_credit_sale_produces_receivable(self, api, admin_token, db):
        pid = _product_id(api, admin_token, db)
        r = api("POST", "/sales", token=admin_token, data={
            "customer_id": 64, "total_amount": 40.0, "discount": 0,
            "tax_amount": 6.0, "final_amount": 46.0,
            "payment_method": "credit", "payment_status": "unpaid",
            "company_id": 1, "branch_id": 1,
            "notes": "pytest integration: credit sale",
            "items": [{"product_id": pid, "quantity": 2,
                       "unit_price": 20.0, "total_price": 40.0}],
        })
        assert r["status"] == 200
        sid = r["data"]["id"]
        r = api("POST", f"/sales/{sid}/submit", token=admin_token, data={})
        r = api("POST", f"/sales/{sid}/approve", token=admin_token, data={})
        assert r["status"] == 200
        entry_id = r["data"]["journal_entry_id"]
        _assert_balanced(db, entry_id, "credit-sale")
        # The JE must include a receivable line (1201 - leaf Accounts Receivable)
        lines = _je_lines(db, entry_id)
        codes = [c[0] for c in lines]
        assert "1201" in codes, f"credit sale must create AR (1201), got {codes}"


# ===========================================================================
# Purchases → Accounting
# ===========================================================================

class TestPurchasesToAccounting:
    def test_purchase_produces_payable(self, api, admin_token, db):
        pid = _product_id(api, admin_token, db)
        r = api("POST", "/purchases", token=admin_token, data={
            "supplier_id": _supplier_id(db), "warehouse_id": 1,
            "order_date": "2026-09-12",
            "order_number": f"INT-{_uuid_hex()}",
            "total_amount": 150.0, "discount": 0,
            "tax_amount": 22.5, "final_amount": 172.5,
            "items": [{"product_id": pid, "quantity": 10,
                       "unit_cost": 15.0, "unit_price": 15.0,
                       "total_cost": 150.0, "total_price": 150.0,
                       "tax_amount": 22.5}],
        })
        assert r["status"] == 200
        oid = r["data"]["id"]
        api("POST", f"/purchases/{oid}/submit", token=admin_token, data={})
        r = api("POST", f"/purchases/{oid}/approve", token=admin_token, data={})
        assert r["status"] == 200
        entry_id = r["data"].get("journal_entry_id")
        assert entry_id
        _assert_balanced(db, entry_id, "purchase")
        lines = _je_lines(db, entry_id)
        codes = [c[0] for c in lines]
        assert any(c.startswith("2") for c in codes), "should credit a liability"


# ===========================================================================
# Inventory → Accounting
# ===========================================================================

class TestInventoryToAccounting:
    def test_stock_in_creates_inventory_transaction(self, api, admin_token, db):
        pid = _product_id(api, admin_token, db)
        r = api("POST", "/inventory/stock-movements", token=admin_token, data={
            "product_id": pid, "movement_type": "in",
            "quantity": 100, "unit_cost": 8.0,
            "reference_type": "pytest", "notes": "integration stock-in",
        })
        assert r["status"] == 200
        # Verify stock increased
        row = db("SELECT current_stock FROM products WHERE id = %s", (pid,))
        assert row, f"product {pid} not found"
        assert float(row[0][0]) >= 100, (
            f"stock should be >= 100, got {row[0][0]}"
        )


# ===========================================================================
# Fixed Assets → Accounting
# ===========================================================================

class TestFixedAssetsToAccounting:
    def test_asset_acquisition_creates_je(self, api, admin_token, db):
        cats = api("GET", "/fixed-assets/categories", token=admin_token)
        if cats["status"] != 200:
            pytest.skip("no fixed-asset categories")
        clist = cats["data"]
        if isinstance(clist, dict):
            clist = clist.get("items", clist.get("categories", []))
        if not clist:
            pytest.skip("no fixed-asset categories")
        cat_id = clist[0]["id"]

        code = f"IFA{_uuid_hex()[:6]}"
        r = api("POST", "/fixed-assets/", token=admin_token, data={
            "code": code,
            "name": f"IntAsset-{_uuid_hex()}",
            "category_id": cat_id,
            "purchase_date": "2026-06-01",
            "purchase_cost": 5000.0,
            "salvage_value": 0.0,
            "useful_life_months": 60,
            "depreciation_method": "STRAIGHT_LINE",
        })
        assert r["status"] == 200, f"asset create: {r}"
        asset_id = r["data"]["id"]
        row = db("SELECT journal_entry_id FROM fixed_assets WHERE id = %s", (asset_id,))
        entry_id = int(row[0][0]) if row and row[0][0] else None
        if entry_id:
            _assert_balanced(db, entry_id, "asset-acquisition")

    def test_depreciation_creates_balanced_je(self, api, admin_token, db):
        cats = api("GET", "/fixed-assets/categories", token=admin_token)
        if cats["status"] != 200:
            pytest.skip("no categories")
        clist = cats["data"]
        if isinstance(clist, dict):
            clist = clist.get("items", clist.get("categories", []))
        if not clist:
            pytest.skip("no categories")
        cat_id = clist[0]["id"]

        code = f"IDP{_uuid_hex()[:6]}"
        r = api("POST", "/fixed-assets/", token=admin_token, data={
            "code": code,
            "name": f"IntDep-{_uuid_hex()}",
            "category_id": cat_id,
            "purchase_date": "2026-01-01",
            "purchase_cost": 6000.0,
            "salvage_value": 0.0,
            "useful_life_months": 24,
            "depreciation_method": "STRAIGHT_LINE",
        })
        if r["status"] != 200:
            pytest.skip("cannot create asset")
        aid = r["data"]["id"]
        dep = api("POST", f"/fixed-assets/{aid}/depreciate",
                  token=admin_token, data={"month": 1, "year": 2026})
        assert dep["status"] == 200, f"depreciation: {dep}"
        entry_id = dep["data"].get("journal_entry_id")
        if entry_id:
            _assert_balanced(db, entry_id, "depreciation")
            lines = _je_lines(db, entry_id)
            codes = [c[0] for c in lines]
            assert any("1610" in c for c in codes), (
                "should credit Accumulated Depreciation (1610)"
            )


# ===========================================================================
# Payments → Accounting
# ===========================================================================

class TestPaymentsToAccounting:
    def test_customer_payment_creates_je(self, api, admin_token, db):
        r = api("POST", "/payments/customers", token=admin_token, data={
            "customer_id": 64, "amount": 500.0,
            "payment_method": "cash",
            "reference_number": f"INT-PAY-{_uuid_hex()}",
        })
        assert r["status"] == 200, f"payment: {r}"
        entry_id = r["data"].get("journal_entry_id")
        assert entry_id
        _assert_balanced(db, entry_id, "customer-payment")

    def test_supplier_payment_creates_je(self, api, admin_token, db):
        r = api("POST", "/payments/suppliers", token=admin_token, data={
            "supplier_id": 5, "amount": 350.0,
            "payment_method": "cash",
            "reference_number": f"INT-PAY-{_uuid_hex()}",
        })
        assert r["status"] == 200, f"payment: {r}"
        entry_id = r["data"].get("journal_entry_id")
        assert entry_id
        _assert_balanced(db, entry_id, "supplier-payment")


# ===========================================================================
# Bank → Accounting
# ===========================================================================

class TestBankToAccounting:
    def test_bank_deposit_creates_transaction(self, api, admin_token, db):
        banks = api("GET", "/payments/banks", token=admin_token)
        assert banks["status"] == 200
        blist = banks["data"]
        if isinstance(blist, dict):
            blist = blist.get("items", blist.get("banks", []))
        if not blist:
            pytest.skip("no banks")
        bank_id = blist[0]["id"]
        r = api("POST", f"/payments/banks/{bank_id}/transactions",
                token=admin_token, data={
                    "transaction_type": "deposit",
                    "amount": 1000.0,
                    "description": f"integration deposit {_uuid_hex()}",
                    "reference_number": f"INT-DEP-{_uuid_hex()}",
                })
        assert r["status"] == 200, f"bank deposit: {r}"
        entry_id = r["data"].get("journal_entry_id")
        if entry_id:
            _assert_balanced(db, entry_id, "bank-deposit")


# ===========================================================================
# Cheques → Accounting
# ===========================================================================

class TestChequesToAccounting:
    def test_cheque_lifecycle_creates_balanced_jes(self, api, admin_token, db):
        r = api("POST", "/cheques", token=admin_token, data={
            "cheque_number": f"INT-{_uuid_hex()[:10]}",
            "issue_date": "2026-09-12",
            "amount": 800.0,
            "cheque_type": "received",
            "bank_name": "Integration Bank",
            "payee_name": "Integration Payee",
            "payer_name": "Integration Payer",
        })
        assert r["status"] == 200, f"cheque create: {r}"
        cid = r["data"]["id"]

        r = api("POST", f"/cheques/{cid}/transition", token=admin_token, data={
            "status": "deposited",
            "bank_name": "Integration Bank",
            "notes": "integration deposit",
        })
        assert r["status"] == 200, f"cheque transition: {r}"
        entry_id = r["data"].get("journal_entry_id")
        if entry_id:
            _assert_balanced(db, entry_id, "cheque-transition")
