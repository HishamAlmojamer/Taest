"""
Seed Chart of Accounts - Comprehensive Saudi ERP System
Run once: python -m app.seed_chart_of_accounts
"""
import asyncio
from datetime import UTC, datetime
from sqlalchemy import text
from app.database import engine, async_session_factory


ACCOUNTS = [
    # ── Assets (الأصول) ──────────────────────────────────────
    # Root group
    {"code": "1000", "name": "الأصول", "name_en": "Assets", "name_ar": "الأصول", "type": "asset", "parent": None, "control": True},

    # Current Assets
    {"code": "1100", "name": "الأصول المتداولة", "name_en": "Current Assets", "name_ar": "الأصول المتداولة", "type": "asset", "parent": "1000", "control": True},

    # Cash & Bank
    {"code": "1110", "name": "الصندوق", "name_en": "Cash on Hand", "name_ar": "الصندوق", "type": "asset", "parent": "1100", "control": False},
    {"code": "1111", "name": "الصندوق الرئيسي", "name_en": "Main Cash Drawer", "name_ar": "الصندوق الرئيسي", "type": "asset", "parent": "1110", "control": False},
    {"code": "1112", "name": "صندوق صغير", "name_en": "Petty Cash", "name_ar": "صندوق صغير", "type": "asset", "parent": "1110", "control": False},
    {"code": "1120", "name": "الحسابات البنكية", "name_en": "Bank Accounts", "name_ar": "الحسابات البنكية", "type": "asset", "parent": "1100", "control": True},
    {"code": "1121", "name": "بنك الأهلي السعودي", "name_en": "Al Ahli Bank", "name_ar": "بنك الأهلي السعودي", "type": "asset", "parent": "1120", "control": False},
    {"code": "1122", "name": "بنك الراجحي", "name_en": "Al Rajhi Bank", "name_ar": "بنك الراجحي", "type": "asset", "parent": "1120", "control": False},
    {"code": "1123", "name": "بنك الإنماء", "name_en": "Al Inma Bank", "name_ar": "بنك الإنماء", "type": "asset", "parent": "1120", "control": False},
    {"code": "1124", "name": "البنك الأهلي التجاري", "name_en": "NCB", "name_ar": "البنك الأهلي التجاري", "type": "asset", "parent": "1120", "control": False},

    # Receivables
    {"code": "1200", "name": "المدينون", "name_en": "Receivables", "name_ar": "المدينون", "type": "asset", "parent": "1100", "control": True},
    {"code": "1201", "name": "حسابات العملاء", "name_en": "Accounts Receivable", "name_ar": "حسابات العملاء", "type": "asset", "parent": "1200", "control": False},
    {"code": "1202", "name": "ديون مدينة مختلفة", "name_en": "Other Receivables", "name_ar": "ديون مدينة مختلفة", "type": "asset", "parent": "1200", "control": False},
    {"code": "1203", "name": "ustadh / موظفون - سلف", "name_en": "Employee Advances", "name_ar": "سلف موظفين", "type": "asset", "parent": "1200", "control": False},
    {"code": "1204", "name": "إيرادات مستحقة", "name_en": "Accrued Revenue", "name_ar": "إيرادات مستحقة", "type": "asset", "parent": "1200", "control": False},
    {"code": "1205", "name": "شيكات تحت التحصيل", "name_en": "Cheques on Hand", "name_ar": "شيكات تحت التحصيل", "type": "asset", "parent": "1200", "control": False},

    # Prepayments
    {"code": "1210", "name": "مصروفات مدفوعة مقدماً", "name_en": "Prepaid Expenses", "name_ar": "مصروفات مدفوعة مقدماً", "type": "asset", "parent": "1100", "control": False},
    {"code": "1211", "name": "إيجار مدفوع مقدماً", "name_en": "Prepaid Rent", "name_ar": "إيجار مدفوع مقدماً", "type": "asset", "parent": "1210", "control": False},
    {"code": "1212", "name": "تأمين مدفوع مقدماً", "name_en": "Prepaid Insurance", "name_ar": "تأمين مدفوع مقدماً", "type": "asset", "parent": "1210", "control": False},

    # Inventory
    {"code": "1300", "name": "المخزون", "name_en": "Inventory", "name_ar": "المخزون", "type": "asset", "parent": "1100", "control": True},
    {"code": "1301", "name": "المخزون - بضائع تامة الصنع", "name_en": "Finished Goods", "name_ar": "المخزون - بضائع تامة", "type": "asset", "parent": "1300", "control": False},
    {"code": "1302", "name": "المخزون - خامات", "name_en": "Raw Materials", "name_ar": "المخزون - خامات", "type": "asset", "parent": "1300", "control": False},
    {"code": "1303", "name": "بضائع مستلمة غير مفوترة", "name_en": "GRNI", "name_ar": "بضائع مستلمة غير مفوترة", "type": "asset", "parent": "1300", "control": False},

    # VAT Input
    {"code": "1400", "name": "ضريبة القيمة المضافة - مدفوعة", "name_en": "VAT Input", "name_ar": "ضريبة القيمة المضافة (مدفوعة)", "type": "asset", "parent": "1000", "control": False},

    # Fixed Assets
    {"code": "1500", "name": "الأصول الثابتة", "name_en": "Fixed Assets", "name_ar": "الأصول الثابتة", "type": "asset", "parent": "1000", "control": True},
    {"code": "1510", "name": "أراضٍ", "name_en": "Land", "name_ar": "أراضٍ", "type": "asset", "parent": "1500", "control": False},
    {"code": "1520", "name": "مباني", "name_en": "Buildings", "name_ar": "مباني", "type": "asset", "parent": "1500", "control": False},
    {"code": "1530", "name": "آلات ومعدات", "name_en": "Machinery & Equipment", "name_ar": "آلات ومعدات", "type": "asset", "parent": "1500", "control": False},
    {"code": "1540", "name": "أثاث ومفروشات", "name_en": "Furniture & Fixtures", "name_ar": "أثاث ومفروشات", "type": "asset", "parent": "1500", "control": False},
    {"code": "1550", "name": "مركبات", "name_en": "Vehicles", "name_ar": "مركبات", "type": "asset", "parent": "1500", "control": False},
    {"code": "1560", "name": "أجهزة كمبيوتر وتقنية معلومات", "name_en": "IT Equipment", "name_ar": "أجهزة كمبيوتر", "type": "asset", "parent": "1500", "control": False},

    # Accumulated Depreciation
    {"code": "1600", "name": "مجمع الإهلاك", "name_en": "Accumulated Depreciation", "name_ar": "مجمع الإهلاك", "type": "asset", "parent": "1000", "control": True},
    {"code": "1610", "name": "مجمع إهلاك المباني", "name_en": "Acc. Depr. - Buildings", "name_ar": "مجمع إهلاك المباني", "type": "asset", "parent": "1600", "control": False},
    {"code": "1620", "name": "مجمع إهلاك الآلات", "name_en": "Acc. Depr. - Machinery", "name_ar": "مجمع إهلاك الآلات", "type": "asset", "parent": "1600", "control": False},
    {"code": "1630", "name": "مجمع إهلاك الأثاث", "name_en": "Acc. Depr. - Furniture", "name_ar": "مجمع إهلاك الأثاث", "type": "asset", "parent": "1600", "control": False},
    {"code": "1640", "name": "مجمع إهلاك المركبات", "name_en": "Acc. Depr. - Vehicles", "name_ar": "مجمع إهلاك المركبات", "type": "asset", "parent": "1600", "control": False},
    {"code": "1650", "name": "مجمع إهلاك الأجهزة", "name_en": "Acc. Depr. - IT Equipment", "name_ar": "مجمع إهلاك الأجهزة", "type": "asset", "parent": "1600", "control": False},

    # ── Liabilities (الخصوم) ─────────────────────────────────
    {"code": "2000", "name": "الخصوم", "name_en": "Liabilities", "name_ar": "الخصوم", "type": "liability", "parent": None, "control": True},

    # Current Liabilities
    {"code": "2100", "name": "الخصوم المتداولة", "name_en": "Current Liabilities", "name_ar": "الخصوم المتداولة", "type": "liability", "parent": "2000", "control": True},

    # Payables
    {"code": "2110", "name": "الدائنون", "name_en": "Payables", "name_ar": "الدائنون", "type": "liability", "parent": "2100", "control": True},
    {"code": "2111", "name": "حسابات الموردين", "name_en": "Accounts Payable", "name_ar": "حسابات الموردين", "type": "liability", "parent": "2110", "control": False},
    {"code": "2112", "name": "ديون دائنة مختلفة", "name_en": "Other Payables", "name_ar": "ديون دائنة مختلفة", "type": "liability", "parent": "2110", "control": False},

    # Tax
    {"code": "2120", "name": "الضرائب المستحقة", "name_en": "Taxes Payable", "name_ar": "الضرائب المستحقة", "type": "liability", "parent": "2100", "control": True},
    {"code": "2121", "name": "ضريبة القيمة المضافة المستحقة", "name_en": "VAT Payable", "name_ar": "ضريبة القيمة المضافة المستحقة", "type": "liability", "parent": "2120", "control": False},
    {"code": "2122", "name": "ضريبة الدخل المستحقة", "name_en": "Income Tax Payable", "name_ar": "ضريبة الدخل المستحقة", "type": "liability", "parent": "2120", "control": False},
    {"code": "2123", "name": "زكاة مستحقة", "name_en": "Zakat Payable", "name_ar": "زكاة مستحقة", "type": "liability", "parent": "2120", "control": False},
    {"code": "2124", "name": "شيكات مسحوبة", "name_en": "Cheques Issued", "name_ar": "شيكات مسحوبة", "type": "liability", "parent": "2100", "control": False},

    # Accrued Expenses
    {"code": "2130", "name": "المصروفات المستحقة", "name_en": "Accrued Expenses", "name_ar": "المصروفات المستحقة", "type": "liability", "parent": "2100", "control": True},
    {"code": "2131", "name": "رواتب مستحقة", "name_en": "Salaries Payable", "name_ar": "رواتب مستحقة", "type": "liability", "parent": "2130", "control": False},
    {"code": "2132", "name": "أرباح إجازة مستحقة", "name_en": "Accrued Leave", "name_ar": "أرباح إجازة مستحقة", "type": "liability", "parent": "2130", "control": False},
    {"code": "2133", "name": "مصروفات أخرى مستحقة", "name_en": "Other Accrued", "name_ar": "مصروفات أخرى مستحقة", "type": "liability", "parent": "2130", "control": False},

    # Deferred Revenue
    {"code": "2140", "name": "إيرادات مقدمة", "name_en": "Deferred Revenue", "name_ar": "إيرادات مقدمة", "type": "liability", "parent": "2100", "control": False},

    # Long-term Liabilities
    {"code": "2200", "name": "خصوم طويلة الأجل", "name_en": "Long-term Liabilities", "name_ar": "خصوم طويلة الأجل", "type": "liability", "parent": "2000", "control": True},
    {"code": "2210", "name": "قروض بنكية طويلة الأجل", "name_en": "Long-term Loans", "name_ar": "قروض بنكية طويلة الأجل", "type": "liability", "parent": "2200", "control": False},
    {"code": "2220", "name": "التزامات التأجير المالي", "name_en": "Finance Lease Liabilities", "name_ar": "التزامات التأجير المالي", "type": "liability", "parent": "2200", "control": False},

    # ── Equity (حقوق الملكية) ────────────────────────────────
    {"code": "3000", "name": "حقوق الملكية", "name_en": "Equity", "name_ar": "حقوق الملكية", "type": "equity", "parent": None, "control": True},

    {"code": "3100", "name": "رأس المال", "name_en": "Capital", "name_ar": "رأس المال", "type": "equity", "parent": "3000", "control": False},
    {"code": "3200", "name": "احتياطيات قانونية", "name_en": "Legal Reserves", "name_ar": "احتياطيات قانونية", "type": "equity", "parent": "3000", "control": False},
    {"code": "3300", "name": "احتياطيات أخرى", "name_en": "Other Reserves", "name_ar": "احتياطيات أخرى", "type": "equity", "parent": "3000", "control": False},
    {"code": "3400", "name": "أرباح محتجزة", "name_en": "Retained Earnings", "name_ar": "أرباح محتجزة", "type": "equity", "parent": "3000", "control": False},
    {"code": "3500", "name": "أرباح مبقاة", "name_en": "Current Year Earnings", "name_ar": "أرباح مبقاة", "type": "equity", "parent": "3000", "control": False},

    # ── Revenue (الإيرادات) ──────────────────────────────────
    {"code": "4000", "name": "الإيرادات", "name_en": "Revenue", "name_ar": "الإيرادات", "type": "revenue", "parent": None, "control": True},

    {"code": "4100", "name": "إيرادات المبيعات", "name_en": "Sales Revenue", "name_ar": "إيرادات المبيعات", "type": "revenue", "parent": "4000", "control": True},
    {"code": "4110", "name": "مبيعات محلية", "name_en": "Local Sales", "name_ar": "مبيعات محلية", "type": "revenue", "parent": "4100", "control": False},
    {"code": "4120", "name": "مبيعات تصدير", "name_en": "Export Sales", "name_ar": "مبيعات تصدير", "type": "revenue", "parent": "4100", "control": False},
    {"code": "4130", "name": "خصم مكتسب", "name_en": "Discount Received", "name_ar": "خصم مكتسب", "type": "revenue", "parent": "4100", "control": False},

    {"code": "4200", "name": "مرتجعات المبيعات", "name_en": "Sales Returns", "name_ar": "مرتجعات المبيعات", "type": "revenue", "parent": "4000", "control": True},
    {"code": "4210", "name": "مرتجعات مبيعات محلية", "name_en": "Local Sales Returns", "name_ar": "مرتجعات مبيعات محلية", "type": "revenue", "parent": "4200", "control": False},
    {"code": "4220", "name": "خصومات على المبيعات", "name_en": "Sales Discounts", "name_ar": "خصومات على المبيعات", "type": "revenue", "parent": "4200", "control": False},

    {"code": "4300", "name": "إيرادات الخدمات", "name_en": "Service Revenue", "name_ar": "إيرادات الخدمات", "type": "revenue", "parent": "4000", "control": True},
    {"code": "4310", "name": "إيرادات خدمات", "name_en": "Service Income", "name_ar": "إيرادات خدمات", "type": "revenue", "parent": "4300", "control": False},
    {"code": "4320", "name": "إيرادات تأجير", "name_en": "Rental Income", "name_ar": "إيرادات تأجير", "type": "revenue", "parent": "4300", "control": False},

    {"code": "4400", "name": "إيرادات أخرى", "name_en": "Other Income", "name_ar": "إيرادات أخرى", "type": "revenue", "parent": "4000", "control": True},
    {"code": "4410", "name": "إيرادات فائدة", "name_en": "Interest Income", "name_ar": "إيرادات فائدة", "type": "revenue", "parent": "4400", "control": False},
    {"code": "4420", "name": "أرباح بيع أصول", "name_en": "Gain on Asset Sale", "name_ar": "أرباح بيع أصول", "type": "revenue", "parent": "4400", "control": False},
    {"code": "4430", "name": "إيرادات أخرى مختلفة", "name_en": "Miscellaneous Income", "name_ar": "إيرادات أخرى مختلفة", "type": "revenue", "parent": "4400", "control": False},

    # ── Expenses (المصروفات) ─────────────────────────────────
    {"code": "5000", "name": "المصروفات", "name_en": "Expenses", "name_ar": "المصروفات", "type": "expense", "parent": None, "control": True},

    # COGS
    {"code": "5100", "name": "تكلفة البضاعة المباعة", "name_en": "Cost of Goods Sold", "name_ar": "تكلفة البضاعة المباعة", "type": "expense", "parent": "5000", "control": True},
    {"code": "5110", "name": "تكلفة المبيعات", "name_en": "Cost of Sales", "name_ar": "تكلفة المبيعات", "type": "expense", "parent": "5100", "control": False},
    {"code": "5120", "name": "تكلفة المرتجعات", "name_en": "Cost of Returns", "name_ar": "تكلفة المرتجعات", "type": "expense", "parent": "5100", "control": False},

    # Personnel
    {"code": "5200", "name": "مصروفات الأفراد", "name_en": "Personnel Expenses", "name_ar": "مصروفات الأفراد", "type": "expense", "parent": "5000", "control": True},
    {"code": "5210", "name": "رواتب", "name_en": "Salaries", "name_ar": "رواتب", "type": "expense", "parent": "5200", "control": False},
    {"code": "5220", "name": "مكافآت", "name_en": "Bonuses", "name_ar": "مكافآت", "type": "expense", "parent": "5200", "control": False},
    {"code": "5230", "name": "بدلات", "name_en": "Allowances", "name_ar": "بدلات", "type": "expense", "parent": "5200", "control": False},
    {"code": "5240", "name": "إيجار سكن", "name_en": "Housing Allowance", "name_ar": "إيجار سكن", "type": "expense", "parent": "5200", "control": False},
    {"code": "5250", "name": "تأمينات ومتطلبات العمل", "name_en": "Employee Benefits", "name_ar": "تأمينات ومتطلبات العمل", "type": "expense", "parent": "5200", "control": False},
    {"code": "5260", "name": "مصاريف تدريب وتطوير", "name_en": "Training", "name_ar": "مصاريف تدريب", "type": "expense", "parent": "5200", "control": False},

    # Operating
    {"code": "5300", "name": "مصروفات تشغيلية", "name_en": "Operating Expenses", "name_ar": "مصروفات تشغيلية", "type": "expense", "parent": "5000", "control": True},
    {"code": "5310", "name": "إيجار", "name_en": "Rent", "name_ar": "إيجار", "type": "expense", "parent": "5300", "control": False},
    {"code": "5320", "name": "مرافق (كهرباء، ماء، هاتف)", "name_en": "Utilities", "name_ar": "مرافق", "type": "expense", "parent": "5300", "control": False},
    {"code": "5330", "name": "صيانة وإصلاح", "name_en": "Maintenance", "name_ar": "صيانة وإصلاح", "type": "expense", "parent": "5300", "control": False},
    {"code": "5340", "name": "تأمين", "name_en": "Insurance", "name_ar": "تأمين", "type": "expense", "parent": "5300", "control": False},
    {"code": "5350", "name": "مصاريف مكتبية", "name_en": "Office Supplies", "name_ar": "مصاريف مكتبية", "type": "expense", "parent": "5300", "control": False},
    {"code": "5360", "name": "نقل وشحن", "name_en": "Shipping & Transport", "name_ar": "نقل وشحن", "type": "expense", "parent": "5300", "control": False},
    {"code": "5370", "name": "إ פרסام وتسويق", "name_en": "Advertising & Marketing", "name_ar": "إפרסام وتسويق", "type": "expense", "parent": "5300", "control": False},
    {"code": "5380", "name": "اشتراكات ورسوم", "name_en": "Subscriptions & Fees", "name_ar": "اشتراكات ورسوم", "type": "expense", "parent": "5300", "control": False},

    # Administrative
    {"code": "5400", "name": "مصروفات إدارية", "name_en": "Administrative Expenses", "name_ar": "مصروفات إدارية", "type": "expense", "parent": "5000", "control": True},
    {"code": "5410", "name": "مصاريف استشارية ومحاسبية", "name_en": "Consulting & Accounting", "name_ar": "استشارات ومحاسبة", "type": "expense", "parent": "5400", "control": False},
    {"code": "5420", "name": "رحلات وتنقل", "name_en": "Travel & Transport", "name_ar": "رحلات وتنقل", "type": "expense", "parent": "5400", "control": False},
    {"code": "5430", "name": "وفاقيات واستقبال", "name_en": "Entertainment", "name_ar": "وفاقيات واستقبال", "type": "expense", "parent": "5400", "control": False},
    {"code": "5440", "name": "قانونية ورسوم حكومية", "name_en": "Legal & Government Fees", "name_ar": "قانونية ورسوم حكومية", "type": "expense", "parent": "5400", "control": False},

    # Financial
    {"code": "5500", "name": "مصروفات مالية", "name_en": "Financial Expenses", "name_ar": "مصروفات مالية", "type": "expense", "parent": "5000", "control": True},
    {"code": "5510", "name": "فوائد قروض", "name_en": "Interest Expense", "name_ar": "فوائد قروض", "type": "expense", "parent": "5500", "control": False},
    {"code": "5520", "name": "رسوم بنكية", "name_en": "Bank Charges", "name_ar": "رسوم بنكية", "type": "expense", "parent": "5500", "control": False},
    {"code": "5530", "name": "خسائر عملة", "name_en": "Foreign Exchange Loss", "name_ar": "خسائر عملة", "type": "expense", "parent": "5500", "control": False},

    # Depreciation
    {"code": "5600", "name": "مصروفات الإهلاك", "name_en": "Depreciation", "name_ar": "مصروفات الإهلاك", "type": "expense", "parent": "5000", "control": True},
    {"code": "5610", "name": "إهلاك مباني", "name_en": "Depr. - Buildings", "name_ar": "إهلاك مباني", "type": "expense", "parent": "5600", "control": False},
    {"code": "5620", "name": "إهلاك آلات", "name_en": "Depr. - Machinery", "name_ar": "إهلاك آلات", "type": "expense", "parent": "5600", "control": False},
    {"code": "5630", "name": "إهلاك أثاث", "name_en": "Depr. - Furniture", "name_ar": "إهلاك أثاث", "type": "expense", "parent": "5600", "control": False},
    {"code": "5640", "name": "إهلاك مركبات", "name_en": "Depr. - Vehicles", "name_ar": "إهلاك مركبات", "type": "expense", "parent": "5600", "control": False},
    {"code": "5650", "name": "إهلاك أجهزة", "name_en": "Depr. - IT Equipment", "name_ar": "إهلاك أجهزة", "type": "expense", "parent": "5600", "control": False},

    # Other
    {"code": "5700", "name": "مصروفات أخرى", "name_en": "Other Expenses", "name_ar": "مصروفات أخرى", "type": "expense", "parent": "5000", "control": True},
    {"code": "5710", "name": "مصروفات مختلفة", "name_en": "Miscellaneous Expense", "name_ar": "مصروفات مختلفة", "type": "expense", "parent": "5700", "control": False},
    {"code": "5720", "name": "هبات وتبرعات", "name_en": "Donations", "name_ar": "هبات وتبرعات", "type": "expense", "parent": "5700", "control": False},
]


