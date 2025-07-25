#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فاحص قاعدة البيانات وإصلاح الأخطاء
تصميم: المهندس هشام المجمر - 773988932
"""

import sqlite3
import os

def inspect_database():
    """فحص شامل لقاعدة البيانات"""
    db_path = "warehouse_management.db"
    
    if not os.path.exists(db_path):
        print("❌ قاعدة البيانات غير موجودة")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔍 فحص شامل لقاعدة البيانات")
        print("=" * 50)
        
        # الحصول على قائمة الجداول
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📋 عدد الجداول: {len(tables)}")
        print("الجداول الموجودة:")
        for table in tables:
            print(f"  • {table[0]}")
        
        print("\n" + "=" * 50)
        
        # فحص كل جدول
        for table_name in [t[0] for t in tables]:
            print(f"\n📊 جدول: {table_name}")
            print("-" * 30)
            
            # معلومات الأعمدة
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print("الأعمدة:")
            for col in columns:
                col_id, name, data_type, not_null, default, pk = col
                nullable = "NOT NULL" if not_null else "NULL"
                primary = "PRIMARY KEY" if pk else ""
                default_val = f"DEFAULT {default}" if default else ""
                print(f"  {name}: {data_type} {nullable} {default_val} {primary}")
            
            # عدد السجلات
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"عدد السجلات: {count}")
            
            # عرض بعض البيانات
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                sample_data = cursor.fetchall()
                print("عينة من البيانات:")
                for i, row in enumerate(sample_data, 1):
                    print(f"  السجل {i}: {row}")
        
    except Exception as e:
        print(f"❌ خطأ في الفحص: {e}")
    finally:
        conn.close()

def fix_database_columns():
    """إصلاح أعمدة قاعدة البيانات"""
    db_path = "warehouse_management.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n🔧 إصلاح أعمدة قاعدة البيانات")
        print("=" * 50)
        
        # إصلاح جدول المبيعات
        print("📝 إصلاح جدول المبيعات...")
        
        # فحص الأعمدة الحالية
        cursor.execute("PRAGMA table_info(sales)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # إضافة عمود total إذا لم يكن موجوداً
        if 'total' not in column_names:
            cursor.execute('ALTER TABLE sales ADD COLUMN total REAL DEFAULT 0')
            print("✅ تم إضافة عمود total")
            
            # نسخ البيانات من final_amount إلى total
            cursor.execute('UPDATE sales SET total = final_amount WHERE total IS NULL OR total = 0')
            print("✅ تم نسخ البيانات إلى عمود total")
        
        # إصلاح جدول المشتريات
        print("📝 إصلاح جدول المشتريات...")
        
        cursor.execute("PRAGMA table_info(purchases)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'total' not in column_names:
            cursor.execute('ALTER TABLE purchases ADD COLUMN total REAL DEFAULT 0')
            print("✅ تم إضافة عمود total للمشتريات")
            
            cursor.execute('UPDATE purchases SET total = final_amount WHERE total IS NULL OR total = 0')
            print("✅ تم نسخ البيانات إلى عمود total")
        
        # إصلاح جدول المنتجات
        print("📝 إصلاح جدول المنتجات...")
        
        cursor.execute("PRAGMA table_info(products)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'stock' not in column_names:
            cursor.execute('ALTER TABLE products ADD COLUMN stock INTEGER DEFAULT 0')
            print("✅ تم إضافة عمود stock")
            
            cursor.execute('UPDATE products SET stock = quantity WHERE stock IS NULL OR stock = 0')
            print("✅ تم نسخ البيانات إلى عمود stock")
        
        # إصلاح جدول sale_items
        print("📝 إصلاح جدول sale_items...")
        
        cursor.execute("PRAGMA table_info(sale_items)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'total' not in column_names:
            cursor.execute('ALTER TABLE sale_items ADD COLUMN total REAL DEFAULT 0')
            print("✅ تم إضافة عمود total لعناصر البيع")
            
            cursor.execute('UPDATE sale_items SET total = quantity * unit_price WHERE total IS NULL OR total = 0')
            print("✅ تم حساب الإجمالي لعناصر البيع")
        
        conn.commit()
        print("✅ تم إصلاح جميع الأعمدة بنجاح")
        
    except Exception as e:
        print(f"❌ خطأ في الإصلاح: {e}")
        conn.rollback()
    finally:
        conn.close()

def add_sample_data():
    """إضافة بيانات تجريبية شاملة"""
    db_path = "warehouse_management.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n📝 إضافة بيانات تجريبية شاملة")
        print("=" * 50)
        
        # إضافة فئات
        categories = [
            ("إلكترونيات", "أجهزة إلكترونية ومعدات تقنية"),
            ("ملابس", "ملابس وأزياء للرجال والنساء"),
            ("طعام ومشروبات", "مواد غذائية ومشروبات"),
            ("كتب وقرطاسية", "كتب ومواد قرطاسية"),
            ("رياضة وترفيه", "معدات رياضية وألعاب"),
            ("منزل ومطبخ", "أدوات منزلية ومطبخية"),
            ("صحة وجمال", "منتجات صحية وتجميل"),
            ("سيارات", "قطع غيار ومعدات سيارات")
        ]
        
        for name, desc in categories:
            try:
                cursor.execute('INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)', (name, desc))
            except:
                pass
        
        print("✅ تم إضافة الفئات")
        
        # إضافة منتجات متنوعة
        products = [
            # إلكترونيات
            ("لابتوب Dell Inspiron", 1, 2500.00, 15, 3, "DEL001", "قطعة"),
            ("هاتف Samsung Galaxy", 1, 1200.00, 25, 5, "SAM001", "قطعة"),
            ("سماعات Bluetooth", 1, 150.00, 40, 8, "BT001", "قطعة"),
            ("شاشة كمبيوتر 24 بوصة", 1, 800.00, 12, 2, "MON001", "قطعة"),
            ("كيبورد لاسلكي", 1, 85.00, 30, 6, "KEY001", "قطعة"),
            
            # ملابس
            ("قميص قطني رجالي", 2, 75.00, 50, 10, "SHI001", "قطعة"),
            ("فستان نسائي", 2, 120.00, 35, 7, "DRE001", "قطعة"),
            ("بنطلون جينز", 2, 95.00, 40, 8, "JEA001", "قطعة"),
            ("حذاء رياضي", 2, 180.00, 28, 5, "SHO001", "زوج"),
            ("جاكيت شتوي", 2, 200.00, 20, 4, "JAC001", "قطعة"),
            
            # طعام ومشروبات
            ("أرز بسمتي 5 كيلو", 3, 35.00, 100, 20, "RIC001", "كيس"),
            ("زيت زيتون 1 لتر", 3, 45.00, 60, 12, "OIL001", "زجاجة"),
            ("شاي أحمد 500 جرام", 3, 25.00, 80, 15, "TEA001", "علبة"),
            ("قهوة عربية 250 جرام", 3, 55.00, 45, 10, "COF001", "علبة"),
            ("عسل طبيعي 1 كيلو", 3, 85.00, 30, 6, "HON001", "برطمان"),
            
            # كتب وقرطاسية
            ("كتاب البرمجة بـ Python", 4, 120.00, 25, 5, "BOO001", "كتاب"),
            ("دفتر ملاحظات A4", 4, 15.00, 100, 20, "NOT001", "دفتر"),
            ("قلم حبر جاف", 4, 3.00, 200, 50, "PEN001", "قلم"),
            ("آلة حاسبة علمية", 4, 65.00, 18, 3, "CAL001", "قطعة"),
            ("مجلد ملفات", 4, 12.00, 75, 15, "FOL001", "مجلد"),
            
            # رياضة وترفيه
            ("كرة قدم", 5, 75.00, 30, 6, "BAL001", "كرة"),
            ("دراجة هوائية", 5, 450.00, 8, 2, "BIK001", "دراجة"),
            ("حبل قفز", 5, 25.00, 50, 10, "ROP001", "حبل"),
            ("أثقال 10 كيلو", 5, 120.00, 15, 3, "WEI001", "زوج"),
            ("مضرب تنس", 5, 95.00, 20, 4, "RAC001", "مضرب")
        ]
        
        for name, cat_id, price, stock, min_stock, barcode, unit in products:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO products 
                    (name, category_id, price, stock, min_stock, barcode, unit, quantity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, cat_id, price, stock, min_stock, barcode, unit, stock))
            except Exception as e:
                print(f"خطأ في إضافة منتج {name}: {e}")
        
        print("✅ تم إضافة المنتجات")
        
        # إضافة عملاء
        customers = [
            ("أحمد محمد علي", "0501234567", "ahmed.mohammed@email.com", "الرياض، حي النخيل"),
            ("فاطمة سالم أحمد", "0507654321", "fatima.salem@email.com", "جدة، حي الروضة"),
            ("محمد عبدالله سعد", "0509876543", "mohammed.abdullah@email.com", "الدمام، حي الفيصلية"),
            ("نورا خالد محمد", "0512345678", "nora.khaled@email.com", "مكة، حي العزيزية"),
            ("عبدالرحمن يوسف", "0598765432", "abdulrahman.youssef@email.com", "المدينة، حي قباء"),
            ("سارة أحمد علي", "0534567890", "sara.ahmed@email.com", "الطائف، حي الشفا"),
            ("خالد محمد سعد", "0556789012", "khaled.mohammed@email.com", "أبها، حي المنهل"),
            ("مريم عبدالله", "0578901234", "mariam.abdullah@email.com", "تبوك، حي السليمانية"),
            ("يوسف سالم أحمد", "0523456789", "youssef.salem@email.com", "حائل، حي الوسيطاء"),
            ("هند خالد محمد", "0545678901", "hind.khaled@email.com", "الخبر، حي الراكة")
        ]
        
        for name, phone, email, address in customers:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO customers (name, phone, email, address)
                    VALUES (?, ?, ?, ?)
                ''', (name, phone, email, address))
            except:
                pass
        
        print("✅ تم إضافة العملاء")
        
        # إضافة موردين
        suppliers = [
            ("شركة التقنية المتقدمة", "0112345678", "info@advanced-tech.com", "الرياض، طريق الملك فهد"),
            ("مؤسسة الأزياء العصرية", "0126789012", "sales@modern-fashion.com", "جدة، شارع التحلية"),
            ("شركة المواد الغذائية", "0138901234", "orders@food-supplies.com", "الدمام، الحي التجاري"),
            ("دار الكتب والمعرفة", "0145678901", "info@knowledge-books.com", "الرياض، حي الملز"),
            ("شركة المعدات الرياضية", "0156789012", "sales@sports-equipment.com", "جدة، حي الحمراء")
        ]
        
        for name, phone, email, address in suppliers:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO suppliers (name, phone, email, address)
                    VALUES (?, ?, ?, ?)
                ''', (name, phone, email, address))
            except:
                pass
        
        print("✅ تم إضافة الموردين")
        
        # إضافة مبيعات تجريبية
        from datetime import datetime, timedelta
        import random
        
        print("📊 إضافة مبيعات تجريبية...")
        
        for i in range(20):
            try:
                # تاريخ عشوائي في آخر 30 يوم
                days_ago = random.randint(1, 30)
                sale_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
                
                customer_id = random.randint(1, 10)
                subtotal = random.uniform(100, 1000)
                discount = random.uniform(0, subtotal * 0.1)
                tax = subtotal * 0.15  # ضريبة 15%
                total = subtotal - discount + tax
                
                cursor.execute('''
                    INSERT INTO sales 
                    (customer_id, user_id, sale_date, subtotal, discount, tax_amount, total, 
                     total_amount, final_amount, payment_method, payment_status, created_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (customer_id, 1, sale_date, subtotal, discount, tax, total, 
                      total, total, "نقدي", "مدفوع", 1, sale_date))
                
                sale_id = cursor.lastrowid
                
                # إضافة عناصر البيع
                num_items = random.randint(1, 5)
                for j in range(num_items):
                    product_id = random.randint(1, 25)
                    quantity = random.randint(1, 5)
                    unit_price = random.uniform(20, 200)
                    item_total = quantity * unit_price
                    
                    cursor.execute('''
                        INSERT INTO sale_items 
                        (sale_id, product_id, quantity, unit_price, total)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (sale_id, product_id, quantity, unit_price, item_total))
                
            except Exception as e:
                print(f"تحذير: فشل في إضافة بيع {i+1}: {e}")
        
        print("✅ تم إضافة المبيعات التجريبية")
        
        # إضافة مشتريات تجريبية
        print("📦 إضافة مشتريات تجريبية...")
        
        for i in range(10):
            try:
                days_ago = random.randint(1, 60)
                purchase_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
                
                supplier_id = random.randint(1, 5)
                subtotal = random.uniform(500, 2000)
                discount = random.uniform(0, subtotal * 0.05)
                total = subtotal - discount
                
                cursor.execute('''
                    INSERT INTO purchases 
                    (supplier_id, user_id, purchase_date, subtotal, total, 
                     total_amount, final_amount, payment_status, created_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (supplier_id, 1, purchase_date, subtotal, total, 
                      total, total, "مدفوع", 1, purchase_date))
                
                purchase_id = cursor.lastrowid
                
                # إضافة عناصر الشراء
                num_items = random.randint(2, 6)
                for j in range(num_items):
                    product_id = random.randint(1, 25)
                    quantity = random.randint(5, 20)
                    unit_price = random.uniform(15, 150)
                    item_total = quantity * unit_price
                    
                    cursor.execute('''
                        INSERT INTO purchase_items 
                        (purchase_id, product_id, quantity, unit_price, total)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (purchase_id, product_id, quantity, unit_price, item_total))
                
            except Exception as e:
                print(f"تحذير: فشل في إضافة شراء {i+1}: {e}")
        
        print("✅ تم إضافة المشتريات التجريبية")
        
        conn.commit()
        print("\n🎉 تم إضافة جميع البيانات التجريبية بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ في إضافة البيانات: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    """الدالة الرئيسية"""
    print("🔧 فاحص وإصلاح قاعدة البيانات")
    print("👨‍💻 المهندس هشام المجمر - 773988932")
    print("=" * 60)
    
    # فحص قاعدة البيانات
    inspect_database()
    
    # إصلاح الأعمدة
    fix_database_columns()
    
    # إضافة بيانات تجريبية
    add_sample_data()
    
    print("\n" + "=" * 60)
    print("✅ تم الانتهاء من فحص وإصلاح قاعدة البيانات")
    print("🚀 النظام جاهز الآن للاستخدام مع البيانات الكاملة")
    print("=" * 60)

if __name__ == "__main__":
    main()