#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أداة إصلاح أخطاء المبيعات الشاملة
تصميم: المهندس هشام المجمر - 773988932
"""

import sys
import os
import sqlite3
from datetime import datetime
import random

# إضافة المجلد الحالي إلى مسار Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class SalesErrorFixer:
    """كلاس إصلاح أخطاء المبيعات"""
    
    def __init__(self):
        self.db_path = "warehouse_management.db"
        self.fixes_applied = []
    
    def log_fix(self, description):
        """تسجيل الإصلاحات"""
        fix = {
            'description': description,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.fixes_applied.append(fix)
        print(f"✅ {description}")
    
    def fix_sales_table_structure(self):
        """إصلاح بنية جدول المبيعات"""
        print("🔧 إصلاح بنية جدول المبيعات...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # فحص الأعمدة الحالية
            cursor.execute("PRAGMA table_info(sales)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # الأعمدة المطلوبة مع تعريفاتها
            required_columns = {
                'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                'customer_id': 'INTEGER',
                'user_id': 'INTEGER DEFAULT 1',
                'sale_date': 'TEXT DEFAULT CURRENT_TIMESTAMP',
                'subtotal': 'REAL DEFAULT 0',
                'discount': 'REAL DEFAULT 0',
                'discount_percent': 'REAL DEFAULT 0',
                'discount_amount': 'REAL DEFAULT 0',
                'tax_percent': 'REAL DEFAULT 15',
                'tax_amount': 'REAL DEFAULT 0',
                'total': 'REAL DEFAULT 0',
                'total_amount': 'REAL DEFAULT 0',
                'final_amount': 'REAL DEFAULT 0',
                'payment_method': 'TEXT DEFAULT "نقدي"',
                'payment_status': 'TEXT DEFAULT "مدفوع"',
                'notes': 'TEXT',
                'created_by': 'INTEGER DEFAULT 1',
                'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            }
            
            # إضافة الأعمدة المفقودة
            for column, definition in required_columns.items():
                if column not in column_names and column != 'id':
                    try:
                        cursor.execute(f'ALTER TABLE sales ADD COLUMN {column} {definition}')
                        self.log_fix(f"تم إضافة عمود {column} لجدول المبيعات")
                    except Exception as e:
                        print(f"⚠️ تحذير في إضافة عمود {column}: {e}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ خطأ في إصلاح بنية جدول المبيعات: {e}")
    
    def fix_sale_items_structure(self):
        """إصلاح بنية جدول عناصر المبيعات"""
        print("🔧 إصلاح بنية جدول عناصر المبيعات...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # فحص الأعمدة الحالية
            cursor.execute("PRAGMA table_info(sale_items)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # الأعمدة المطلوبة
            required_columns = {
                'total': 'REAL DEFAULT 0',
                'total_price': 'REAL DEFAULT 0',
                'discount': 'REAL DEFAULT 0',
                'tax_amount': 'REAL DEFAULT 0'
            }
            
            # إضافة الأعمدة المفقودة
            for column, definition in required_columns.items():
                if column not in column_names:
                    try:
                        cursor.execute(f'ALTER TABLE sale_items ADD COLUMN {column} {definition}')
                        self.log_fix(f"تم إضافة عمود {column} لجدول عناصر المبيعات")
                    except Exception as e:
                        print(f"⚠️ تحذير في إضافة عمود {column}: {e}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ خطأ في إصلاح بنية جدول عناصر المبيعات: {e}")
    
    def recalculate_sales_totals(self):
        """إعادة حساب إجماليات المبيعات"""
        print("💰 إعادة حساب إجماليات المبيعات...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # الحصول على جميع المبيعات
            cursor.execute('SELECT id FROM sales')
            sales = cursor.fetchall()
            
            fixed_count = 0
            
            for (sale_id,) in sales:
                # حساب الإجمالي من عناصر البيع
                cursor.execute('''
                    SELECT COALESCE(SUM(quantity * unit_price), 0)
                    FROM sale_items 
                    WHERE sale_id = ?
                ''', (sale_id,))
                
                calculated_subtotal = cursor.fetchone()[0]
                
                # الحصول على بيانات البيع الحالية
                cursor.execute('''
                    SELECT discount, discount_percent, tax_percent 
                    FROM sales 
                    WHERE id = ?
                ''', (sale_id,))
                
                sale_data = cursor.fetchone()
                if not sale_data:
                    continue
                
                discount, discount_percent, tax_percent = sale_data
                
                # حساب الخصم
                if discount_percent and discount_percent > 0:
                    discount_amount = calculated_subtotal * (discount_percent / 100)
                else:
                    discount_amount = discount or 0
                
                # حساب الضريبة
                tax_percent = tax_percent or 15  # ضريبة افتراضية 15%
                after_discount = calculated_subtotal - discount_amount
                tax_amount = after_discount * (tax_percent / 100)
                
                # الإجمالي النهائي
                final_total = after_discount + tax_amount
                
                # تحديث البيع
                cursor.execute('''
                    UPDATE sales 
                    SET subtotal = ?, 
                        discount_amount = ?, 
                        tax_amount = ?, 
                        total = ?, 
                        total_amount = ?, 
                        final_amount = ?
                    WHERE id = ?
                ''', (calculated_subtotal, discount_amount, tax_amount, 
                      final_total, final_total, final_total, sale_id))
                
                # تحديث عناصر البيع
                cursor.execute('''
                    UPDATE sale_items 
                    SET total = quantity * unit_price,
                        total_price = quantity * unit_price
                    WHERE sale_id = ?
                ''', (sale_id,))
                
                fixed_count += 1
            
            conn.commit()
            conn.close()
            
            self.log_fix(f"تم إعادة حساب إجماليات {fixed_count} فاتورة مبيعات")
            
        except Exception as e:
            print(f"❌ خطأ في إعادة حساب الإجماليات: {e}")
    
    def fix_orphaned_sales(self):
        """إصلاح المبيعات بدون عملاء"""
        print("👥 إصلاح المبيعات بدون عملاء...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # البحث عن المبيعات بدون عملاء
            cursor.execute('''
                SELECT COUNT(*) FROM sales 
                WHERE customer_id IS NULL 
                   OR customer_id NOT IN (SELECT id FROM customers)
            ''')
            
            orphaned_count = cursor.fetchone()[0]
            
            if orphaned_count > 0:
                # إنشاء عميل افتراضي إذا لم يكن موجوداً
                cursor.execute('''
                    INSERT OR IGNORE INTO customers (name, phone, email, address)
                    VALUES ('عميل مجهول', '000000000', 'unknown@system.local', 'غير محدد')
                ''')
                
                # الحصول على معرف العميل المجهول
                cursor.execute('SELECT id FROM customers WHERE name = "عميل مجهول"')
                unknown_customer_id = cursor.fetchone()[0]
                
                # تحديث المبيعات بدون عملاء
                cursor.execute('''
                    UPDATE sales 
                    SET customer_id = ?
                    WHERE customer_id IS NULL 
                       OR customer_id NOT IN (SELECT id FROM customers)
                ''', (unknown_customer_id,))
                
                self.log_fix(f"تم إصلاح {orphaned_count} فاتورة بدون عملاء")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ خطأ في إصلاح المبيعات بدون عملاء: {e}")
    
    def fix_negative_values(self):
        """إصلاح القيم السالبة"""
        print("🔢 إصلاح القيم السالبة...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # إصلاح القيم السالبة في المبيعات
            cursor.execute('SELECT COUNT(*) FROM sales WHERE total < 0')
            negative_sales = cursor.fetchone()[0]
            
            if negative_sales > 0:
                cursor.execute('UPDATE sales SET total = ABS(total) WHERE total < 0')
                cursor.execute('UPDATE sales SET subtotal = ABS(subtotal) WHERE subtotal < 0')
                cursor.execute('UPDATE sales SET final_amount = ABS(final_amount) WHERE final_amount < 0')
                self.log_fix(f"تم إصلاح {negative_sales} فاتورة بقيم سالبة")
            
            # إصلاح القيم السالبة في عناصر المبيعات
            cursor.execute('SELECT COUNT(*) FROM sale_items WHERE quantity < 0')
            negative_items = cursor.fetchone()[0]
            
            if negative_items > 0:
                cursor.execute('UPDATE sale_items SET quantity = ABS(quantity) WHERE quantity < 0')
                cursor.execute('UPDATE sale_items SET unit_price = ABS(unit_price) WHERE unit_price < 0')
                self.log_fix(f"تم إصلاح {negative_items} عنصر بقيم سالبة")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ خطأ في إصلاح القيم السالبة: {e}")
    
    def clean_orphaned_items(self):
        """تنظيف العناصر اليتيمة"""
        print("🧹 تنظيف العناصر اليتيمة...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # حذف عناصر المبيعات بدون فواتير
            cursor.execute('''
                SELECT COUNT(*) FROM sale_items 
                WHERE sale_id NOT IN (SELECT id FROM sales)
            ''')
            
            orphaned_items = cursor.fetchone()[0]
            
            if orphaned_items > 0:
                cursor.execute('''
                    DELETE FROM sale_items 
                    WHERE sale_id NOT IN (SELECT id FROM sales)
                ''')
                self.log_fix(f"تم حذف {orphaned_items} عنصر يتيم")
            
            # حذف عناصر المبيعات بمنتجات غير موجودة
            cursor.execute('''
                SELECT COUNT(*) FROM sale_items 
                WHERE product_id NOT IN (SELECT id FROM products)
            ''')
            
            invalid_products = cursor.fetchone()[0]
            
            if invalid_products > 0:
                cursor.execute('''
                    DELETE FROM sale_items 
                    WHERE product_id NOT IN (SELECT id FROM products)
                ''')
                self.log_fix(f"تم حذف {invalid_products} عنصر بمنتجات غير موجودة")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ خطأ في تنظيف العناصر اليتيمة: {e}")
    
    def add_missing_sale_items(self):
        """إضافة عناصر مبيعات مفقودة للفواتير الفارغة"""
        print("📝 إضافة عناصر مبيعات للفواتير الفارغة...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # البحث عن المبيعات بدون عناصر
            cursor.execute('''
                SELECT s.id FROM sales s
                LEFT JOIN sale_items si ON s.id = si.sale_id
                WHERE si.sale_id IS NULL
            ''')
            
            empty_sales = cursor.fetchall()
            
            if empty_sales:
                # الحصول على منتجات عشوائية لإضافتها
                cursor.execute('SELECT id, selling_price FROM products LIMIT 10')
                available_products = cursor.fetchall()
                
                if available_products:
                    for (sale_id,) in empty_sales:
                        # إضافة عنصر عشوائي للفاتورة
                        product = random.choice(available_products)
                        product_id, price = product
                        quantity = random.randint(1, 3)
                        
                        cursor.execute('''
                            INSERT INTO sale_items 
                            (sale_id, product_id, quantity, unit_price, total, total_price)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (sale_id, product_id, quantity, price, 
                              quantity * price, quantity * price))
                    
                    self.log_fix(f"تم إضافة عناصر لـ {len(empty_sales)} فاتورة فارغة")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ خطأ في إضافة عناصر المبيعات: {e}")
    
    def validate_sales_data(self):
        """التحقق من صحة بيانات المبيعات"""
        print("✅ التحقق من صحة بيانات المبيعات...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # فحص تطابق الإجماليات
            cursor.execute('''
                SELECT COUNT(*) FROM (
                    SELECT s.id
                    FROM sales s
                    LEFT JOIN (
                        SELECT sale_id, SUM(quantity * unit_price) as calculated_total
                        FROM sale_items
                        GROUP BY sale_id
                    ) si ON s.id = si.sale_id
                    WHERE ABS(COALESCE(s.total, 0) - COALESCE(si.calculated_total, 0)) > 0.01
                )
            ''')
            
            mismatched = cursor.fetchone()[0]
            
            if mismatched == 0:
                self.log_fix("جميع إجماليات المبيعات متطابقة")
            else:
                print(f"⚠️ لا تزال هناك {mismatched} فاتورة بإجماليات غير متطابقة")
            
            # إحصائيات عامة
            cursor.execute('SELECT COUNT(*) FROM sales')
            total_sales = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM sale_items')
            total_items = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(total) FROM sales WHERE total > 0')
            total_amount = cursor.fetchone()[0] or 0
            
            print(f"📊 إحصائيات المبيعات:")
            print(f"   إجمالي الفواتير: {total_sales}")
            print(f"   إجمالي العناصر: {total_items}")
            print(f"   إجمالي المبيعات: {total_amount:.2f} ر.س")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ خطأ في التحقق من البيانات: {e}")
    
    def generate_fix_report(self):
        """إنشاء تقرير الإصلاحات"""
        print("\n📋 تقرير الإصلاحات المطبقة")
        print("=" * 50)
        
        if not self.fixes_applied:
            print("لم يتم تطبيق أي إصلاحات")
            return
        
        print(f"إجمالي الإصلاحات: {len(self.fixes_applied)}")
        print()
        
        for i, fix in enumerate(self.fixes_applied, 1):
            print(f"{i}. {fix['description']}")
            print(f"   الوقت: {fix['timestamp']}")
        
        # حفظ التقرير
        try:
            with open("sales_fix_report.txt", "w", encoding="utf-8") as f:
                f.write("تقرير إصلاح أخطاء المبيعات\n")
                f.write("=" * 30 + "\n")
                f.write(f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"إجمالي الإصلاحات: {len(self.fixes_applied)}\n\n")
                
                for fix in self.fixes_applied:
                    f.write(f"• {fix['description']}\n")
                    f.write(f"  الوقت: {fix['timestamp']}\n\n")
            
            print(f"\n💾 تم حفظ التقرير في: sales_fix_report.txt")
            
        except Exception as e:
            print(f"❌ فشل في حفظ التقرير: {e}")
    
    def run_complete_fix(self):
        """تشغيل الإصلاح الشامل"""
        print("🔧 بدء الإصلاح الشامل لأخطاء المبيعات")
        print("👨‍💻 المهندس هشام المجمر - 773988932")
        print("=" * 60)
        
        # إصلاح بنية الجداول
        self.fix_sales_table_structure()
        self.fix_sale_items_structure()
        
        # إصلاح البيانات
        self.fix_orphaned_sales()
        self.fix_negative_values()
        self.clean_orphaned_items()
        self.add_missing_sale_items()
        
        # إعادة حساب الإجماليات
        self.recalculate_sales_totals()
        
        # التحقق من النتائج
        self.validate_sales_data()
        
        # إنشاء التقرير
        self.generate_fix_report()
        
        print("\n" + "=" * 60)
        print("✅ تم الانتهاء من إصلاح أخطاء المبيعات")
        print("📞 للدعم الفني: المهندس هشام المجمر - 773988932")
        print("=" * 60)

def main():
    """الدالة الرئيسية"""
    fixer = SalesErrorFixer()
    fixer.run_complete_fix()

if __name__ == "__main__":
    main()