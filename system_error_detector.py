#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أداة شاملة لاكتشاف وإصلاح أخطاء النظام
تصميم: المهندس هشام المجمر - 773988932
"""

import sys
import os
import sqlite3
import traceback
from datetime import datetime

# إضافة المجلد الحالي إلى مسار Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class SystemErrorDetector:
    """كلاس لاكتشاف وإصلاح أخطاء النظام"""
    
    def __init__(self):
        self.db_path = "warehouse_management.db"
        self.errors_found = []
        self.fixes_applied = []
    
    def log_error(self, error_type, description, fix_applied=None):
        """تسجيل الأخطاء"""
        error = {
            'type': error_type,
            'description': description,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'fix_applied': fix_applied
        }
        self.errors_found.append(error)
        
        if fix_applied:
            self.fixes_applied.append(error)
    
    def check_database_structure(self):
        """فحص بنية قاعدة البيانات"""
        print("🔍 فحص بنية قاعدة البيانات...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # فحص الجداول المطلوبة
            required_tables = [
                'users', 'products', 'customers', 'suppliers', 'categories',
                'sales', 'sale_items', 'purchases', 'purchase_items',
                'stock_movements', 'roles', 'permissions'
            ]
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                self.log_error("DATABASE", f"جداول مفقودة: {missing_tables}")
                print(f"❌ جداول مفقودة: {missing_tables}")
            else:
                print("✅ جميع الجداول الأساسية موجودة")
            
            # فحص الأعمدة المطلوبة في جدول المبيعات
            cursor.execute("PRAGMA table_info(sales)")
            sales_columns = [col[1] for col in cursor.fetchall()]
            
            required_sales_columns = [
                'id', 'customer_id', 'user_id', 'sale_date', 'subtotal',
                'discount', 'tax_amount', 'total', 'payment_method', 'payment_status'
            ]
            
            missing_sales_columns = [col for col in required_sales_columns if col not in sales_columns]
            
            if missing_sales_columns:
                self.log_error("SALES_TABLE", f"أعمدة مفقودة في جدول المبيعات: {missing_sales_columns}")
                print(f"❌ أعمدة مفقودة في جدول المبيعات: {missing_sales_columns}")
                
                # إصلاح الأعمدة المفقودة
                self.fix_sales_table_columns(cursor, missing_sales_columns)
            else:
                print("✅ جدول المبيعات سليم")
            
            # فحص جدول المنتجات
            cursor.execute("PRAGMA table_info(products)")
            products_columns = [col[1] for col in cursor.fetchall()]
            
            required_products_columns = [
                'id', 'name', 'barcode', 'category_id', 'unit',
                'purchase_price', 'selling_price', 'stock', 'min_stock'
            ]
            
            missing_products_columns = [col for col in required_products_columns if col not in products_columns]
            
            if missing_products_columns:
                self.log_error("PRODUCTS_TABLE", f"أعمدة مفقودة في جدول المنتجات: {missing_products_columns}")
                print(f"❌ أعمدة مفقودة في جدول المنتجات: {missing_products_columns}")
                
                # إصلاح الأعمدة المفقودة
                self.fix_products_table_columns(cursor, missing_products_columns)
            else:
                print("✅ جدول المنتجات سليم")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.log_error("DATABASE_CONNECTION", f"خطأ في الاتصال بقاعدة البيانات: {e}")
            print(f"❌ خطأ في فحص قاعدة البيانات: {e}")
    
    def fix_sales_table_columns(self, cursor, missing_columns):
        """إصلاح أعمدة جدول المبيعات"""
        print("🔧 إصلاح جدول المبيعات...")
        
        column_definitions = {
            'user_id': 'INTEGER',
            'sale_date': 'TEXT DEFAULT CURRENT_TIMESTAMP',
            'subtotal': 'REAL DEFAULT 0',
            'discount': 'REAL DEFAULT 0',
            'tax_amount': 'REAL DEFAULT 0',
            'total': 'REAL DEFAULT 0',
            'payment_method': 'TEXT DEFAULT "نقدي"',
            'payment_status': 'TEXT DEFAULT "مدفوع"'
        }
        
        for column in missing_columns:
            if column in column_definitions:
                try:
                    cursor.execute(f'ALTER TABLE sales ADD COLUMN {column} {column_definitions[column]}')
                    print(f"✅ تم إضافة عمود {column} لجدول المبيعات")
                    self.log_error("SALES_FIX", f"تم إضافة عمود {column}", "نجح")
                except Exception as e:
                    print(f"❌ فشل في إضافة عمود {column}: {e}")
                    self.log_error("SALES_FIX", f"فشل في إضافة عمود {column}: {e}")
        
        # تحديث البيانات الموجودة
        try:
            cursor.execute('''
                UPDATE sales 
                SET total = COALESCE(final_amount, total_amount, 0)
                WHERE total IS NULL OR total = 0
            ''')
            print("✅ تم تحديث بيانات المبيعات")
        except Exception as e:
            print(f"⚠️ تحذير في تحديث بيانات المبيعات: {e}")
    
    def fix_products_table_columns(self, cursor, missing_columns):
        """إصلاح أعمدة جدول المنتجات"""
        print("🔧 إصلاح جدول المنتجات...")
        
        column_definitions = {
            'stock': 'INTEGER DEFAULT 0',
            'min_stock': 'INTEGER DEFAULT 0',
            'purchase_price': 'REAL DEFAULT 0',
            'selling_price': 'REAL DEFAULT 0'
        }
        
        for column in missing_columns:
            if column in column_definitions:
                try:
                    cursor.execute(f'ALTER TABLE products ADD COLUMN {column} {column_definitions[column]}')
                    print(f"✅ تم إضافة عمود {column} لجدول المنتجات")
                    self.log_error("PRODUCTS_FIX", f"تم إضافة عمود {column}", "نجح")
                except Exception as e:
                    print(f"❌ فشل في إضافة عمود {column}: {e}")
                    self.log_error("PRODUCTS_FIX", f"فشل في إضافة عمود {column}: {e}")
        
        # تحديث البيانات الموجودة
        try:
            cursor.execute('''
                UPDATE products 
                SET stock = COALESCE(current_stock, quantity, 0)
                WHERE stock IS NULL OR stock = 0
            ''')
            print("✅ تم تحديث بيانات المنتجات")
        except Exception as e:
            print(f"⚠️ تحذير في تحديث بيانات المنتجات: {e}")
    
    def check_sales_data_integrity(self):
        """فحص سلامة بيانات المبيعات"""
        print("\n💰 فحص سلامة بيانات المبيعات...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # فحص المبيعات بدون عملاء
            cursor.execute('''
                SELECT COUNT(*) FROM sales 
                WHERE customer_id IS NULL OR customer_id NOT IN (SELECT id FROM customers)
            ''')
            orphaned_sales = cursor.fetchone()[0]
            
            if orphaned_sales > 0:
                self.log_error("SALES_DATA", f"مبيعات بدون عملاء: {orphaned_sales}")
                print(f"⚠️ مبيعات بدون عملاء: {orphaned_sales}")
                
                # إصلاح المبيعات بدون عملاء
                self.fix_orphaned_sales(cursor)
            
            # فحص المبيعات بقيم سالبة
            cursor.execute('SELECT COUNT(*) FROM sales WHERE total < 0')
            negative_sales = cursor.fetchone()[0]
            
            if negative_sales > 0:
                self.log_error("SALES_DATA", f"مبيعات بقيم سالبة: {negative_sales}")
                print(f"❌ مبيعات بقيم سالبة: {negative_sales}")
                
                # إصلاح القيم السالبة
                cursor.execute('UPDATE sales SET total = ABS(total) WHERE total < 0')
                print("✅ تم إصلاح القيم السالبة")
            
            # فحص عناصر المبيعات
            cursor.execute('''
                SELECT COUNT(*) FROM sale_items si
                WHERE si.sale_id NOT IN (SELECT id FROM sales)
            ''')
            orphaned_items = cursor.fetchone()[0]
            
            if orphaned_items > 0:
                self.log_error("SALES_ITEMS", f"عناصر مبيعات يتيمة: {orphaned_items}")
                print(f"⚠️ عناصر مبيعات يتيمة: {orphaned_items}")
                
                # حذف العناصر اليتيمة
                cursor.execute('''
                    DELETE FROM sale_items 
                    WHERE sale_id NOT IN (SELECT id FROM sales)
                ''')
                print("✅ تم حذف العناصر اليتيمة")
            
            # فحص تطابق الإجماليات
            cursor.execute('''
                SELECT s.id, s.total, 
                       COALESCE(SUM(si.quantity * si.unit_price), 0) as calculated_total
                FROM sales s
                LEFT JOIN sale_items si ON s.id = si.sale_id
                GROUP BY s.id, s.total
                HAVING ABS(s.total - calculated_total) > 0.01
            ''')
            mismatched_totals = cursor.fetchall()
            
            if mismatched_totals:
                self.log_error("SALES_TOTALS", f"إجماليات غير متطابقة: {len(mismatched_totals)}")
                print(f"⚠️ إجماليات غير متطابقة: {len(mismatched_totals)}")
                
                # إصلاح الإجماليات
                self.fix_sales_totals(cursor, mismatched_totals)
            else:
                print("✅ إجماليات المبيعات متطابقة")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.log_error("SALES_CHECK", f"خطأ في فحص بيانات المبيعات: {e}")
            print(f"❌ خطأ في فحص بيانات المبيعات: {e}")
    
    def fix_orphaned_sales(self, cursor):
        """إصلاح المبيعات بدون عملاء"""
        print("🔧 إصلاح المبيعات بدون عملاء...")
        
        try:
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
                WHERE customer_id IS NULL OR customer_id NOT IN (SELECT id FROM customers)
            ''', (unknown_customer_id,))
            
            print("✅ تم إصلاح المبيعات بدون عملاء")
            self.log_error("ORPHANED_SALES_FIX", "تم إصلاح المبيعات بدون عملاء", "نجح")
            
        except Exception as e:
            print(f"❌ فشل في إصلاح المبيعات بدون عملاء: {e}")
            self.log_error("ORPHANED_SALES_FIX", f"فشل في الإصلاح: {e}")
    
    def fix_sales_totals(self, cursor, mismatched_sales):
        """إصلاح إجماليات المبيعات"""
        print("🔧 إصلاح إجماليات المبيعات...")
        
        for sale_id, current_total, calculated_total in mismatched_sales:
            try:
                # تحديث الإجمالي المحسوب
                cursor.execute('''
                    UPDATE sales 
                    SET total = ?, subtotal = ?
                    WHERE id = ?
                ''', (calculated_total, calculated_total, sale_id))
                
                print(f"✅ تم إصلاح إجمالي البيع {sale_id}: {current_total} → {calculated_total}")
                
            except Exception as e:
                print(f"❌ فشل في إصلاح البيع {sale_id}: {e}")
    
    def check_products_data(self):
        """فحص بيانات المنتجات"""
        print("\n📦 فحص بيانات المنتجات...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # فحص المنتجات بدون أسعار
            cursor.execute('SELECT COUNT(*) FROM products WHERE selling_price <= 0')
            no_price_products = cursor.fetchone()[0]
            
            if no_price_products > 0:
                self.log_error("PRODUCTS_DATA", f"منتجات بدون أسعار: {no_price_products}")
                print(f"⚠️ منتجات بدون أسعار: {no_price_products}")
                
                # تحديث الأسعار الافتراضية
                cursor.execute('''
                    UPDATE products 
                    SET selling_price = 1.0, purchase_price = 0.8
                    WHERE selling_price <= 0
                ''')
                print("✅ تم تحديث الأسعار الافتراضية")
            
            # فحص المنتجات بمخزون سالب
            cursor.execute('SELECT COUNT(*) FROM products WHERE stock < 0')
            negative_stock = cursor.fetchone()[0]
            
            if negative_stock > 0:
                self.log_error("PRODUCTS_DATA", f"منتجات بمخزون سالب: {negative_stock}")
                print(f"❌ منتجات بمخزون سالب: {negative_stock}")
                
                # إصلاح المخزون السالب
                cursor.execute('UPDATE products SET stock = 0 WHERE stock < 0')
                print("✅ تم إصلاح المخزون السالب")
            
            # فحص المنتجات بدون فئات
            cursor.execute('''
                SELECT COUNT(*) FROM products 
                WHERE category_id IS NULL OR category_id NOT IN (SELECT id FROM categories)
            ''')
            no_category_products = cursor.fetchone()[0]
            
            if no_category_products > 0:
                self.log_error("PRODUCTS_DATA", f"منتجات بدون فئات: {no_category_products}")
                print(f"⚠️ منتجات بدون فئات: {no_category_products}")
                
                # إنشاء فئة افتراضية
                cursor.execute('''
                    INSERT OR IGNORE INTO categories (name, description)
                    VALUES ('فئة عامة', 'فئة افتراضية للمنتجات')
                ''')
                
                cursor.execute('SELECT id FROM categories WHERE name = "فئة عامة"')
                default_category_id = cursor.fetchone()[0]
                
                # تحديث المنتجات بدون فئات
                cursor.execute('''
                    UPDATE products 
                    SET category_id = ?
                    WHERE category_id IS NULL OR category_id NOT IN (SELECT id FROM categories)
                ''', (default_category_id,))
                
                print("✅ تم إصلاح المنتجات بدون فئات")
            else:
                print("✅ جميع المنتجات لها فئات")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.log_error("PRODUCTS_CHECK", f"خطأ في فحص بيانات المنتجات: {e}")
            print(f"❌ خطأ في فحص بيانات المنتجات: {e}")
    
    def check_system_files(self):
        """فحص ملفات النظام"""
        print("\n📁 فحص ملفات النظام...")
        
        required_files = [
            'database.py', 'login_window.py', 'main_window.py',
            'sales_window.py', 'products_window.py', 'customers_window.py',
            'suppliers_window.py', 'reports_window.py'
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            self.log_error("SYSTEM_FILES", f"ملفات مفقودة: {missing_files}")
            print(f"❌ ملفات مفقودة: {missing_files}")
        else:
            print("✅ جميع ملفات النظام موجودة")
        
        # فحص ملفات النظام المحسن
        enhanced_files = [
            'ai_analytics.py', 'enhanced_sales_window.py',
            'enhanced_dashboard.py', 'enhanced_reports.py',
            'permissions_system.py', 'security_utils.py'
        ]
        
        missing_enhanced = []
        for file in enhanced_files:
            if not os.path.exists(file):
                missing_enhanced.append(file)
        
        if missing_enhanced:
            self.log_error("ENHANCED_FILES", f"ملفات محسنة مفقودة: {missing_enhanced}")
            print(f"⚠️ ملفات محسنة مفقودة: {missing_enhanced}")
        else:
            print("✅ جميع ملفات النظام المحسن موجودة")
    
    def test_system_imports(self):
        """اختبار استيراد ملفات النظام"""
        print("\n🔍 اختبار استيراد ملفات النظام...")
        
        modules_to_test = [
            'database', 'login_window', 'main_window',
            'sales_window', 'products_window', 'customers_window'
        ]
        
        for module in modules_to_test:
            try:
                __import__(module)
                print(f"✅ {module}")
            except Exception as e:
                self.log_error("IMPORT_ERROR", f"خطأ في استيراد {module}: {e}")
                print(f"❌ {module}: {e}")
        
        # اختبار الملفات المحسنة
        enhanced_modules = [
            'ai_analytics', 'enhanced_sales_window',
            'enhanced_dashboard', 'permissions_system'
        ]
        
        for module in enhanced_modules:
            try:
                __import__(module)
                print(f"✅ {module} (محسن)")
            except Exception as e:
                self.log_error("ENHANCED_IMPORT", f"خطأ في استيراد {module}: {e}")
                print(f"⚠️ {module}: {e}")
    
    def generate_error_report(self):
        """إنشاء تقرير الأخطاء"""
        print("\n📋 تقرير الأخطاء والإصلاحات")
        print("=" * 50)
        
        if not self.errors_found:
            print("🎉 لم يتم العثور على أخطاء!")
            return
        
        print(f"📊 إجمالي الأخطاء المكتشفة: {len(self.errors_found)}")
        print(f"🔧 الإصلاحات المطبقة: {len(self.fixes_applied)}")
        
        # تجميع الأخطاء حسب النوع
        error_types = {}
        for error in self.errors_found:
            error_type = error['type']
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(error)
        
        for error_type, errors in error_types.items():
            print(f"\n📂 {error_type}:")
            for error in errors:
                status = "✅ تم الإصلاح" if error['fix_applied'] else "❌ يحتاج إصلاح"
                print(f"   • {error['description']} - {status}")
        
        # حفظ التقرير في ملف
        try:
            with open("error_report.txt", "w", encoding="utf-8") as f:
                f.write("تقرير أخطاء النظام\n")
                f.write("=" * 30 + "\n")
                f.write(f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"إجمالي الأخطاء: {len(self.errors_found)}\n")
                f.write(f"الإصلاحات المطبقة: {len(self.fixes_applied)}\n\n")
                
                for error in self.errors_found:
                    f.write(f"النوع: {error['type']}\n")
                    f.write(f"الوصف: {error['description']}\n")
                    f.write(f"الوقت: {error['timestamp']}\n")
                    f.write(f"الإصلاح: {error['fix_applied'] or 'لم يتم'}\n")
                    f.write("-" * 30 + "\n")
            
            print(f"\n💾 تم حفظ التقرير في: error_report.txt")
            
        except Exception as e:
            print(f"❌ فشل في حفظ التقرير: {e}")
    
    def run_full_diagnosis(self):
        """تشغيل التشخيص الشامل"""
        print("🔧 بدء التشخيص الشامل للنظام")
        print("👨‍💻 المهندس هشام المجمر - 773988932")
        print("=" * 60)
        
        # فحص بنية قاعدة البيانات
        self.check_database_structure()
        
        # فحص بيانات المبيعات
        self.check_sales_data_integrity()
        
        # فحص بيانات المنتجات
        self.check_products_data()
        
        # فحص ملفات النظام
        self.check_system_files()
        
        # اختبار الاستيراد
        self.test_system_imports()
        
        # إنشاء التقرير
        self.generate_error_report()
        
        print("\n" + "=" * 60)
        print("✅ تم الانتهاء من التشخيص الشامل")
        print("📞 للدعم الفني: المهندس هشام المجمر - 773988932")
        print("=" * 60)

def main():
    """الدالة الرئيسية"""
    detector = SystemErrorDetector()
    detector.run_full_diagnosis()

if __name__ == "__main__":
    main()