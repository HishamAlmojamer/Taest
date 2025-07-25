#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إصلاح شامل لقاعدة البيانات مع توحيد أسماء الأعمدة
تصميم: المهندس هشام المجمر - 773988932
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

def fix_all_tables():
    """إصلاح شامل لجميع الجداول"""
    db_path = "warehouse_management.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔧 إصلاح شامل لقاعدة البيانات")
        print("=" * 50)
        
        # إصلاح جدول المنتجات
        print("📦 إصلاح جدول المنتجات...")
        
        cursor.execute("PRAGMA table_info(products)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # إضافة الأعمدة المفقودة
        missing_columns = [
            ("price", "REAL DEFAULT 0"),
            ("stock", "INTEGER DEFAULT 0"),
            ("quantity", "INTEGER DEFAULT 0")
        ]
        
        for column_name, column_def in missing_columns:
            if column_name not in column_names:
                cursor.execute(f'ALTER TABLE products ADD COLUMN {column_name} {column_def}')
                print(f"✅ تم إضافة عمود {column_name}")
        
        # نسخ البيانات من الأعمدة الموجودة
        cursor.execute('''
            UPDATE products 
            SET price = COALESCE(selling_price, 0),
                stock = COALESCE(current_stock, 0),
                quantity = COALESCE(current_stock, 0)
            WHERE price IS NULL OR price = 0
        ''')
        
        # إصلاح جدول المبيعات
        print("💰 إصلاح جدول المبيعات...")
        
        cursor.execute("PRAGMA table_info(sales)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'total' not in column_names:
            cursor.execute('ALTER TABLE sales ADD COLUMN total REAL DEFAULT 0')
            print("✅ تم إضافة عمود total للمبيعات")
        
        cursor.execute('''
            UPDATE sales 
            SET total = COALESCE(final_amount, total_amount, 0)
            WHERE total IS NULL OR total = 0
        ''')
        
        # إصلاح جدول المشتريات
        print("📋 إصلاح جدول المشتريات...")
        
        cursor.execute("PRAGMA table_info(purchases)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'total' not in column_names:
            cursor.execute('ALTER TABLE purchases ADD COLUMN total REAL DEFAULT 0')
            print("✅ تم إضافة عمود total للمشتريات")
        
        cursor.execute('''
            UPDATE purchases 
            SET total = COALESCE(final_amount, total_amount, 0)
            WHERE total IS NULL OR total = 0
        ''')
        
        # إصلاح جدول عناصر البيع
        print("🛒 إصلاح جدول عناصر البيع...")
        
        cursor.execute("PRAGMA table_info(sale_items)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'total' not in column_names:
            cursor.execute('ALTER TABLE sale_items ADD COLUMN total REAL DEFAULT 0')
            print("✅ تم إضافة عمود total لعناصر البيع")
        
        cursor.execute('''
            UPDATE sale_items 
            SET total = COALESCE(total_price, quantity * unit_price, 0)
            WHERE total IS NULL OR total = 0
        ''')
        
        # إصلاح جدول عناصر المشتريات
        print("📦 إصلاح جدول عناصر المشتريات...")
        
        cursor.execute("PRAGMA table_info(purchase_items)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'total' not in column_names:
            cursor.execute('ALTER TABLE purchase_items ADD COLUMN total REAL DEFAULT 0')
            print("✅ تم إضافة عمود total لعناصر المشتريات")
        
        cursor.execute('''
            UPDATE purchase_items 
            SET total = COALESCE(total_price, quantity * unit_price, 0)
            WHERE total IS NULL OR total = 0
        ''')
        
        conn.commit()
        print("✅ تم إصلاح جميع الجداول بنجاح")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في الإصلاح: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def add_comprehensive_sample_data():
    """إضافة بيانات تجريبية شاملة ومصححة"""
    db_path = "warehouse_management.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n📝 إضافة بيانات تجريبية شاملة")
        print("=" * 50)
        
        # مسح البيانات القديمة (اختياري)
        # cursor.execute('DELETE FROM sale_items')
        # cursor.execute('DELETE FROM sales')
        # cursor.execute('DELETE FROM purchase_items')
        # cursor.execute('DELETE FROM purchases')
        
        # إضافة منتجات بالأعمدة الصحيحة
        products = [
            # (name, category_id, selling_price, stock, min_stock, barcode, unit, purchase_price)
            ("لابتوب Dell Inspiron 15", 2, 2500.00, 15, 3, "DEL001", "قطعة", 2200.00),
            ("هاتف Samsung Galaxy S23", 2, 1200.00, 25, 5, "SAM001", "قطعة", 1000.00),
            ("سماعات Bluetooth JBL", 2, 150.00, 40, 8, "JBL001", "قطعة", 120.00),
            ("شاشة كمبيوتر 24 بوصة", 2, 800.00, 12, 2, "MON001", "قطعة", 650.00),
            ("كيبورد لاسلكي Logitech", 2, 85.00, 30, 6, "LOG001", "قطعة", 65.00),
            
            ("قميص قطني رجالي", 3, 75.00, 50, 10, "SHI001", "قطعة", 45.00),
            ("فستان نسائي أنيق", 3, 120.00, 35, 7, "DRE001", "قطعة", 80.00),
            ("بنطلون جينز", 3, 95.00, 40, 8, "JEA001", "قطعة", 65.00),
            ("حذاء رياضي Nike", 3, 180.00, 28, 5, "NIK001", "زوج", 140.00),
            ("جاكيت شتوي", 3, 200.00, 20, 4, "JAC001", "قطعة", 150.00),
            
            ("أرز بسمتي 5 كيلو", 4, 35.00, 100, 20, "RIC001", "كيس", 28.00),
            ("زيت زيتون 1 لتر", 4, 45.00, 60, 12, "OIL001", "زجاجة", 35.00),
            ("شاي أحمد 500 جرام", 4, 25.00, 80, 15, "TEA001", "علبة", 18.00),
            ("قهوة عربية 250 جرام", 4, 55.00, 45, 10, "COF001", "علبة", 40.00),
            ("عسل طبيعي 1 كيلو", 4, 85.00, 30, 6, "HON001", "برطمان", 65.00),
            
            ("كتاب البرمجة بـ Python", 5, 120.00, 25, 5, "BOO001", "كتاب", 90.00),
            ("دفتر ملاحظات A4", 5, 15.00, 100, 20, "NOT001", "دفتر", 10.00),
            ("قلم حبر جاف", 5, 3.00, 200, 50, "PEN001", "قلم", 2.00),
            ("آلة حاسبة علمية", 5, 65.00, 18, 3, "CAL001", "قطعة", 45.00),
            ("مجلد ملفات", 5, 12.00, 75, 15, "FOL001", "مجلد", 8.00),
            
            ("كرة قدم", 6, 75.00, 30, 6, "BAL001", "كرة", 55.00),
            ("دراجة هوائية", 6, 450.00, 8, 2, "BIK001", "دراجة", 350.00),
            ("حبل قفز", 6, 25.00, 50, 10, "ROP001", "حبل", 18.00),
            ("أثقال 10 كيلو", 6, 120.00, 15, 3, "WEI001", "زوج", 90.00),
            ("مضرب تنس", 6, 95.00, 20, 4, "RAC001", "مضرب", 70.00)
        ]
        
        print("📦 إضافة المنتجات...")
        for name, cat_id, selling_price, stock, min_stock, barcode, unit, purchase_price in products:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO products 
                    (name, category_id, selling_price, stock, min_stock, barcode, unit, purchase_price, 
                     current_stock, price, quantity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, cat_id, selling_price, stock, min_stock, barcode, unit, purchase_price, 
                      stock, selling_price, stock))
                print(f"✅ تم إضافة: {name}")
            except Exception as e:
                print(f"❌ خطأ في إضافة {name}: {e}")
        
        # إضافة عملاء إضافيين
        additional_customers = [
            ("سعد محمد الأحمد", "0567890123", "saad.mohammed@email.com", "الرياض، حي الملقا"),
            ("ليلى عبدالعزيز", "0589012345", "layla.abdulaziz@email.com", "جدة، حي الزهراء"),
            ("عمر سالم القحطاني", "0512345679", "omar.salem@email.com", "الدمام، حي الشاطئ"),
            ("هدى أحمد المطيري", "0534567891", "huda.ahmed@email.com", "الطائف، حي السلامة"),
            ("ماجد خالد العتيبي", "0556789013", "majed.khaled@email.com", "أبها، حي الأندلس")
        ]
        
        print("👥 إضافة عملاء إضافيين...")
        for name, phone, email, address in additional_customers:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO customers (name, phone, email, address)
                    VALUES (?, ?, ?, ?)
                ''', (name, phone, email, address))
            except:
                pass
        
        # إضافة مبيعات تجريبية مع البيانات الصحيحة
        print("💰 إضافة مبيعات تجريبية...")
        
        for i in range(30):
            try:
                # تاريخ عشوائي في آخر 60 يوم
                days_ago = random.randint(1, 60)
                sale_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
                
                customer_id = random.randint(1, 10)
                
                # إنشاء البيع أولاً
                cursor.execute('''
                    INSERT INTO sales 
                    (customer_id, user_id, sale_date, subtotal, discount, tax_amount, total, 
                     total_amount, final_amount, payment_method, payment_status, created_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (customer_id, 1, sale_date, 0, 0, 0, 0, 0, 0, "نقدي", "مدفوع", 1, sale_date))
                
                sale_id = cursor.lastrowid
                
                # إضافة عناصر البيع
                num_items = random.randint(1, 5)
                sale_total = 0
                
                for j in range(num_items):
                    product_id = random.randint(1, 25)
                    quantity = random.randint(1, 5)
                    
                    # الحصول على سعر المنتج
                    cursor.execute('SELECT selling_price FROM products WHERE id = ?', (product_id,))
                    result = cursor.fetchone()
                    unit_price = result[0] if result else 50.0
                    
                    item_total = quantity * unit_price
                    sale_total += item_total
                    
                    cursor.execute('''
                        INSERT INTO sale_items 
                        (sale_id, product_id, quantity, unit_price, total, total_price)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (sale_id, product_id, quantity, unit_price, item_total, item_total))
                
                # تحديث إجمالي البيع
                tax = sale_total * 0.15  # ضريبة 15%
                discount = random.uniform(0, sale_total * 0.1)
                final_total = sale_total - discount + tax
                
                cursor.execute('''
                    UPDATE sales 
                    SET subtotal = ?, tax_amount = ?, discount = ?, total = ?, 
                        total_amount = ?, final_amount = ?
                    WHERE id = ?
                ''', (sale_total, tax, discount, final_total, final_total, final_total, sale_id))
                
                if i % 5 == 0:
                    print(f"✅ تم إضافة {i+1} مبيعات")
                
            except Exception as e:
                print(f"❌ خطأ في إضافة بيع {i+1}: {e}")
        
        # إضافة مشتريات تجريبية
        print("📦 إضافة مشتريات تجريبية...")
        
        for i in range(15):
            try:
                days_ago = random.randint(1, 90)
                purchase_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
                
                supplier_id = random.randint(1, 5)
                
                # إنشاء الشراء أولاً
                cursor.execute('''
                    INSERT INTO purchases 
                    (supplier_id, user_id, purchase_date, subtotal, total, 
                     total_amount, final_amount, payment_status, created_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (supplier_id, 1, purchase_date, 0, 0, 0, 0, "مدفوع", 1, purchase_date))
                
                purchase_id = cursor.lastrowid
                
                # إضافة عناصر الشراء
                num_items = random.randint(2, 6)
                purchase_total = 0
                
                for j in range(num_items):
                    product_id = random.randint(1, 25)
                    quantity = random.randint(5, 20)
                    
                    # الحصول على سعر الشراء
                    cursor.execute('SELECT purchase_price FROM products WHERE id = ?', (product_id,))
                    result = cursor.fetchone()
                    unit_price = result[0] if result else 30.0
                    
                    item_total = quantity * unit_price
                    purchase_total += item_total
                    
                    cursor.execute('''
                        INSERT INTO purchase_items 
                        (purchase_id, product_id, quantity, unit_price, total, total_price)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (purchase_id, product_id, quantity, unit_price, item_total, item_total))
                
                # تحديث إجمالي الشراء
                discount = random.uniform(0, purchase_total * 0.05)
                final_total = purchase_total - discount
                
                cursor.execute('''
                    UPDATE purchases 
                    SET subtotal = ?, discount = ?, total = ?, 
                        total_amount = ?, final_amount = ?
                    WHERE id = ?
                ''', (purchase_total, discount, final_total, final_total, final_total, purchase_id))
                
                if i % 3 == 0:
                    print(f"✅ تم إضافة {i+1} مشتريات")
                
            except Exception as e:
                print(f"❌ خطأ في إضافة شراء {i+1}: {e}")
        
        conn.commit()
        print("\n🎉 تم إضافة جميع البيانات التجريبية بنجاح!")
        
        # عرض إحصائيات
        cursor.execute('SELECT COUNT(*) FROM products')
        products_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM customers')
        customers_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sales')
        sales_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM purchases')
        purchases_count = cursor.fetchone()[0]
        
        print(f"\n📊 إحصائيات البيانات:")
        print(f"   المنتجات: {products_count}")
        print(f"   العملاء: {customers_count}")
        print(f"   المبيعات: {sales_count}")
        print(f"   المشتريات: {purchases_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إضافة البيانات: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def verify_database():
    """التحقق من صحة قاعدة البيانات"""
    db_path = "warehouse_management.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n🔍 التحقق من صحة قاعدة البيانات")
        print("=" * 50)
        
        # فحص الجداول الأساسية
        tables_to_check = ['products', 'customers', 'sales', 'sale_items', 'purchases', 'purchase_items']
        
        for table in tables_to_check:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f"✅ جدول {table}: {count} سجل")
        
        # فحص الأعمدة المطلوبة
        required_columns = {
            'products': ['id', 'name', 'price', 'stock', 'selling_price'],
            'sales': ['id', 'customer_id', 'total', 'sale_date'],
            'sale_items': ['id', 'sale_id', 'product_id', 'total'],
            'purchases': ['id', 'supplier_id', 'total'],
            'purchase_items': ['id', 'purchase_id', 'product_id', 'total']
        }
        
        for table, columns in required_columns.items():
            cursor.execute(f"PRAGMA table_info({table})")
            existing_columns = [col[1] for col in cursor.fetchall()]
            
            missing = [col for col in columns if col not in existing_columns]
            if missing:
                print(f"⚠️ جدول {table} يفتقد الأعمدة: {missing}")
            else:
                print(f"✅ جدول {table}: جميع الأعمدة موجودة")
        
        # اختبار استعلام بسيط
        cursor.execute('''
            SELECT p.name, p.price, p.stock 
            FROM products p 
            LIMIT 3
        ''')
        products = cursor.fetchall()
        
        if products:
            print(f"\n📦 عينة من المنتجات:")
            for name, price, stock in products:
                print(f"   {name}: {price} ر.س (مخزون: {stock})")
        
        # اختبار استعلام المبيعات
        cursor.execute('''
            SELECT s.id, c.name, s.total, s.sale_date
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
            LIMIT 3
        ''')
        sales = cursor.fetchall()
        
        if sales:
            print(f"\n💰 عينة من المبيعات:")
            for sale_id, customer, total, date in sales:
                print(f"   فاتورة {sale_id}: {customer or 'عميل مجهول'} - {total} ر.س")
        
        print("\n✅ قاعدة البيانات سليمة وجاهزة للاستخدام!")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في التحقق: {e}")
        return False
    finally:
        conn.close()

def main():
    """الدالة الرئيسية"""
    print("🔧 إصلاح شامل لقاعدة البيانات")
    print("👨‍💻 المهندس هشام المجمر - 773988932")
    print("=" * 60)
    
    try:
        # إصلاح الجداول
        if fix_all_tables():
            print("✅ تم إصلاح الجداول بنجاح")
        else:
            print("❌ فشل في إصلاح الجداول")
            return
        
        # إضافة البيانات التجريبية
        if add_comprehensive_sample_data():
            print("✅ تم إضافة البيانات التجريبية بنجاح")
        else:
            print("❌ فشل في إضافة البيانات التجريبية")
            return
        
        # التحقق من النتائج
        if verify_database():
            print("✅ تم التحقق من قاعدة البيانات بنجاح")
        
        print("\n" + "=" * 60)
        print("🎉 تم إصلاح قاعدة البيانات بالكامل!")
        print("🚀 النظام جاهز الآن مع بيانات شاملة للعرض")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ خطأ عام: {e}")

if __name__ == "__main__":
    main()