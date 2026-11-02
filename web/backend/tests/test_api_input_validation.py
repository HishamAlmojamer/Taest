"""Regression tests for the "bad input must not be a 500" bug class.

Endpoints that accept a raw ``dict`` body got no Pydantic validation, so a
missing field reached the INSERT/UPDATE and surfaced as a database error:

    KeyError / NotNullViolationError / ForeignKeyViolationError / DataError
    TypeError: invalid keyword argument for <model>

Every request below must produce a 4xx that names the problem (422 for a bad
payload, 404 for an unknown reference), never a 500. Several of these bugs are
silently dependent on live data, so they are asserted against the running stack
on port 8001 rather than in isolation.

Companion case: ``product_warehouse`` has no ``reserved_quantity``/``bin_number``
columns (they are absent from schema.sql and referenced nowhere else), yet
inventory.py passed them to the ORM constructor -> TypeError -> 500.
"""

import inspect

import pytest

from app.utils.validation import coerce_datetime, parse_date_value, require_fields


# POST endpoints that took a raw dict: empty body must be rejected as 422.
EMPTY_BODY_POSTS = [
    "/inventory/product-warehouse",
    "/inventory/transfers",
    "/currencies/currencies",
    "/currencies/exchange-rates",
    "/period-closing/fiscal-periods",
    "/period-closing/fiscal-years",
    "/bank-reconciliation/reconciliations",
    "/settings/companies",
    "/hr/departments",
    "/hr/positions",
    "/hr/employees",
    "/hr/attendance",
    "/hr/leave-types",
    "/hr/leaves",
    "/hr/shifts",
    "/hr/overtime",
    "/hr/bonuses",
    "/hr/performance-reviews",
    "/hr/contracts",
    "/hr/resignations",
    "/hr/training",
    "/hr/documents",
]


@pytest.mark.parametrize("path", EMPTY_BODY_POSTS)
def test_empty_body_is_rejected_not_500(api, admin_token, path):
    res = api("POST", path, token=admin_token, data={})
    assert res["status"] != 500, f"{path} returned 500: {res['data']}"
    assert res["status"] == 422, f"{path} returned {res['status']}: {res['data']}"
    assert "detail" in res["data"]


# Date query params used to raise ValueError out of the handler.
BAD_DATE_GETS = [
    "/accounting/cost-centers/report?from_date=not-a-date",
    "/accounting/cost-centers/report?to_date=2026-13-45",
    "/accounting/vouchers?from_date=not-a-date",
    "/taxes/vat-return?from_date=not-a-date&to_date=2026-12-31",
]


@pytest.mark.parametrize("path", BAD_DATE_GETS)
def test_bad_date_query_is_422_not_500(api, admin_token, path):
    res = api("GET", path, token=admin_token)
    assert res["status"] == 422, f"{path} returned {res['status']}: {res['data']}"


@pytest.mark.parametrize(
    "path",
    [
        "/accounting/cost-centers/report?from_date=2026-01-01&to_date=2026-12-31",
        "/accounting/vouchers?from_date=2026-01-01",
        "/taxes/vat-return?from_date=2026-01-01&to_date=2026-12-31",
    ],
)
def test_valid_dates_still_succeed(api, admin_token, path):
    res = api("GET", path, token=admin_token)
    assert res["status"] == 200, f"{path} returned {res['status']}: {res['data']}"


def test_settings_roles_survives_legacy_text_timestamps(api, admin_token):
    """roles.created_at is a legacy text column; one bad row used to 500 the listing."""
    res = api("GET", "/settings/roles", token=admin_token)
    assert res["status"] == 200, res["data"]
    assert res["data"]["total"] >= 1


@pytest.mark.parametrize(
    "path,body",
    [
        ("/payments/banks/999999/transactions", {"amount": 10}),
        ("/bank-reconciliation/reconciliations",
         {"bank_id": 999999, "statement_date": "2026-01-01", "statement_balance": 1}),
    ],
)
def test_unknown_bank_reference_is_404_not_500(api, admin_token, path, body):
    """A bad foreign key must be rejected before the INSERT, not by the database."""
    res = api("POST", path, token=admin_token, data=body)
    assert res["status"] == 404, f"{path} returned {res['status']}: {res['data']}"


def test_product_warehouse_ignores_columns_that_do_not_exist(api, admin_token, db):
    """Regression: reserved_quantity/bin_number are not real columns."""
    product_id, warehouse_id = db(
        "SELECT (SELECT id FROM products ORDER BY id LIMIT 1), "
        "(SELECT id FROM warehouses ORDER BY id LIMIT 1)"
    )[0]
    res = api("POST", "/inventory/product-warehouse", token=admin_token, data={
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "quantity": 3,
        "reserved_quantity": 7,
        "bin_number": "A-1",
    })
    assert res["status"] == 200, res["data"]


