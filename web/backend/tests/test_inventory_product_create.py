"""Regression: saving a product without a barcode must never fail silently.

``products.barcode`` has a UNIQUE constraint. The form used to submit
``barcode: ""`` for an untouched field, so every new product without a barcode
collided with the first empty string (and with any other blank barcode). The
database raised a unique violation, the API answered 500 and the UI had no
``onError`` handler, so pressing "حفظ" appeared to do nothing.

The contract asserted here:
* a blank/whitespace barcode is persisted as NULL and can be repeated;
* a real duplicate barcode is a readable 409, never a 500;
* blank name / negative price are 422;
* the session cleanup in conftest removes the rows created below.
"""

import uuid

import pytest


def _payload(**overrides):
    code = "RGT-" + uuid.uuid4().hex[:10].upper()
    data = {
        "code": code,
        "name": f"منتج اختبار {code}",
        "unit": "pcs",
        "purchase_price": 10,
        "selling_price": 20,
        "current_stock": 0,
        "min_stock": 0,
        "max_stock": 0,
        "tax_percent": 15,
        "company_id": 1,
    }
    data.update(overrides)
    return data


def test_product_without_barcode_can_be_created_twice(api, admin_token):
    first = api("POST", "/inventory/products", token=admin_token, data=_payload(barcode=""))
    second = api("POST", "/inventory/products", token=admin_token, data=_payload(barcode=""))
    assert first["status"] == 200, first
    assert second["status"] == 200, second
    assert first["data"]["id"] != second["data"]["id"]


def test_blank_barcode_is_stored_as_null(api, admin_token, db):
    code = "RGT-" + uuid.uuid4().hex[:10].upper()
    res = api("POST", "/inventory/products", token=admin_token, data=_payload(code=code, barcode="   "))
    assert res["status"] == 200, res
    rows = db("SELECT barcode FROM products WHERE code = %s", (code,))
    assert rows, "created product not found"
    assert rows[0][0] is None


def test_duplicate_barcode_is_409_not_500(api, admin_token):
    barcode = "BC-" + uuid.uuid4().hex[:12].upper()
    first = api("POST", "/inventory/products", token=admin_token, data=_payload(barcode=barcode))
    assert first["status"] == 200, first
    second = api("POST", "/inventory/products", token=admin_token, data=_payload(barcode=barcode))
    assert second["status"] == 409, second
    assert "الباركود" in str(second["data"])


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": "   "},
        {"unit": "   "},
        {"purchase_price": -1},
        {"selling_price": -0.01},
    ],
)
def test_invalid_product_payload_is_422(api, admin_token, overrides):
    res = api("POST", "/inventory/products", token=admin_token, data=_payload(**overrides))
    assert res["status"] == 422, res
