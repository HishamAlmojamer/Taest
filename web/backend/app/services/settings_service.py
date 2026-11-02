"""
Configurable application settings service.

Settings are stored as key/value rows in the `app_settings` table, enriched with
metadata (group, data type, options, visibility) so the UI can render dynamic,
configurable forms grouped by section — similar to global ERP systems.

A rich set of defaults is defined below, organized by group/section.
"""

import json
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import AppSetting


def _default(key: str) -> Optional[dict]:
    return DEFAULT_SETTINGS.get(key)


def _default_value(key: str, fallback: str = "") -> str:
    d = _default(key)
    if d is None:
        return fallback
    return d.get("value", fallback)


# Default settings:
#   key -> {value, description, group, data_type, options, is_visible}
# data_type supports: text, textarea, number, boolean, select, color, date
DEFAULT_SETTINGS: dict[str, dict] = {
    # ── General / Company ────────────────────────────────────────
    "company_name": {
        "value": "", "description": "اسم الشركة", "group": "general",
        "data_type": "text", "options": None, "is_visible": True,
    },
    "company_name_ar": {
        "value": "", "description": "اسم الشركة (عربي)", "group": "general",
        "data_type": "text", "options": None, "is_visible": True,
    },
    "company_tax_number": {
        "value": "", "description": "الرقم الضريبي", "group": "general",
        "data_type": "text", "options": None, "is_visible": True,
    },
    "company_phone": {
        "value": "", "description": "هاتف الشركة", "group": "general",
        "data_type": "text", "options": None, "is_visible": True,
    },
    "company_email": {
        "value": "", "description": "البريد الإلكتروني للشركة", "group": "general",
        "data_type": "text", "options": None, "is_visible": True,
    },
    "company_address": {
        "value": "", "description": "عنوان الشركة", "group": "general",
        "data_type": "textarea", "options": None, "is_visible": True,
    },
    "language": {
        "value": "ar", "description": "لغة الواجهة", "group": "general",
        "data_type": "select", "options": json.dumps([
            {"value": "ar", "label": "العربية"},
            {"value": "en", "label": "English"},
            {"value": "both", "label": "العربية + English"},
        ], ensure_ascii=False), "is_visible": True,
    },
    # ── Numbering / Documents ────────────────────────────────────
    "sale_invoice_prefix": {
        "value": "INV", "description": "بادئة فواتير المبيعات", "group": "numbering",
        "data_type": "text", "options": None, "is_visible": True,
    },
    "purchase_order_prefix": {
        "value": "PO", "description": "بادئة أوامر الشراء", "group": "numbering",
        "data_type": "text", "options": None, "is_visible": True,
    },
    # ── Inventory ────────────────────────────────────────────────
    "low_stock_threshold": {
        "value": "10", "description": "حد التنبيه بالمخزون", "group": "inventory",
        "data_type": "number", "options": None, "is_visible": True,
    },
    "track_batches": {
        "value": "false", "description": "تتبع الدفعات (Batch)", "group": "inventory",
        "data_type": "boolean", "options": None, "is_visible": True,
    },
    "allow_negative_stock": {
        "value": "false", "description": "السماح بمخزون سالب", "group": "inventory",
        "data_type": "boolean", "options": None, "is_visible": True,
    },
    "default_warehouse_id": {
        "value": "", "description": "المستودع الافتراضي", "group": "inventory",
        "data_type": "number", "options": None, "is_visible": True,
    },
    # ── Finance / Accounting ─────────────────────────────────────
    "currency_symbol": {
        "value": "ر.س", "description": "رمز العملة", "group": "finance",
        "data_type": "text", "options": None, "is_visible": True,
    },
    "base_currency": {
        "value": "SAR", "description": "العملة الأساسية", "group": "finance",
        "data_type": "text", "options": None, "is_visible": True,
    },
    "decimal_places": {
        "value": "2", "description": "عدد الخانات العشرية للمبالغ", "group": "finance",
        "data_type": "select", "options": json.dumps([
            {"value": "0", "label": "0"},
            {"value": "2", "label": "2"},
            {"value": "3", "label": "3"},
            {"value": "4", "label": "4"},
        ]), "is_visible": True,
    },
    "rounding_method": {
        "value": "half_up", "description": "طريقة التقريب", "group": "finance",
        "data_type": "select", "options": json.dumps([
            {"value": "half_up", "label": "تقريب نصف لأعلى"},
            {"value": "up", "label": "لأعلى دائماً"},
            {"value": "down", "label": "لأسفل دائماً"},
        ], ensure_ascii=False), "is_visible": True,
    },
    "date_format": {
        "value": "YYYY-MM-DD", "description": "تنسيق التاريخ", "group": "finance",
        "data_type": "select", "options": json.dumps([
            {"value": "YYYY-MM-DD", "label": "YYYY-MM-DD"},
            {"value": "DD-MM-YYYY", "label": "DD-MM-YYYY"},
            {"value": "MM-DD-YYYY", "label": "MM-DD-YYYY"},
        ]), "is_visible": True,
    },
    "fiscal_year_start_month": {
        "value": "1", "description": "شهر بداية السنة المالية", "group": "finance",
        "data_type": "select", "options": json.dumps([
            {"value": str(m), "label": f"شهر {m}"} for m in range(1, 13)
        ], ensure_ascii=False), "is_visible": True,
    },
    "retained_earnings_account_code": {
        "value": "3400", "description": "كود حساب الأرباح المحتجزة", "group": "finance",
        "data_type": "text", "options": None, "is_visible": True,
    },
    "vat_output_account_code": {
        "value": "2121", "description": "كود حساب ضريبة القيمة المضافة المستحقة (الناتج)", "group": "finance",
        "data_type": "text", "options": None, "is_visible": True,
    },
    "vat_input_account_code": {
        "value": "1400", "description": "كود حساب الضريبة غير المستحقة للمطالبة (المدخل)", "group": "finance",
        "data_type": "text", "options": None, "is_visible": True,
    },
    "fx_gain_loss_account_code": {
        "value": "5530", "description": "كود حساب فروق العملة (أرباح/خسائر)", "group": "finance",
        "data_type": "text", "options": None, "is_visible": True,
    },
    # ── Invoicing / Documents ────────────────────────────────────
    "default_tax_rate": {
        "value": "15", "description": "نسبة الضريبة الافتراضية (%)", "group": "invoice",
        "data_type": "number", "options": None, "is_visible": True,
    },
    "show_tax_in_invoice": {
        "value": "true", "description": "إظهار الضريبة في الفواتير", "group": "invoice",
        "data_type": "boolean", "options": None, "is_visible": True,
    },
    "receipt_footer": {
        "value": "", "description": "تذييل الإيصال (الطباعة)", "group": "invoice",
        "data_type": "textarea", "options": None, "is_visible": True,
    },
    "invoice_terms": {
        "value": "", "description": "الشروط والأحكام في الفاتورة", "group": "invoice",
        "data_type": "textarea", "options": None, "is_visible": True,
    },
    # ── UI / Appearance ──────────────────────────────────────────
    "theme": {
        "value": "system", "description": "السمة الافتراضية", "group": "ui",
        "data_type": "select", "options": json.dumps([
            {"value": "light", "label": "فاتح"},
            {"value": "dark", "label": "داكن"},
            {"value": "system", "label": "تلقائي"},
        ], ensure_ascii=False), "is_visible": True,
    },
    "rtl_direction": {
        "value": "true", "description": "اتجاه الواجهة من اليمين لليسار (RTL)", "group": "ui",
        "data_type": "boolean", "options": None, "is_visible": True,
    },
}


