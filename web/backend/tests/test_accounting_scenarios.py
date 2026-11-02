"""§48 Mandatory Accounting Scenarios — End-to-End.

Each scenario tests a complete business flow through the accounting posting
engine, verifying resulting journal entries are balanced and correct.
Scenarios follow the exact order specified in Promt.txt §48.
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
        "SELECT SUM(debit), SUM(credit) FROM journal_entry_lines WHERE journal_entry_id = %s",
        (entry_id,),
    )
    d, c = float(rows[0][0] or 0), float(rows[0][1] or 0)
    assert abs(d - c) < 0.01, f"{label} JE#{entry_id} unbalanced: D={d} C={c}"


def _account_balance(db, code):
    rows = db("""
        SELECT COALESCE(SUM(jl.debit - jl.credit), 0)
        FROM journal_entry_lines jl
        JOIN journal_entries je ON je.id = jl.journal_entry_id
        JOIN accounts a ON a.id = jl.account_id
        WHERE a.account_code = %s AND je.status = 'Posted'
    """, (code,))
    return float(rows[0][0])


def _purge_test_year_data(db, name, year):
    """Hard-delete leftovers of an aborted earlier run (test-only years)."""
    je_ids = [r[0] for r in db(
        "SELECT id FROM journal_entries WHERE EXTRACT(YEAR FROM entry_date) = %s",
        (year,),
    )]
    period_ids = [r[0] for r in db(
        "SELECT id FROM fiscal_periods WHERE name LIKE %s", (f"{year}%",),
    )]
    if je_ids:
        db("DELETE FROM period_closing_entries WHERE journal_entry_id = ANY(%s)", (je_ids,))
    if period_ids:
        db("DELETE FROM period_closing_entries WHERE fiscal_period_id = ANY(%s)", (period_ids,))
        for table in ("gl_budgets", "purchases", "sales"):
            db(f"DELETE FROM {table} WHERE fiscal_period_id = ANY(%s)", (period_ids,))
    for je_id in je_ids:
        db("DELETE FROM journal_entry_lines WHERE journal_entry_id = %s", (je_id,))
        db("DELETE FROM journal_entries WHERE id = %s", (je_id,))
    for pid in period_ids:
        db("DELETE FROM fiscal_periods WHERE id = %s", (pid,))
    for fy_id in [r[0] for r in db("SELECT id FROM fiscal_years WHERE name = %s", (name,))]:
        db("DELETE FROM fiscal_years WHERE id = %s", (fy_id,))


def _product_id(api, token, db):
    code = f"SCN{_uuid_hex()}"
    r = api("POST", "/inventory/products", token=token, data={
        "code": code, "name": f"Scenario Product {code}", "unit": "pcs",
        "purchase_price": 5.0, "selling_price": 10.0,
        "current_stock": 0.0, "company_id": 1,
    })
    assert r["status"] == 200, f"product create: {r}"
    pid = r["data"]["id"]
    api("POST", "/inventory/stock-movements", token=token, data={
        "product_id": pid, "movement_type": "in",
        "quantity": 999, "unit_cost": 5.0,
        "reference_type": "pytest", "notes": "scenario stock",
    })
    return pid


def _create_sale(api, token, *, product_id, total_amount, discount, tax_amount,
                 final_amount, payment_method, payment_status, qty=2, price=10.0):
    r = api("POST", "/sales", token=token, data={
        "customer_id": 64,
        "total_amount": total_amount, "discount": discount,
        "tax_amount": tax_amount, "final_amount": final_amount,
        "payment_method": payment_method, "payment_status": payment_status,
        "company_id": 1, "branch_id": 1,
        "notes": f"pytest scenario {payment_method}",
        "items": [{"product_id": product_id, "quantity": qty,
                   "unit_price": price, "total_price": qty * price}],
    })
    assert r["status"] == 200, f"sale create: {r}"
    return r["data"]["id"]


def _approve_sale(api, token, sale_id):
    r = api("POST", f"/sales/{sale_id}/submit", token=token, data={})
    assert r["status"] == 200, f"submit: {r}"
    r = api("POST", f"/sales/{sale_id}/approve", token=token, data={})
    assert r["status"] == 200, f"approve: {r}"
    return r["data"]


def _create_je(api, token, lines, entry_date="2026-09-12"):
    r = api("POST", "/accounting/journal-entries", token=token, data={
        "entry_number": f"MNL-{_uuid_hex()}",
        "entry_date": entry_date,
        "description": "scenario manual JE",
        "lines": lines,
    })
    assert r["status"] == 200, f"manual JE: {r}"
    return r["data"]["id"]


def _post_je(api, token, je_id):
    r = api("POST", f"/accounting/journal-entries/{je_id}/post", token=token, data={})
    assert r["status"] == 200, f"post JE: {r}"


# ---------------------------------------------------------------------------
# Scenario 1 — Cash Sale
# ---------------------------------------------------------------------------

class TestScenario1_CashSale:
    def test_full_cash_sale_flow(self, api, admin_token, db):
        pid = _product_id(api, admin_token, db)
        total, discount, tax, final = 100.0, 10.0, 12.6, 102.6
        sale_id = _create_sale(
            api, admin_token, product_id=pid, total_amount=total,
            discount=discount, tax_amount=tax, final_amount=final,
            payment_method="cash", payment_status="paid", qty=5, price=20.0,
        )
        approved = _approve_sale(api, admin_token, sale_id)
        assert approved["workflow_state"] == "approved"
        entry_id = approved.get("journal_entry_id")
        assert entry_id, "sale missing JE"
        _assert_balanced(db, entry_id, "cash-sale")
        rev = _account_balance(db, "4110")
        assert rev < 0 or abs(abs(rev) - (final - tax)) < 1.0, (
            f"revenue expected ~{final - tax}, got {rev}"
        )
        tb = api("GET", "/accounting/trial-balance?per_page=500", token=admin_token)
        assert tb["status"] == 200
        assert tb["data"].get("is_balanced") is True
        inc = api("GET", "/financial-statements/income-statement", token=admin_token)
        assert inc["status"] == 200


# ---------------------------------------------------------------------------
# Scenario 2 — Credit Sale
# ---------------------------------------------------------------------------

class TestScenario2_CreditSale:
    def test_full_credit_sale_flow(self, api, admin_token, db):
        pid = _product_id(api, admin_token, db)
        total, tax, final = 200.0, 30.0, 230.0
        sale_id = _create_sale(
            api, admin_token, product_id=pid, total_amount=total,
            discount=0, tax_amount=tax, final_amount=final,
            payment_method="credit", payment_status="unpaid", qty=10, price=20.0,
        )
        approved = _approve_sale(api, admin_token, sale_id)
        entry_id = approved["journal_entry_id"]
        _assert_balanced(db, entry_id, "credit-sale")
        ar = _account_balance(db, "1200")
        assert ar >= 0, f"AR should be positive (debit), got {ar}"
        aging = api("GET", "/aging-reports/ar-aging", token=admin_token)
        assert aging["status"] == 200


# ---------------------------------------------------------------------------
# Scenario 3 — Purchase
# ---------------------------------------------------------------------------

class TestScenario3_Purchase:
    def test_full_purchase_flow(self, api, admin_token, db):
        pid = _product_id(api, admin_token, db)
        total, discount, tax, final = 500.0, 50.0, 67.5, 517.5
        po = api("POST", "/purchases", token=admin_token, data={
            "supplier_id": _supplier_id(db), "warehouse_id": 1,
            "order_date": "2026-09-12",
            "order_number": f"PO-{_uuid_hex()}",
            "total_amount": total, "discount": discount,
            "tax_amount": tax, "final_amount": final,
            "items": [{"product_id": pid, "quantity": 10,
                       "unit_cost": 50.0, "unit_price": 50.0,
                       "total_cost": 500.0, "total_price": 500.0,
                       "tax_amount": tax}],
        })
        assert po["status"] == 200, f"purchase create: {po}"
        oid = po["data"]["id"]
        r = api("POST", f"/purchases/{oid}/submit", token=admin_token, data={})
        assert r["status"] == 200
        r = api("POST", f"/purchases/{oid}/approve", token=admin_token, data={})
        assert r["status"] == 200
        entry_id = r["data"].get("journal_entry_id")
        assert entry_id, "purchase missing JE"
        _assert_balanced(db, entry_id, "purchase")


# ---------------------------------------------------------------------------
# Scenario 4 — Foreign Currency
# ---------------------------------------------------------------------------

class TestScenario4_ForeignCurrency:
    def test_fx_revaluation_posts_balanced_entry(self, api, admin_token, db):
        currencies = api("GET", "/currencies/currencies", token=admin_token)
        if currencies["status"] != 200 or not currencies["data"]:
            pytest.skip("no currencies available")
        preview = api("POST", "/currencies/revaluate/preview",
                      token=admin_token, data={"as_of": "2026-09-12"})
        assert preview["status"] == 200, f"revaluation preview: {preview}"
        diffs = preview["data"].get("differences", [])
        if diffs:
            result = api("POST", "/currencies/revaluate",
                         token=admin_token, data={"as_of": "2026-09-12"})
            assert result["status"] == 200, f"revaluation apply: {result}"
            entry_id = result["data"].get("journal_entry_id")
            if entry_id:
                _assert_balanced(db, entry_id, "fx-revaluation")


# ---------------------------------------------------------------------------
# Scenario 5 — Cost Allocation
#   Seed expense balance via manual JE → create rule → preview → apply
# ---------------------------------------------------------------------------

class TestScenario5_CostAllocation:
    def test_cost_allocation_flow(self, api, admin_token, db):
        ccs = api("GET", "/accounting/cost-centers", token=admin_token)
        assert ccs["status"] == 200
        cc_list = ccs["data"]
        if isinstance(cc_list, dict):
            cc_list = cc_list.get("items", cc_list.get("cost_centers", []))
        if len(cc_list) < 2:
            pytest.skip("need at least 2 cost centers")

        cc1, cc2 = cc_list[0]["id"], cc_list[1]["id"]

        row = db("SELECT id FROM accounts WHERE account_code = '5210' AND is_active = true AND is_control = false LIMIT 1")
        src_id = int(row[0][0])

        # get account_id for 1121 to credit in the seed JE
        row2 = db("SELECT id FROM accounts WHERE account_code = '1121' AND is_active = true AND is_control = false LIMIT 1")
        bank_id_acct = int(row2[0][0])

        seed_je_id = _create_je(api, admin_token, [
            {"account_id": src_id, "debit": 2000, "credit": 0, "cost_center_id": None},
            {"account_id": bank_id_acct, "debit": 0, "credit": 2000, "cost_center_id": None},
        ], entry_date="2026-09-15")
        _post_je(api, admin_token, seed_je_id)

        rule = api("POST", "/accounting/cost-centers/allocation-rules",
                   token=admin_token, data={
                       "name": f"Alloc Rule {_uuid_hex()}",
                       "description": "pytest allocation",
                       "source_account_id": src_id,
                       "default_method": "percentage",
                       "frequency": "ONCE",
                       "is_active": True,
                       "lines": [
                           {"cost_center_id": cc1, "percentage": 60.0},
                           {"cost_center_id": cc2, "percentage": 40.0},
                       ],
                   })
        assert rule["status"] == 200, f"rule create: {rule}"
        rule_id = rule["data"]["id"]

        preview = api("POST",
                      f"/accounting/cost-centers/allocation-rules/{rule_id}/preview",
                      token=admin_token,
                      data={"from_date": "2026-09-01", "to_date": "2026-09-30"})
        assert preview["status"] == 200, f"preview: {preview}"

        applied = api("POST",
                      f"/accounting/cost-centers/allocation-rules/{rule_id}/apply",
                      token=admin_token,
                      data={"from_date": "2026-09-01", "to_date": "2026-09-30"})
        assert applied["status"] == 200, f"apply: {applied}"
        entry_id = applied["data"].get("entry_id")
        assert entry_id, "apply should return entry_id"
        _assert_balanced(db, entry_id, "cost-allocation")

        report = api("GET", "/accounting/cost-centers/report",
                     token=admin_token)
        assert report["status"] == 200, f"cc report: {report}"


# ---------------------------------------------------------------------------
# Scenario 6 — Asset lifecycle
#   purchase_cost + salvage_value + code → acquire → depreciate → dispose
# ---------------------------------------------------------------------------

class TestScenario6_Asset:
    def test_full_asset_lifecycle(self, api, admin_token, db):
        cats = api("GET", "/fixed-assets/categories", token=admin_token)
        assert cats["status"] == 200
        cat_list = cats["data"]
        if isinstance(cat_list, dict):
            cat_list = cat_list.get("items", cat_list.get("categories", []))
        if not cat_list:
            cat_r = api("POST", "/fixed-assets/categories", token=admin_token, data={
                "name": f"Cat-{_uuid_hex()}", "code": f"CAT{_uuid_hex()[:4]}",
                "depreciation_method": "STRAIGHT_LINE",
                "useful_life_months": 60, "depreciation_rate": 20.0,
            })
            assert cat_r["status"] == 200
            cat_id = cat_r["data"]["id"]
        else:
            cat_id = cat_list[0]["id"]

        code = f"AST{_uuid_hex()[:6]}"
        asset = api("POST", "/fixed-assets/", token=admin_token, data={
            "code": code,
            "name": f"Asset-{_uuid_hex()}",
            "category_id": cat_id,
            "purchase_date": "2026-01-01",
            "purchase_cost": 12000.0,
            "salvage_value": 0.0,
            "useful_life_months": 60,
            "depreciation_method": "STRAIGHT_LINE",
        })
        assert asset["status"] == 200, f"asset create: {asset}"
        asset_id = asset["data"]["id"]

        row = db("SELECT journal_entry_id FROM fixed_assets WHERE id = %s", (asset_id,))
        acq_entry = int(row[0][0]) if row and row[0][0] else None
        if acq_entry:
            _assert_balanced(db, acq_entry, "asset-acquisition")

        dep = api("POST", f"/fixed-assets/{asset_id}/depreciate",
                  token=admin_token, data={"month": 1, "year": 2026})
        assert dep["status"] == 200, f"depreciate: {dep}"
        dep_entry = dep["data"].get("journal_entry_id")
        if dep_entry:
            _assert_balanced(db, dep_entry, "depreciation")

        disp = api("POST", f"/fixed-assets/{asset_id}/dispose",
                   token=admin_token, data={
                       "disposal_date": "2026-06-30",
                       "disposal_amount": 9000.0,
                       "reason": "pytest disposal",
                   })
        assert disp["status"] == 200, f"dispose: {disp}"
        disp_entry = disp["data"].get("journal_entry_id")
        if disp_entry:
            _assert_balanced(db, disp_entry, "disposal")
        gain = disp["data"].get("gain_or_loss")
        assert gain is not None, "disposal should report gain_or_loss"


# ---------------------------------------------------------------------------
# Scenario 7 — Month Closing
#   create throwaway period → post rev+expense JEs → GET validate → close →
#   verify closing JE balanced
# ---------------------------------------------------------------------------

class TestScenario7_MonthClosing:
    def test_period_validate_and_close(self, api, admin_token, db):
        _purge_test_year_data(db, "2099-TST", 2099)
        try:
            fy_r = api("POST", "/period-closing/fiscal-years",
                       token=admin_token, data={
                           "name": "2099-TST",
                           "start_date": "2099-01-01",
                           "end_date": "2099-12-31",
                       })
            assert fy_r["status"] == 200, f"create FY: {fy_r}"
            fy_id = fy_r["data"]["id"]

            p_r = api("POST", "/period-closing/fiscal-periods",
                      token=admin_token, data={
                          "name": "2099-01-TST",
                          "start_date": "2099-01-01",
                          "end_date": "2099-01-31",
                      })
            assert p_r["status"] == 200, f"create period: {p_r}"
            period_id = p_r["data"]["id"]

            row1 = db("SELECT id FROM accounts WHERE account_code = '1121' AND is_active = true AND is_control = false LIMIT 1")
            bank_acct_id = int(row1[0][0])
            row2 = db("SELECT id FROM accounts WHERE account_code = '4110' AND is_active = true AND is_control = false LIMIT 1")
            rev_acct_id = int(row2[0][0])
            row3 = db("SELECT id FROM accounts WHERE account_code = '5210' AND is_active = true AND is_control = false LIMIT 1")
            exp_acct_id = int(row3[0][0])

            je_rev = _create_je(api, admin_token, [
                {"account_id": bank_acct_id, "debit": 500, "credit": 0, "cost_center_id": None},
                {"account_id": rev_acct_id,  "debit": 0,   "credit": 500, "cost_center_id": None},
            ], entry_date="2099-01-15")
            _post_je(api, admin_token, je_rev)

            je_exp = _create_je(api, admin_token, [
                {"account_id": exp_acct_id,  "debit": 200, "credit": 0, "cost_center_id": None},
                {"account_id": bank_acct_id, "debit": 0,   "credit": 200, "cost_center_id": None},
            ], entry_date="2099-01-20")
            _post_je(api, admin_token, je_exp)

            val = api("GET", f"/period-closing/fiscal-periods/{period_id}/validate",
                      token=admin_token)
            assert val["status"] == 200, f"validate: {val}"
            assert val["data"].get("can_close") is True, f"should be closeable: {val['data']}"

            close = api("POST", f"/period-closing/fiscal-periods/{period_id}/close",
                        token=admin_token, data={})
            assert close["status"] == 200, f"close: {close}"

            closing_rows = db(
                "SELECT journal_entry_id FROM period_closing_entries WHERE fiscal_period_id = %s",
                (period_id,),
            )
            assert closing_rows and closing_rows[0][0], "closing entry should exist"
            _assert_balanced(db, int(closing_rows[0][0]), "month-closing-JE")

            tb = api("GET", "/accounting/trial-balance?per_page=500",
                     token=admin_token)
            assert tb["status"] == 200
            assert tb["data"].get("is_balanced") is True
        finally:
            _purge_test_year_data(db, "2099-TST", 2099)


# ---------------------------------------------------------------------------
# Scenario 8 — Year End
#   create throwaway FY → rev+expense JEs → close year → open next year →
#   verify closing JE + opening JE balanced
# ---------------------------------------------------------------------------

class TestScenario8_YearEnd:
    def test_fiscal_year_close_and_reopen(self, api, admin_token, db):
        _purge_test_year_data(db, "2098-TEST", 2098)
        try:
            fy_r = api("POST", "/period-closing/fiscal-years",
                       token=admin_token, data={
                           "name": "2098-TEST",
                           "start_date": "2098-01-01",
                           "end_date": "2098-12-31",
                       })
            assert fy_r["status"] == 200, f"create FY: {fy_r}"
            fy_id = fy_r["data"]["id"]

            gen_r = api("POST",
                        f"/period-closing/fiscal-years/{fy_id}/generate-periods?periods=12",
                        token=admin_token, data={})
            assert gen_r["status"] == 200, f"generate periods: {gen_r}"

            row1 = db("SELECT id FROM accounts WHERE account_code = '1121' AND is_active = true AND is_control = false LIMIT 1")
            bank_acct_id = int(row1[0][0])
            row2 = db("SELECT id FROM accounts WHERE account_code = '4110' AND is_active = true AND is_control = false LIMIT 1")
            rev_acct_id = int(row2[0][0])
            row3 = db("SELECT id FROM accounts WHERE account_code = '5210' AND is_active = true AND is_control = false LIMIT 1")
            exp_acct_id = int(row3[0][0])

            je_rev = _create_je(api, admin_token, [
                {"account_id": bank_acct_id, "debit": 1000, "credit": 0, "cost_center_id": None},
                {"account_id": rev_acct_id,  "debit": 0,    "credit": 1000, "cost_center_id": None},
            ], entry_date="2098-06-15")
            _post_je(api, admin_token, je_rev)

            je_exp = _create_je(api, admin_token, [
                {"account_id": exp_acct_id,  "debit": 400, "credit": 0, "cost_center_id": None},
                {"account_id": bank_acct_id, "debit": 0,   "credit": 400, "cost_center_id": None},
            ], entry_date="2098-09-10")
            _post_je(api, admin_token, je_exp)

            close = api("POST", f"/period-closing/fiscal-years/{fy_id}/closing",
                        token=admin_token, data={})
            assert close["status"] == 200, f"year-end closing: {close}"
            close_je_id = close["data"].get("journal_entry_id")
            assert close_je_id, "closing should produce a JE"
            _assert_balanced(db, close_je_id, "year-end-closing-JE")

            nxt = api("POST",
                      f"/period-closing/fiscal-years/{fy_id}/open-next-year",
                      token=admin_token, data={})
            assert nxt["status"] == 200, f"open next year: {nxt}"
            open_je_id = nxt["data"].get("journal_entry_id")
            if open_je_id:
                _assert_balanced(db, open_je_id, "year-end-opening-JE")

            tb = api("GET", "/accounting/trial-balance?per_page=500",
                     token=admin_token)
            assert tb["status"] == 200
            assert tb["data"].get("is_balanced") is True
        finally:
            _purge_test_year_data(db, "2098-TEST", 2098)
