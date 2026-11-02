"""Focused tests for the journal-entries lifecycle.

Covers the hardenings that protect the daily journal:
  - double-entry balance is enforced at CREATE time (drafts too),
  - control (group) accounts and inactive/missing accounts are rejected,
  - blank descriptions are rejected,
  - active entries are linked to a covering fiscal period automatically,
  - the `status` list filter accepts any casing / aliases (DRAFT/VOID/...),
  - list/get responses enrich lines with account code/name,
  - void reversals carry the SAME date as the original entry.

These tests run against the live backend (api/admin_token fixtures) and the
session-scoped cleanup fixture removes everything they create.
"""

import pytest


def _get_account(db, code):
    row = db(
        "SELECT id FROM accounts WHERE account_code=%s AND is_control=false AND is_active=true LIMIT 1",
        (code,),
    )
    return row[0][0] if row else None


def _control_account(db):
    row = db(
        "SELECT id FROM accounts WHERE is_control=true AND is_active=true "
        "ORDER BY length(account_code) ASC LIMIT 1"
    )
    return row[0][0] if row else None


def _mk_lines(db, dr_code="1111", cr_code="4110", dr=100.0, cr=100.0):
    dr_acct = _get_account(db, dr_code)
    cr_acct = _get_account(db, cr_code)
    assert dr_acct, f"leaf account {dr_code} not found"
    assert cr_acct, f"leaf account {cr_code} not found"
    return dr_acct, cr_acct


class TestCreateHardening:
    def test_create_rejects_unbalanced(self, api, admin_token, db):
        dr, cr = _mk_lines(db)
        r = api("POST", "/accounting/journal-entries", token=admin_token, data={
            "entry_date": "2026-09-01",
            "description": "pytest unbalanced",
            "lines": [
                {"account_id": dr, "debit": 100, "credit": 0},
                {"account_id": cr, "debit": 0, "credit": 50},
            ],
        })
        assert r["status"] == 400, r
        assert "not balanced" in r["data"].get("detail", ""), r

    def test_create_rejects_control_account(self, api, admin_token, db):
        ctrl = _control_account(db)
        dr, cr = _mk_lines(db)
        assert ctrl is not None, "no control account available"
        r = api("POST", "/accounting/journal-entries", token=admin_token, data={
            "entry_date": "2026-09-01",
            "description": "pytest control account",
            "lines": [
                {"account_id": ctrl, "debit": 100, "credit": 0},
                {"account_id": cr, "debit": 0, "credit": 100},
            ],
        })
        assert r["status"] == 400, r
        assert "control" in r["data"].get("detail", "").lower(), r

    def test_create_rejects_missing_account(self, api, admin_token, db):
        dr, cr = _mk_lines(db)
        r = api("POST", "/accounting/journal-entries", token=admin_token, data={
            "entry_date": "2026-09-01",
            "description": "pytest missing account",
            "lines": [
                {"account_id": 999999, "debit": 100, "credit": 0},
                {"account_id": cr, "debit": 0, "credit": 100},
            ],
        })
        assert r["status"] == 400, r

    def test_create_rejects_blank_description(self, api, admin_token, db):
        dr, cr = _mk_lines(db)
        r = api("POST", "/accounting/journal-entries", token=admin_token, data={
            "entry_date": "2026-09-01",
            "description": "   ",
            "lines": [
                {"account_id": dr, "debit": 100, "credit": 0},
                {"account_id": cr, "debit": 0, "credit": 100},
            ],
        })
        assert r["status"] == 400, r

    def test_create_single_line_rejected(self, api, admin_token, db):
        dr, _ = _mk_lines(db)
        r = api("POST", "/accounting/journal-entries", token=admin_token, data={
            "entry_date": "2026-09-01",
            "description": "pytest one line",
            "lines": [
                {"account_id": dr, "debit": 100, "credit": 0},
            ],
        })
        assert r["status"] == 400, r

    def test_create_auto_links_fiscal_period(self, api, admin_token, db):
        dr, cr = _mk_lines(db)
        r = api("POST", "/accounting/journal-entries", token=admin_token, data={
            "entry_date": "2026-09-01",
            "description": "pytest period link",
            "lines": [
                {"account_id": dr, "debit": 100, "credit": 0},
                {"account_id": cr, "debit": 0, "credit": 100},
            ],
        })
        assert r["status"] == 200, r
        assert r["data"].get("fiscal_period_id") is not None, r
        entry_number = r["data"]["entry_number"]
        row = db(
            "SELECT fiscal_period_id, status FROM journal_entries WHERE entry_number=%s",
            (entry_number,),
        )
        assert row and row[0][0] is not None, row
        assert row[0][1] == "Draft", row


