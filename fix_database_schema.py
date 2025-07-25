#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إصلاح مخطط قاعدة البيانات للنظام المحدث
تصميم: المهندس هشام المجمر - 773988932
"""

import sqlite3
import os

def fix_sales_table():
    """إصلاح جدول المبيعات"""
    db_path = "warehouse_management.db"
    
    if not os.path.exists(db_path):
        print("❌ قاعدة البيانات غير موجودة")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # فحص أعمدة جدول المبيعات
        cursor.execute("PRAGMA table_info(sales)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print("أعمدة جدول المبيعات الحالية:", column_names)
        
        # إضافة الأعمدة المفقودة
        missing_columns = [
            ("user_id", "INTEGER REFERENCES users(id)"),
            ("sale_date", "TEXT DEFAULT CURRENT_TIMESTAMP"),
            ("subtotal", "REAL DEFAULT 0"),
            ("discount_percent", "REAL DEFAULT 0"),
            ("discount_amount", "REAL DEFAULT 0"),
            ("tax_percent", "REAL DEFAULT 0"),
            ("tax_amount", "REAL DEFAULT 0"),
            ("payment_method", "TEXT DEFAULT 'نقدي'"),
            ("notes", "TEXT")
        ]
        
        for column_name, column_def in missing_columns:
            if column_name not in column_names:
                try:
                    cursor.execute(f'ALTER TABLE sales ADD COLUMN {column_name} {column_def}')
                    print(f"✅ تم إضافة عمود {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"⚠️ تحذير: فشل في إضافة عمود {column_name}: {e}")
            else:
                print(f"✅ عمود {column_name} موجود بالفعل")
        
        # تحديث البيانات الموجودة
        cursor.execute('''
            UPDATE sales 
            SET user_id = 1, 
                sale_date = COALESCE(sale_date, datetime('now')),
                subtotal = COALESCE(subtotal, total),
                payment_method = COALESCE(payment_method, 'نقدي')
            WHERE user_id IS NULL OR sale_date IS NULL
        ''')
        
        conn.commit()
        print("✅ تم إصلاح جدول المبيعات بنجاح")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إصلاح جدول المبيعات: {e}")
        return False
    finally:
        conn.close()

def fix_purchases_table():
    """إصلاح جدول المشتريات"""
    db_path = "warehouse_management.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # فحص أعمدة جدول المشتريات
        cursor.execute("PRAGMA table_info(purchases)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print("أعمدة جدول المشتريات الحالية:", column_names)
        
        # إضافة الأعمدة المفقودة
        missing_columns = [
            ("user_id", "INTEGER REFERENCES users(id)"),
            ("purchase_date", "TEXT DEFAULT CURRENT_TIMESTAMP"),
            ("subtotal", "REAL DEFAULT 0"),
            ("tax_amount", "REAL DEFAULT 0"),
            ("notes", "TEXT")
        ]
        
        for column_name, column_def in missing_columns:
            if column_name not in column_names:
                try:
                    cursor.execute(f'ALTER TABLE purchases ADD COLUMN {column_name} {column_def}')
                    print(f"✅ تم إضافة عمود {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"⚠️ تحذير: فشل في إضافة عمود {column_name}: {e}")
            else:
                print(f"✅ عمود {column_name} موجود بالفعل")
        
        # تحديث البيانات الموجودة
        cursor.execute('''
            UPDATE purchases 
            SET user_id = 1, 
                purchase_date = COALESCE(purchase_date, datetime('now')),
                subtotal = COALESCE(subtotal, total)
            WHERE user_id IS NULL OR purchase_date IS NULL
        ''')
        
        conn.commit()
        print("✅ تم إصلاح جدول المشتريات بنجاح")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إصلاح جدول المشتريات: {e}")
        return False
    finally:
        conn.close()

def create_indexes():
    """إنشاء فهارس لتحسين الأداء"""
    db_path = "warehouse_management.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date)",
            "CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_user ON sales(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items(sale_id)",
            "CREATE INDEX IF NOT EXISTS idx_sale_items_product ON sale_items(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_purchases_date ON purchases(purchase_date)",
            "CREATE INDEX IF NOT EXISTS idx_purchases_supplier ON purchases(supplier_id)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_items_purchase ON purchase_items(purchase_id)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_items_product ON purchase_items(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)",
            "CREATE INDEX IF NOT EXISTS idx_products_stock ON products(stock)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print(f"✅ تم إنشاء فهرس")
            except sqlite3.OperationalError as e:
                print(f"⚠️ تحذير في إنشاء الفهرس: {e}")
        
        conn.commit()
        print("✅ تم إنشاء جميع الفهارس بنجاح")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء الفهارس: {e}")
        return False
    finally:
        conn.close()

def main():
    """الدالة الرئيسية"""
    print("🔧 إصلاح مخطط قاعدة البيانات للنظام المحدث")
    print("👨‍💻 المهندس هشام المجمر - 773988932")
    print("=" * 50)
    
    try:
        # إصلاح جدول المبيعات
        print("\n1️⃣ إصلاح جدول المبيعات...")
        fix_sales_table()
        
        # إصلاح جدول المشتريات
        print("\n2️⃣ إصلاح جدول المشتريات...")
        fix_purchases_table()
        
        # إنشاء الفهارس
        print("\n3️⃣ إنشاء فهارس الأداء...")
        create_indexes()
        
        print("\n✅ تم إصلاح قاعدة البيانات بنجاح!")
        print("🚀 النظام جاهز للاستخدام")
        
    except Exception as e:
        print(f"\n❌ خطأ عام: {e}")

if __name__ == "__main__":
    main()