async def seed():
    async with engine.begin() as conn:
        # Add account_name_ar column if not exists
        await conn.execute(text("""
            DO $$ BEGIN
                ALTER TABLE accounts ADD COLUMN IF NOT EXISTS account_name_ar VARCHAR(200);
            EXCEPTION WHEN duplicate_column THEN null;
            END $$;
        """))
        await conn.execute(text("""
            DO $$ BEGIN
                ALTER TABLE accounts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
            EXCEPTION WHEN duplicate_column THEN null;
            END $$;
        """))
        await conn.execute(text("COMMIT"))

    async with async_session_factory() as session:
        # Check existing accounts
        result = await session.execute(text("SELECT count(*) FROM accounts"))
        existing = result.scalar()
        if existing and existing > 0:
            print(f"Found {existing} existing accounts. Clearing related data and re-seeding...")
            await session.execute(text("DELETE FROM journal_entry_lines"))
            await session.execute(text("DELETE FROM journal_entries"))
            await session.execute(text("DELETE FROM accounts"))
            await session.commit()
            print("Cleared existing data.")

        # Build code-to-id mapping
        code_map = {}
        now = datetime.now(UTC).replace(tzinfo=None)

        for acc in ACCOUNTS:
            parent_id = code_map.get(acc["parent"])
            insert = text("""
                INSERT INTO accounts (account_code, account_name, account_name_en, account_name_ar, account_type, parent_id, is_control, is_active, opening_balance, created_at, updated_at)
                VALUES (:code, :name, :name_en, :name_ar, :type, :parent_id, :is_control, true, 0, :now, :now)
                RETURNING id
            """)
            result = await session.execute(insert, {
                "code": acc["code"], "name": acc["name"], "name_en": acc["name_en"],
                "name_ar": acc["name_ar"], "type": acc["type"], "parent_id": parent_id,
                "is_control": acc["control"], "now": now,
            })
            row = result.fetchone()
            code_map[acc["code"]] = row[0]

        await session.commit()
        print(f"Seeded {len(ACCOUNTS)} accounts successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