class TestListAndEnrichment:
    def test_status_filter_is_case_insensitive(self, api, admin_token, db):
        # 'DRAFT' (uppercase) must resolve to the canonical 'Draft' status.
        r = api("GET", "/accounting/journal-entries?status=DRAFT", token=admin_token)
        assert r["status"] == 200, r
        assert isinstance(r["data"].get("items"), list), r

        r2 = api("GET", "/accounting/journal-entries?status=draft", token=admin_token)
        assert r2["status"] == 200, r2

        r3 = api("GET", "/accounting/journal-entries?status=VOID", token=admin_token)
        assert r3["status"] == 200, r3

    def test_lines_enriched_with_account_info(self, api, admin_token, db):
        dr, cr = _mk_lines(db)
        r = api("POST", "/accounting/journal-entries", token=admin_token, data={
            "entry_date": "2026-09-02",
            "description": "pytest enrichment",
            "lines": [
                {"account_id": dr, "debit": 200, "credit": 0},
                {"account_id": cr, "debit": 0, "credit": 200},
            ],
        })
        assert r["status"] == 200, r
        entry_number = r["data"]["entry_number"]

        for url in (f"/accounting/journal-entries?search={entry_number}",
                    f"/accounting/journal-entries/{r['data']['id']}"):
            resp = api("GET", url, token=admin_token)
            assert resp["status"] == 200, resp
            items = resp["data"].get("items") or [resp["data"]]
            entry = next((it for it in items if it.get("entry_number") == entry_number), items[0])
            lines = entry.get("lines") or []
            assert len(lines) >= 2, lines
            assert all("account_code" in l for l in lines), lines
            # debit line is cash 1111 / revenue 4110 -> codes must be present
            codes = {l.get("account_code") for l in lines}
            assert codes == {"1111", "4110"}, codes

    def test_search_by_account_code(self, api, admin_token, db):
        r = api("GET", "/accounting/journal-entries?search=4110", token=admin_token)
        assert r["status"] == 200, r
        assert isinstance(r["data"].get("items"), list), r


class TestUpdateHardening:
    def test_update_rejects_control_account(self, api, admin_token, db):
        dr, cr = _mk_lines(db)
        r = api("POST", "/accounting/journal-entries", token=admin_token, data={
            "entry_date": "2026-09-03",
            "description": "pytest update ctrl",
            "lines": [
                {"account_id": dr, "debit": 100, "credit": 0},
                {"account_id": cr, "debit": 0, "credit": 100},
            ],
        })
        assert r["status"] == 200, r
        je_id = r["data"]["id"]
        ctrl = _control_account(db)
        r = api("PUT", f"/accounting/journal-entries/{je_id}", token=admin_token, data={
            "lines": [
                {"account_id": ctrl, "debit": 100, "credit": 0},
                {"account_id": cr, "debit": 0, "credit": 100},
            ],
        })
        assert r["status"] == 400, r
        assert "control" in r["data"].get("detail", "").lower(), r


class TestVoidLifecycle:
    def test_void_reversal_keeps_original_date(self, api, admin_token, db):
        dr, cr = _mk_lines(db)
        r = api("POST", "/accounting/journal-entries", token=admin_token, data={
            "entry_date": "2026-08-15",
            "description": "pytest void date",
            "lines": [
                {"account_id": dr, "debit": 300, "credit": 0},
                {"account_id": cr, "debit": 0, "credit": 300},
            ],
        })
        assert r["status"] == 200, r
        je_id = r["data"]["id"]
        pr = api("POST", f"/accounting/journal-entries/{je_id}/post", token=admin_token, data={})
        assert pr["status"] == 200, pr

        import urllib.parse
        vr = api("POST", f"/accounting/journal-entries/{je_id}/void?reason={urllib.parse.quote('pytest void')}",
                 token=admin_token, data={})
        assert vr["status"] == 200, vr
        reversal_id = vr["data"]["reversal_id"]

        row = db("SELECT entry_date FROM journal_entries WHERE id=%s", (je_id,))
        orig = row[0][0]
        rev = db("SELECT entry_date, reference_type, status FROM journal_entries WHERE id=%s", (reversal_id,))
        assert rev and rev[0][1] == "JournalEntryReversal" and rev[0][2] == "Posted", rev
        assert rev[0][0].date() == orig.date(), (rev[0][0], orig)