@pytest.mark.parametrize(
    "body",
    [
        {"product_id": 999001, "warehouse_id": 1, "quantity": 1},
        {"product_id": 1, "warehouse_id": 999001, "quantity": 1},
    ],
)
def test_product_warehouse_unknown_reference_is_404_not_500(api, admin_token, db, body):
    """Foreign keys exist on product_warehouse; a bad id must be a 404."""
    real_product, real_warehouse = db(
        "SELECT (SELECT id FROM products ORDER BY id LIMIT 1), "
        "(SELECT id FROM warehouses ORDER BY id LIMIT 1)"
    )[0]
    body = dict(body)
    if body["product_id"] == 1:
        body["product_id"] = real_product
    if body["warehouse_id"] == 1:
        body["warehouse_id"] = real_warehouse
    res = api("POST", "/inventory/product-warehouse", token=admin_token, data=body)
    assert res["status"] == 404, res["data"]


def test_stock_transfer_unknown_reference_is_404_not_500(api, admin_token, db):
    product_id, warehouse_id = db(
        "SELECT (SELECT id FROM products ORDER BY id LIMIT 1), "
        "(SELECT id FROM warehouses ORDER BY id LIMIT 1)"
    )[0]

    def body(**overrides):
        base = {
            "from_warehouse_id": warehouse_id,
            "to_warehouse_id": warehouse_id,
            "transfer_date": "2026-01-01",
            "items": [{"product_id": product_id, "quantity": 1}],
        }
        base.update(overrides)
        return base

    for bad_field in ("from_warehouse_id", "to_warehouse_id"):
        res = api("POST", "/inventory/transfers", token=admin_token,
                  data=body(**{bad_field: 999001}))
        assert res["status"] == 404, f"{bad_field}: {res['status']} {res['data']}"

    res = api("POST", "/inventory/transfers", token=admin_token,
              data=body(items=[{"product_id": 999001, "quantity": 1}]))
    assert res["status"] == 404, res["data"]

    res = api("POST", "/inventory/transfers", token=admin_token,
              data=body(items=[{"product_id": product_id, "quantity": 1, "batch_id": 999001}]))
    assert res["status"] == 404, res["data"]


def test_product_warehouse_listing_is_not_500(api, admin_token):
    res = api("GET", "/inventory/product-warehouse", token=admin_token)
    assert res["status"] == 200, res["data"]
    for row in res["data"]["items"]:
        assert "reserved_quantity" in row
        assert "available_quantity" in row


def test_product_warehouse_model_matches_schema():
    """Guard against reintroducing kwargs the table does not have."""
    from app.models.inventory import ProductWarehouse

    params = inspect.signature(ProductWarehouse.__init__).parameters
    for absent in ("reserved_quantity", "bin_number"):
        assert absent not in params


def test_require_fields_names_the_missing_keys():
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        require_fields({"a": 1}, ["a", "b", "c"])
    assert exc.value.status_code == 422
    assert "b" in exc.value.detail and "c" in exc.value.detail
    for bad in ({"a": 1, "b": None}, {"a": 1, "b": "   "}):
        with pytest.raises(HTTPException) as exc:
            require_fields(bad, ["a", "b"])
        assert exc.value.status_code == 422
        assert "b" in exc.value.detail


def test_parse_date_value_accepts_common_formats():
    assert parse_date_value("2026-03-15").year == 2026
    assert parse_date_value("2026-03-15T10:30:00Z").month == 3
    assert parse_date_value("15/03/2026").day == 15
    assert parse_date_value(None) is None
    assert parse_date_value("") is None


def test_parse_date_value_raises_422_on_garbage():
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        parse_date_value("not-a-date", "from_date")
    assert exc.value.status_code == 422
    assert "from_date" in exc.value.detail


def test_coerce_datetime_is_total_and_never_raises():
    from datetime import date, datetime

    assert coerce_datetime(None) is None
    assert coerce_datetime(datetime(2026, 1, 2)) == datetime(2026, 1, 2)
    assert coerce_datetime(date(2026, 1, 2)) == datetime(2026, 1, 2)
    # Legacy text timestamp from the roles table.
    parsed = coerce_datetime("2026-08-24 13:48:11.325934+03:00")
    assert isinstance(parsed, datetime)
    # Unparseable legacy data degrades to None instead of killing the response.
    assert coerce_datetime("garbage") is None