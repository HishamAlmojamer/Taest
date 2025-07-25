#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أداة الفحص والإصلاح الشاملة للنظام
تصميم: المهندس هشام المجمر - 773988932
"""

import sys
import os
import sqlite3
import traceback
from datetime import datetime
import shutil
import json

# إضافة المجلد الحالي إلى مسار Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class CompleteSystemFixer:
    """كلاس الفحص والإصلاح الشامل للنظام"""
    
    def __init__(self):
        self.db_path = "warehouse_management.db"
        self.errors_found = []
        self.fixes_applied = []
        self.backup_created = False
    
    def log_error(self, error_type, description, severity="WARNING", fix_applied=None):
        """تسجيل الأخطاء"""
        error = {
            'type': error_type,
            'description': description,
            'severity': severity,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'fix_applied': fix_applied
        }
        self.errors_found.append(error)
        
        if fix_applied:
            self.fixes_applied.append(error)
        
        # طباعة الخطأ حسب الخطورة
        if severity == "CRITICAL":
            print(f"🚨 خطر: {description}")
        elif severity == "ERROR":
            print(f"❌ خطأ: {description}")
        elif severity == "WARNING":
            print(f"⚠️ تحذير: {description}")
        else:
            print(f"ℹ️ معلومة: {description}")
    
    def create_backup(self):
        """إنشاء نسخة احتياطية من قاعدة البيانات"""
        print("💾 إنشاء نسخة احتياطية...")
        
        try:
            if os.path.exists(self.db_path):
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                backup_path = os.path.join("backups", backup_name)
                
                # إنشاء مجلد النسخ الاحتياطية إذا لم يكن موجوداً
                os.makedirs("backups", exist_ok=True)
                
                shutil.copy2(self.db_path, backup_path)
                self.backup_created = True
                print(f"✅ تم إنشاء نسخة احتياطية: {backup_path}")
                return True
            else:
                print("⚠️ قاعدة البيانات غير موجودة")
                return False
                
        except Exception as e:
            self.log_error("BACKUP", f"فشل في إنشاء النسخة الاحتياطية: {e}", "ERROR")
            return False
    
    def check_database_existence(self):
        """فحص وجود قاعدة البيانات"""
        print("🔍 فحص وجود قاعدة البيانات...")
        
        if not os.path.exists(self.db_path):
            self.log_error("DATABASE", "قاعدة البيانات غير موجودة", "CRITICAL")
            return self.create_database()
        else:
            print("✅ قاعدة البيانات موجودة")
            return True
    
    def create_database(self):
        """إنشاء قاعدة البيانات من الصفر"""
        print("🔧 إنشاء قاعدة البيانات...")
        
        try:
            from database import Database
            db = Database()
            db.create_tables()
            self.log_error("DATABASE_CREATE", "تم إنشاء قاعدة البيانات", "INFO", "نجح")
            return True
        except Exception as e:
            self.log_error("DATABASE_CREATE", f"فشل في إنشاء قاعدة البيانات: {e}", "CRITICAL")
            return False
    
    def check_database_structure(self):
        """فحص بنية قاعدة البيانات"""
        print("🏗️ فحص بنية قاعدة البيانات...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # الجداول المطلوبة
            required_tables = {
                'users': [
                    'id INTEGER PRIMARY KEY AUTOINCREMENT',
                    'username TEXT UNIQUE NOT NULL',
                    'password TEXT NOT NULL',
                    'full_name TEXT',
                    'email TEXT',
                    'phone TEXT',
                    'role TEXT DEFAULT "user"',
                    'is_active INTEGER DEFAULT 1',
                    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                ],
                'categories': [
                    'id INTEGER PRIMARY KEY AUTOINCREMENT',
                    'name TEXT NOT NULL',
                    'description TEXT',
                    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                ],
                'products': [
                    'id INTEGER PRIMARY KEY AUTOINCREMENT',
                    'name TEXT NOT NULL',
                    'barcode TEXT UNIQUE',
                    'category_id INTEGER',
                    'unit TEXT DEFAULT "قطعة"',
                    'purchase_price REAL DEFAULT 0',
                    'selling_price REAL DEFAULT 0',
                    'stock INTEGER DEFAULT 0',
                    'min_stock INTEGER DEFAULT 0',
                    'description TEXT',
                    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                    'FOREIGN KEY (category_id) REFERENCES categories (id)'
                ],
                'customers': [
                    'id INTEGER PRIMARY KEY AUTOINCREMENT',
                    'name TEXT NOT NULL',
                    'phone TEXT',
                    'email TEXT',
                    'address TEXT',
                    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                ],
                'suppliers': [
                    'id INTEGER PRIMARY KEY AUTOINCREMENT',
                    'name TEXT NOT NULL',
                    'phone TEXT',
                    'email TEXT',
                    'address TEXT',
                    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                ],
                'sales': [
                    'id INTEGER PRIMARY KEY AUTOINCREMENT',
                    'customer_id INTEGER',
                    'user_id INTEGER DEFAULT 1',
                    'sale_date TEXT DEFAULT CURRENT_TIMESTAMP',
                    'subtotal REAL DEFAULT 0',
                    'discount REAL DEFAULT 0',
                    'discount_percent REAL DEFAULT 0',
                    'discount_amount REAL DEFAULT 0',
                    'tax_percent REAL DEFAULT 15',
                    'tax_amount REAL DEFAULT 0',
                    'total REAL DEFAULT 0',
                    'total_amount REAL DEFAULT 0',
                    'final_amount REAL DEFAULT 0',
                    'payment_method TEXT DEFAULT "نقدي"',
                    'payment_status TEXT DEFAULT "مدفوع"',
                    'notes TEXT',
                    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                    'FOREIGN KEY (customer_id) REFERENCES customers (id)',
                    'FOREIGN KEY (user_id) REFERENCES users (id)'
                ],
                'sale_items': [
                    'id INTEGER PRIMARY KEY AUTOINCREMENT',
                    'sale_id INTEGER NOT NULL',
                    'product_id INTEGER NOT NULL',
                    'quantity INTEGER NOT NULL',
                    'unit_price REAL NOT NULL',
                    'total REAL DEFAULT 0',
                    'total_price REAL DEFAULT 0',
                    'discount REAL DEFAULT 0',
                    'tax_amount REAL DEFAULT 0',
                    'FOREIGN KEY (sale_id) REFERENCES sales (id)',
                    'FOREIGN KEY (product_id) REFERENCES products (id)'
                ],
                'purchases': [
                    'id INTEGER PRIMARY KEY AUTOINCREMENT',
                    'supplier_id INTEGER',
                    'user_id INTEGER DEFAULT 1',
                    'purchase_date TEXT DEFAULT CURRENT_TIMESTAMP',
                    'total REAL DEFAULT 0',
                    'payment_status TEXT DEFAULT "مدفوع"',
                    'notes TEXT',
                    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                    'FOREIGN KEY (supplier_id) REFERENCES suppliers (id)',
                    'FOREIGN KEY (user_id) REFERENCES users (id)'
                ],
                'purchase_items': [
                    'id INTEGER PRIMARY KEY AUTOINCREMENT',
                    'purchase_id INTEGER NOT NULL',
                    'product_id INTEGER NOT NULL',
                    'quantity INTEGER NOT NULL',
                    'unit_price REAL NOT NULL',
                    'total REAL DEFAULT 0',
                    'FOREIGN KEY (purchase_id) REFERENCES purchases (id)',
                    'FOREIGN KEY (product_id) REFERENCES products (id)'
                ],
                'stock_movements': [
                    'id INTEGER PRIMARY KEY AUTOINCREMENT',
                    'product_id INTEGER NOT NULL',
                    'movement_type TEXT NOT NULL',
                    'quantity INTEGER NOT NULL',
                    'reference_id INTEGER',
                    'reference_type TEXT',
                    'notes TEXT',
                    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                    'FOREIGN KEY (product_id) REFERENCES products (id)'
                ]
            }
            
            # فحص الجداول الموجودة
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            # إنشاء الجداول المفقودة
            for table_name, columns in required_tables.items():
                if table_name not in existing_tables:
                    columns_sql = ', '.join(columns)
                    create_sql = f"CREATE TABLE {table_name} ({columns_sql})"
                    cursor.execute(create_sql)
                    self.log_error("TABLE_CREATE", f"تم إنشاء جدول {table_name}", "INFO", "نجح")
                else:
                    # فحص أعمدة الجدول الموجود
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    existing_columns = [col[1] for col in cursor.fetchall()]
                    
                    # إضافة الأعمدة المفقودة
                    for column_def in columns:
                        if 'PRIMARY KEY' in column_def or 'FOREIGN KEY' in column_def:
                            continue
                        
                        column_name = column_def.split()[0]
                        if column_name not in existing_columns:
                            try:
                                cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_def}')
                                self.log_error("COLUMN_ADD", f"تم إضافة عمود {column_name} لجدول {table_name}", "INFO", "نجح")
                            except Exception as e:
                                self.log_error("COLUMN_ADD", f"فشل في إضافة عمود {column_name}: {e}", "WARNING")
            
            conn.commit()
            conn.close()
            print("✅ تم فحص وإصلاح بنية قاعدة البيانات")
            return True
            
        except Exception as e:
            self.log_error("DATABASE_STRUCTURE", f"خطأ في فحص بنية قاعدة البيانات: {e}", "ERROR")
            return False
    
    def check_default_data(self):
        """فحص وإنشاء البيانات الافتراضية"""
        print("👤 فحص البيانات الافتراضية...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # فحص المستخدم الافتراضي
            cursor.execute('SELECT COUNT(*) FROM users WHERE username = "admin"')
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO users (username, password, full_name, role)
                    VALUES ("admin", "admin123", "مدير النظام", "admin")
                ''')
                self.log_error("DEFAULT_USER", "تم إنشاء المستخدم الافتراضي admin", "INFO", "نجح")
            
            # فحص الفئة الافتراضية
            cursor.execute('SELECT COUNT(*) FROM categories')
            if cursor.fetchone()[0] == 0:
                default_categories = [
                    ("فئة عامة", "فئة افتراضية للمنتجات"),
                    ("إلكترونيات", "الأجهزة الإلكترونية"),
                    ("ملابس", "الملابس والأزياء"),
                    ("طعام ومشروبات", "المواد الغذائية")
                ]
                
                for name, desc in default_categories:
                    cursor.execute('INSERT INTO categories (name, description) VALUES (?, ?)', (name, desc))
                
                self.log_error("DEFAULT_CATEGORIES", "تم إنشاء الفئات الافتراضية", "INFO", "نجح")
            
            # فحص العميل الافتراضي
            cursor.execute('SELECT COUNT(*) FROM customers WHERE name = "عميل مجهول"')
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO customers (name, phone, email, address)
                    VALUES ("عميل مجهول", "000000000", "unknown@system.local", "غير محدد")
                ''')
                self.log_error("DEFAULT_CUSTOMER", "تم إنشاء العميل الافتراضي", "INFO", "نجح")
            
            conn.commit()
            conn.close()
            print("✅ تم فحص البيانات الافتراضية")
            return True
            
        except Exception as e:
            self.log_error("DEFAULT_DATA", f"خطأ في فحص البيانات الافتراضية: {e}", "ERROR")
            return False
    
    def fix_sales_data(self):
        """إصلاح بيانات المبيعات"""
        print("💰 إصلاح بيانات المبيعات...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # إصلاح المبيعات بدون عملاء
            cursor.execute('''
                UPDATE sales 
                SET customer_id = (SELECT id FROM customers WHERE name = "عميل مجهول" LIMIT 1)
                WHERE customer_id IS NULL OR customer_id NOT IN (SELECT id FROM customers)
            ''')
            
            # إصلاح القيم السالبة
            cursor.execute('UPDATE sales SET total = ABS(total) WHERE total < 0')
            cursor.execute('UPDATE sales SET subtotal = ABS(subtotal) WHERE subtotal < 0')
            
            # حذف العناصر اليتيمة
            cursor.execute('DELETE FROM sale_items WHERE sale_id NOT IN (SELECT id FROM sales)')
            cursor.execute('DELETE FROM sale_items WHERE product_id NOT IN (SELECT id FROM products)')
            
            # إعادة حساب الإجماليات
            cursor.execute('SELECT id FROM sales')
            sales = cursor.fetchall()
            
            for (sale_id,) in sales:
                cursor.execute('''
                    SELECT COALESCE(SUM(quantity * unit_price), 0)
                    FROM sale_items WHERE sale_id = ?
                ''', (sale_id,))
                
                calculated_total = cursor.fetchone()[0]
                
                cursor.execute('''
                    UPDATE sales 
                    SET subtotal = ?, total = ?, final_amount = ?
                    WHERE id = ?
                ''', (calculated_total, calculated_total, calculated_total, sale_id))
            
            conn.commit()
            conn.close()
            
            self.log_error("SALES_FIX", "تم إصلاح بيانات المبيعات", "INFO", "نجح")
            print("✅ تم إصلاح بيانات المبيعات")
            return True
            
        except Exception as e:
            self.log_error("SALES_FIX", f"خطأ في إصلاح بيانات المبيعات: {e}", "ERROR")
            return False
    
    def fix_products_data(self):
        """إصلاح بيانات المنتجات"""
        print("📦 إصلاح بيانات المنتجات...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # إصلاح المنتجات بدون فئات
            cursor.execute('''
                UPDATE products 
                SET category_id = (SELECT id FROM categories WHERE name = "فئة عامة" LIMIT 1)
                WHERE category_id IS NULL OR category_id NOT IN (SELECT id FROM categories)
            ''')
            
            # إصلاح الأسعار السالبة أو الصفرية
            cursor.execute('UPDATE products SET selling_price = 1.0 WHERE selling_price <= 0')
            cursor.execute('UPDATE products SET purchase_price = 0.8 WHERE purchase_price < 0')
            
            # إصلاح المخزون السالب
            cursor.execute('UPDATE products SET stock = 0 WHERE stock < 0')
            cursor.execute('UPDATE products SET min_stock = 0 WHERE min_stock < 0')
            
            conn.commit()
            conn.close()
            
            self.log_error("PRODUCTS_FIX", "تم إصلاح بيانات المنتجات", "INFO", "نجح")
            print("✅ تم إصلاح بيانات المنتجات")
            return True
            
        except Exception as e:
            self.log_error("PRODUCTS_FIX", f"خطأ في إصلاح بيانات المنتجات: {e}", "ERROR")
            return False
    
    def check_system_files(self):
        """فحص ملفات النظام"""
        print("📁 فحص ملفات النظام...")
        
        required_files = [
            'database.py', 'login_window.py', 'main_window.py',
            'sales_window.py', 'products_window.py', 'customers_window.py',
            'suppliers_window.py', 'reports_window.py', 'category_window.py'
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
                self.log_error("MISSING_FILE", f"ملف مفقود: {file}", "WARNING")
        
        if not missing_files:
            print("✅ جميع ملفات النظام موجودة")
        
        # فحص الملفات المحسنة
        enhanced_files = [
            'ai_analytics.py', 'enhanced_sales_window.py',
            'enhanced_dashboard.py', 'enhanced_reports.py'
        ]
        
        for file in enhanced_files:
            if os.path.exists(file):
                print(f"✅ ملف محسن موجود: {file}")
        
        return len(missing_files) == 0
    
    def test_imports(self):
        """اختبار استيراد الملفات"""
        print("🔍 اختبار استيراد ملفات النظام...")
        
        modules_to_test = [
            'database', 'login_window', 'main_window',
            'sales_window', 'products_window', 'customers_window'
        ]
        
        import_errors = 0
        for module in modules_to_test:
            try:
                __import__(module)
                print(f"✅ {module}")
            except Exception as e:
                self.log_error("IMPORT_ERROR", f"خطأ في استيراد {module}: {e}", "ERROR")
                import_errors += 1
        
        return import_errors == 0
    
    def optimize_database(self):
        """تحسين قاعدة البيانات"""
        print("⚡ تحسين قاعدة البيانات...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # تنظيف قاعدة البيانات
            cursor.execute('VACUUM')
            
            # إعادة تحليل الإحصائيات
            cursor.execute('ANALYZE')
            
            # إنشاء فهارس للأداء
            indexes = [
                'CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)',
                'CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date)',
                'CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id)',
                'CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items(sale_id)',
                'CREATE INDEX IF NOT EXISTS idx_sale_items_product ON sale_items(product_id)'
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            conn.commit()
            conn.close()
            
            self.log_error("DB_OPTIMIZE", "تم تحسين قاعدة البيانات", "INFO", "نجح")
            print("✅ تم تحسين قاعدة البيانات")
            return True
            
        except Exception as e:
            self.log_error("DB_OPTIMIZE", f"خطأ في تحسين قاعدة البيانات: {e}", "ERROR")
            return False
    
    def generate_system_report(self):
        """إنشاء تقرير حالة النظام"""
        print("📊 إنشاء تقرير حالة النظام...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # إحصائيات النظام
            stats = {}
            
            cursor.execute('SELECT COUNT(*) FROM users')
            stats['users'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM products')
            stats['products'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM customers')
            stats['customers'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM sales')
            stats['sales'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(total) FROM sales WHERE total > 0')
            stats['total_sales'] = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM products WHERE stock <= min_stock')
            stats['low_stock'] = cursor.fetchone()[0]
            
            conn.close()
            
            # إنشاء التقرير
            report = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'system_stats': stats,
                'errors_found': len(self.errors_found),
                'fixes_applied': len(self.fixes_applied),
                'backup_created': self.backup_created,
                'errors': self.errors_found,
                'fixes': self.fixes_applied
            }
            
            # حفظ التقرير
            with open('system_report.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"📊 إحصائيات النظام:")
            print(f"   المستخدمون: {stats['users']}")
            print(f"   المنتجات: {stats['products']}")
            print(f"   العملاء: {stats['customers']}")
            print(f"   المبيعات: {stats['sales']} فاتورة")
            print(f"   إجمالي المبيعات: {stats['total_sales']:.2f} ر.س")
            print(f"   منتجات بمخزون منخفض: {stats['low_stock']}")
            
            print(f"\n💾 تم حفظ التقرير في: system_report.json")
            return True
            
        except Exception as e:
            self.log_error("SYSTEM_REPORT", f"خطأ في إنشاء التقرير: {e}", "ERROR")
            return False
    
    def run_complete_fix(self):
        """تشغيل الإصلاح الشامل"""
        print("🔧 بدء الفحص والإصلاح الشامل للنظام")
        print("👨‍💻 المهندس هشام المجمر - 773988932")
        print("🤖 نظام إدارة المخازن المتطور v3.0")
        print("=" * 70)
        
        # إنشاء نسخة احتياطية
        self.create_backup()
        
        # فحص وجود قاعدة البيانات
        self.check_database_existence()
        
        # فحص بنية قاعدة البيانات
        self.check_database_structure()
        
        # فحص البيانات الافتراضية
        self.check_default_data()
        
        # إصلاح بيانات المبيعات
        self.fix_sales_data()
        
        # إصلاح بيانات المنتجات
        self.fix_products_data()
        
        # فحص ملفات النظام
        self.check_system_files()
        
        # اختبار الاستيراد
        self.test_imports()
        
        # تحسين قاعدة البيانات
        self.optimize_database()
        
        # إنشاء تقرير النظام
        self.generate_system_report()
        
        # ملخص النتائج
        print("\n" + "=" * 70)
        print("📋 ملخص النتائج:")
        print(f"🔍 الأخطاء المكتشفة: {len(self.errors_found)}")
        print(f"🔧 الإصلاحات المطبقة: {len(self.fixes_applied)}")
        print(f"💾 نسخة احتياطية: {'تم إنشاؤها' if self.backup_created else 'لم يتم إنشاؤها'}")
        
        # تصنيف الأخطاء
        critical_errors = [e for e in self.errors_found if e['severity'] == 'CRITICAL']
        errors = [e for e in self.errors_found if e['severity'] == 'ERROR']
        warnings = [e for e in self.errors_found if e['severity'] == 'WARNING']
        
        if critical_errors:
            print(f"🚨 أخطاء حرجة: {len(critical_errors)}")
        if errors:
            print(f"❌ أخطاء: {len(errors)}")
        if warnings:
            print(f"⚠️ تحذيرات: {len(warnings)}")
        
        if not self.errors_found:
            print("🎉 النظام سليم ولا توجد أخطاء!")
        
        print("\n✅ تم الانتهاء من الفحص والإصلاح الشامل")
        print("📞 للدعم الفني: المهندس هشام المجمر - 773988932")
        print("=" * 70)

def main():
    """الدالة الرئيسية"""
    fixer = CompleteSystemFixer()
    fixer.run_complete_fix()

if __name__ == "__main__":
    main()