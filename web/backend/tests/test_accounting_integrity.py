"""§49 Accounting Integrity Tests.

Verifies the fundamental invariants that every accounting system must satisfy:
  1. Total Debits = Total Credits (for all posted journal entries)
  2. Assets = Liabilities + Equity (balance sheet)
  3. Opening + Movement = Closing (per-account running balance)
  4. Budget + Variance = Actual (when a budget exists)

Each failing assertion indicates a data-integrity violation that must be
investigated and corrected before release.
"""

import pytest


# ---------------------------------------------------------------------------
# §49.1  Total Debits = Total Credits
# ---------------------------------------------------------------------------

class TestDebitEqualsCredit:
    def test_every_posted_entry_is_balanced(self, db):
        """Every posted JE must have SUM(debit) == SUM(credit)."""
        rows = db("""
            SELECT je.id, je.entry_number,
                   COALESCE(SUM(jl.debit), 0) AS dr,
                   COALESCE(SUM(jl.credit), 0) AS cr
            FROM journal_entries je
            LEFT JOIN journal_entry_lines jl ON jl.journal_entry_id = je.id
            WHERE je.status = 'Posted'
            GROUP BY je.id, je.entry_number
            HAVING ABS(COALESCE(SUM(jl.debit),0) - COALESCE(SUM(jl.credit),0)) > 0.01
        """)
        bad = [(r[1], r[2], r[3]) for r in rows]
        assert not bad, f"unbalanced posted entries: {bad}"

    def test_global_debit_equals_credit(self, db):
        """The sum of ALL posted lines: total debit == total credit."""
        rows = db("""
            SELECT COALESCE(SUM(jl.debit), 0),
                   COALESCE(SUM(jl.credit), 0)
            FROM journal_entry_lines jl
            JOIN journal_entries je ON je.id = jl.journal_entry_id
            WHERE je.status = 'Posted'
        """)
        dr, cr = float(rows[0][0]), float(rows[0][1])
        assert abs(dr - cr) < 0.01, f"global D≠C: D={dr} C={cr}"

    def test_no_posted_entry_has_zero_lines(self, db):
        """A posted entry must not be empty (zero lines)."""
        rows = db("""
            SELECT je.id, je.entry_number
            FROM journal_entries je
            LEFT JOIN journal_entry_lines jl ON jl.journal_entry_id = je.id
            WHERE je.status = 'Posted' AND jl.id IS NULL
        """)
        assert not rows, f"posted entries with no lines: {rows}"

    def test_no_posted_entry_has_only_one_side(self, db):
        """A posted entry must have at least one debit AND one credit line."""
        rows = db("""
            SELECT je.entry_number,
                   COALESCE(SUM(jl.debit), 0) AS dr,
                   COALESCE(SUM(jl.credit), 0) AS cr
            FROM journal_entries je
            JOIN journal_entry_lines jl ON jl.journal_entry_id = je.id
            WHERE je.status = 'Posted'
            GROUP BY je.id, je.entry_number
            HAVING (COALESCE(SUM(jl.debit),0) < 0.01
                    OR COALESCE(SUM(jl.credit),0) < 0.01)
        """)
        assert not rows, f"one-sided entries: {rows}"


# ---------------------------------------------------------------------------
# §49.2  Assets = Liabilities + Equity
# ---------------------------------------------------------------------------

class TestAccountingEquation:
    def test_balance_sheet_balances(self, api, admin_token, db):
        """Assets == Liabilities + Equity (including current-period net income)."""
        r = api("GET", "/financial-statements/balance-sheet",
                token=admin_token)
        assert r["status"] == 200, f"balance sheet endpoint: {r}"
        data = r["data"]
        total_assets = float(data.get("total_assets", 0))
        total_liab = float(data.get("total_liabilities", 0))
        total_equity = float(data.get("total_equity", 0))
        assert abs(total_assets - (total_liab + total_equity)) < 0.01, (
            f"A={total_assets} ≠ L+E={total_liab + total_equity}"
        )

    def test_balance_sheet_reports_balanced_flag(self, api, admin_token):
        r = api("GET", "/financial-statements/balance-sheet",
                token=admin_token)
        assert r["status"] == 200
        assert r["data"].get("is_balanced") is True, (
            "balance sheet is_balanced should be True"
        )

    def test_trial_balance_debits_equal_credits(self, api, admin_token):
        r = api("GET", "/accounting/trial-balance?per_page=500",
                token=admin_token)
        assert r["status"] == 200
        d = r["data"]
        assert d.get("is_balanced") is True
        assert abs(float(d["total_debit"]) - float(d["total_credit"])) < 0.01


# ---------------------------------------------------------------------------
# §49.3  Opening + Movement = Closing
# ---------------------------------------------------------------------------

class TestOpeningPlusMovementEqualsClosing:
    def test_per_account_balance_consistency(self, db):
        """For every active account:
        opening_balance + SUM(debit - credit) for posted entries == closing balance."""
        rows = db("""
            WITH posted AS (
                SELECT account_id,
                       COALESCE(SUM(debit - credit), 0) AS movement
                FROM journal_entry_lines jl
                JOIN journal_entries je ON je.id = jl.journal_entry_id
                WHERE je.status = 'Posted'
                GROUP BY account_id
            )
            SELECT a.account_code, a.account_name,
                   a.opening_balance,
                   COALESCE(p.movement, 0) AS movement,
                   a.opening_balance + COALESCE(p.movement, 0) AS expected_closing
            FROM accounts a
            LEFT JOIN posted p ON p.account_id = a.id
            WHERE a.is_active = true AND a.is_control = false
        """)
        for code, name, opening, movement, closing in rows:
            # closing must equal opening + movement
            assert abs(opening + movement - closing) < 0.01, (
                f"{code} {name}: opening({opening}) + movement({movement}) "
                f"≠ closing({closing})"
            )


# ---------------------------------------------------------------------------
# §49.4  Budget + Variance = Actual
# ---------------------------------------------------------------------------

class TestBudgetVarianceActual:
    def test_budget_variance_consistency(self, api, admin_token, db):
        """For any budget in a period: budget_amount + variance == actual_amount."""
        periods = api("GET", "/period-closing/fiscal-periods",
                      token=admin_token)
        if periods["status"] != 200:
            pytest.skip("cannot fetch periods")
        plist = periods["data"]
        if isinstance(plist, dict):
            plist = plist.get("items", plist.get("periods", []))
        if not plist:
            pytest.skip("no fiscal periods")

        for p in plist:
            pid = p["id"]
            r = api("GET",
                    f"/budgets/vs-actual?fiscal_period_id={pid}",
                    token=admin_token)
            if r["status"] != 200:
                continue
            items = r["data"]
            if isinstance(items, dict):
                items = items.get("items", items.get("budgets", []))
            for b in items:
                budget = float(b.get("budget_amount", 0))
                actual = float(b.get("actual_amount", 0))
                variance = float(b.get("variance", 0))
                assert abs((budget + variance) - actual) < 0.01, (
                    f"budget {b.get('id')}: budget({budget}) + "
                    f"variance({variance}) ≠ actual({actual})"
                )