async def get_setting(db: AsyncSession, key: str, default: Optional[str] = None) -> str:
    result = await db.execute(select(AppSetting).where(AppSetting.key == key))
    setting = result.scalar_one_or_none()
    if setting and setting.value is not None:
        return setting.value
    if default is not None:
        return default
    return _default_value(key)


async def get_setting_int(db: AsyncSession, key: str, default: int = 0) -> int:
    raw = await get_setting(db, key, str(default))
    try:
        return int(float(raw))
    except (TypeError, ValueError):
        return default


async def ensure_default_settings(db: AsyncSession) -> None:
    """Insert any missing default settings (idempotent) and refresh metadata."""
    keys = list(DEFAULT_SETTINGS.keys())
    result = await db.execute(select(AppSetting).where(AppSetting.key.in_(keys)))
    existing = {row.key: row for row in result.scalars().all()}
    for key, spec in DEFAULT_SETTINGS.items():
        row = existing.get(key)
        if row is None:
            db.add(AppSetting(
                key=key, value=spec["value"], description=spec["description"],
                group=spec["group"], data_type=spec["data_type"],
                options=spec.get("options"), is_visible=spec.get("is_visible", True),
                updated_at=datetime.now(UTC).replace(tzinfo=None),
            ))
    if len(existing) < len(keys):
        await db.flush()


async def set_settings(db: AsyncSession, values: dict) -> int:
    """Upsert settings by key, returning the number of updated/inserted rows."""
    count = 0
    for key, value in values.items():
        spec = _default(key)
        if spec is None:
            continue
        now = datetime.now(UTC).replace(tzinfo=None)
        result = await db.execute(
            update(AppSetting)
            .where(AppSetting.key == key)
            .values(
                value=None if value is None else str(value),
                updated_at=now,
                description=spec["description"],
                group=spec["group"],
                data_type=spec["data_type"],
                options=spec.get("options"),
                is_visible=spec.get("is_visible", True),
            )
        )
        if result.rowcount == 0:
            db.add(AppSetting(
                key=key, value=None if value is None else str(value),
                description=spec["description"], group=spec["group"],
                data_type=spec["data_type"], options=spec.get("options"),
                is_visible=spec.get("is_visible", True), updated_at=now,
            ))
        count += 1
    await db.flush()
    return count


async def list_settings(db: AsyncSession) -> list[dict]:
    await ensure_default_settings(db)
    result = await db.execute(select(AppSetting).order_by(AppSetting.id))
    items = []
    for s in result.scalars().all():
        options = json.loads(s.options) if s.options else None
        items.append({
            "key": s.key, "value": s.value, "description": s.description,
            "group": s.group, "data_type": s.data_type or "text",
            "options": options, "is_visible": s.is_visible if s.is_visible is not None else True,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        })
    return items
