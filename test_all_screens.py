#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار جميع الشاشات مع البيانات المُصححة
تصميم: المهندس هشام المجمر - 773988932
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import threading
import time

# إضافة المجلد الحالي إلى مسار Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """اختبار الاتصال بقاعدة البيانات"""
    print("🔍 اختبار الاتصال بقاعدة البيانات...")
    
    try:
        from database import Database
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # اختبار الجداول الأساسية
        tables = ['products', 'customers', 'sales', 'purchases', 'categories', 'suppliers']
        
        for table in tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f"✅ جدول {table}: {count} سجل")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ خطأ في قاعدة البيانات: {e}")
        return False

def test_login_system():
    """اختبار نظام تسجيل الدخول"""
    print("\n🔐 اختبار نظام تسجيل الدخول...")
    
    try:
        from database import Database
        db = Database()
        
        # اختبار تسجيل الدخول
        user = db.authenticate_user("admin", "admin123")
        
        if user:
            print(f"✅ تسجيل الدخول نجح: {user['full_name']}")
            print(f"   الدور: {user['role']}")
            return True
        else:
            print("❌ فشل في تسجيل الدخول")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في نظام تسجيل الدخول: {e}")
        return False

def test_ai_analytics():
    """اختبار محرك التحليلات الذكي"""
    print("\n🤖 اختبار محرك التحليلات الذكي...")
    
    try:
        from ai_analytics import AIAnalyticsEngine
        
        ai_engine = AIAnalyticsEngine("warehouse_management.db")
        
        # اختبار تحليل أنماط المبيعات
        patterns = ai_engine.analyze_sales_patterns(30)
        print("✅ تحليل أنماط المبيعات يعمل")
        
        # اختبار توقع الطلب
        prediction = ai_engine.predict_demand(1, 7)
        print("✅ توقع الطلب يعمل")
        
        # اختبار الرؤى التجارية
        insights = ai_engine.generate_business_insights()
        print(f"✅ تم توليد {len(insights)} رؤية تجارية")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في محرك التحليلات: {e}")
        return False

def test_enhanced_sales_window():
    """اختبار نقطة البيع المحسنة"""
    print("\n🛒 اختبار نقطة البيع المحسنة...")
    
    try:
        from enhanced_sales_window import AIRecommendationEngine, SmartPriceCalculator
        from database import Database
        
        db = Database()
        
        # اختبار محرك التوصيات
        ai_engine = AIRecommendationEngine(db)
        trending = ai_engine.get_trending_products()
        print(f"✅ محرك التوصيات: {len(trending)} منتج رائج")
        
        # اختبار حاسبة الأسعار الذكية
        price_calculator = SmartPriceCalculator(db)
        discount = price_calculator.suggest_discount(1, 5)
        print(f"✅ حاسبة الأسعار الذكية: خصم مقترح {discount}%")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في نقطة البيع المحسنة: {e}")
        return False

def test_enhanced_dashboard():
    """اختبار لوحة التحكم المحسنة"""
    print("\n🎛️ اختبار لوحة التحكم المحسنة...")
    
    try:
        # اختبار تحميل البيانات للوحة التحكم
        from database import Database
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # اختبار الإحصائيات
        cursor.execute('SELECT COUNT(*), SUM(total) FROM sales WHERE sale_date >= date("now", "-30 days")')
        sales_count, sales_total = cursor.fetchone()
        print(f"✅ إحصائيات المبيعات: {sales_count} فاتورة بقيمة {sales_total or 0:.2f} ر.س")
        
        cursor.execute('SELECT COUNT(*) FROM products WHERE stock <= min_stock')
        low_stock = cursor.fetchone()[0]
        print(f"✅ تنبيهات المخزون: {low_stock} منتج منخفض المخزون")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ خطأ في لوحة التحكم: {e}")
        return False

def test_enhanced_reports():
    """اختبار نظام التقارير المحسن"""
    print("\n📊 اختبار نظام التقارير المحسن...")
    
    try:
        from database import Database
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # اختبار تقرير المبيعات
        cursor.execute('''
            SELECT s.id, c.name, s.total, s.sale_date
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
            ORDER BY s.sale_date DESC
            LIMIT 5
        ''')
        sales_data = cursor.fetchall()
        print(f"✅ تقرير المبيعات: {len(sales_data)} فاتورة")
        
        # اختبار تقرير المنتجات
        cursor.execute('''
            SELECT p.name, p.stock, p.price
            FROM products p
            ORDER BY p.stock ASC
            LIMIT 5
        ''')
        products_data = cursor.fetchall()
        print(f"✅ تقرير المنتجات: {len(products_data)} منتج")
        
        # اختبار تقرير العملاء
        cursor.execute('''
            SELECT c.name, COUNT(s.id) as orders, SUM(s.total) as total_spent
            FROM customers c
            LEFT JOIN sales s ON c.id = s.customer_id
            GROUP BY c.id, c.name
            ORDER BY total_spent DESC
            LIMIT 5
        ''')
        customers_data = cursor.fetchall()
        print(f"✅ تقرير العملاء: {len(customers_data)} عميل")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ خطأ في نظام التقارير: {e}")
        return False

def test_products_window():
    """اختبار نافذة المنتجات"""
    print("\n🏷️ اختبار نافذة المنتجات...")
    
    try:
        from database import Database
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # اختبار عرض المنتجات
        cursor.execute('SELECT name, price, stock FROM products LIMIT 5')
        products = cursor.fetchall()
        
        print("✅ عينة من المنتجات:")
        for name, price, stock in products:
            print(f"   {name}: {price} ر.س (مخزون: {stock})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ خطأ في نافذة المنتجات: {e}")
        return False

def test_customers_window():
    """اختبار نافذة العملاء"""
    print("\n👥 اختبار نافذة العملاء...")
    
    try:
        from database import Database
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # اختبار عرض العملاء
        cursor.execute('SELECT name, phone, email FROM customers LIMIT 5')
        customers = cursor.fetchall()
        
        print("✅ عينة من العملاء:")
        for name, phone, email in customers:
            print(f"   {name}: {phone} - {email or 'لا يوجد إيميل'}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ خطأ في نافذة العملاء: {e}")
        return False

def test_suppliers_window():
    """اختبار نافذة الموردين"""
    print("\n🏭 اختبار نافذة الموردين...")
    
    try:
        from database import Database
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # اختبار عرض الموردين
        cursor.execute('SELECT name, phone, email FROM suppliers LIMIT 5')
        suppliers = cursor.fetchall()
        
        print("✅ عينة من الموردين:")
        for name, phone, email in suppliers:
            print(f"   {name}: {phone} - {email or 'لا يوجد إيميل'}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ خطأ في نافذة الموردين: {e}")
        return False

def test_permissions_system():
    """اختبار نظام الصلاحيات"""
    print("\n🔒 اختبار نظام الصلاحيات...")
    
    try:
        from permissions_system import PermissionManager
        
        pm = PermissionManager("warehouse_management.db")
        
        # اختبار صلاحيات المستخدم
        user_permissions = pm.get_user_permissions(1)
        print(f"✅ صلاحيات المستخدم: {len(user_permissions)} صلاحية")
        
        # اختبار فحص صلاحية محددة
        has_permission = pm.check_permission(1, "products_view")
        print(f"✅ صلاحية عرض المنتجات: {'موجودة' if has_permission else 'غير موجودة'}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في نظام الصلاحيات: {e}")
        return False

def test_security_features():
    """اختبار ميزات الأمان"""
    print("\n🔐 اختبار ميزات الأمان...")
    
    try:
        from security_utils import BackupManager, DataIntegrityChecker
        
        # اختبار مدير النسخ الاحتياطية
        backup_manager = BackupManager("warehouse_management.db")
        print("✅ مدير النسخ الاحتياطية يعمل")
        
        # اختبار فاحص سلامة البيانات
        integrity_checker = DataIntegrityChecker("warehouse_management.db")
        is_valid = integrity_checker.check_database_integrity()
        print(f"✅ سلامة البيانات: {'سليمة' if is_valid else 'تحتاج مراجعة'}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في ميزات الأمان: {e}")
        return False

def run_visual_test():
    """تشغيل اختبار بصري للنظام"""
    print("\n🖥️ تشغيل اختبار بصري للنظام...")
    
    try:
        # إنشاء نافذة اختبار
        root = tk.Tk()
        root.title("اختبار النظام المرئي")
        root.geometry("800x600")
        root.withdraw()  # إخفاء النافذة الرئيسية
        
        # اختبار نافذة تسجيل الدخول
        from login_window import LoginWindow
        
        print("✅ نافذة تسجيل الدخول جاهزة")
        print("📋 بيانات تسجيل الدخول:")
        print("   اسم المستخدم: admin")
        print("   كلمة المرور: admin123")
        
        # تشغيل النافذة لثواني قليلة للاختبار
        def close_after_delay():
            time.sleep(3)
            try:
                root.quit()
                root.destroy()
            except:
                pass
        
        # تشغيل في خيط منفصل
        threading.Thread(target=close_after_delay, daemon=True).start()
        
        # تشغيل النافذة
        app = LoginWindow()
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في الاختبار البصري: {e}")
        return False

def generate_test_report():
    """إنشاء تقرير شامل للاختبار"""
    print("\n📋 إنشاء تقرير شامل للاختبار...")
    
    tests = [
        ("قاعدة البيانات", test_database_connection),
        ("نظام تسجيل الدخول", test_login_system),
        ("محرك التحليلات الذكي", test_ai_analytics),
        ("نقطة البيع المحسنة", test_enhanced_sales_window),
        ("لوحة التحكم المحسنة", test_enhanced_dashboard),
        ("نظام التقارير المحسن", test_enhanced_reports),
        ("نافذة المنتجات", test_products_window),
        ("نافذة العملاء", test_customers_window),
        ("نافذة الموردين", test_suppliers_window),
        ("نظام الصلاحيات", test_permissions_system),
        ("ميزات الأمان", test_security_features)
    ]
    
    results = []
    
    for test_name, test_function in tests:
        try:
            result = test_function()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ خطأ في اختبار {test_name}: {e}")
            results.append((test_name, False))
    
    # تلخيص النتائج
    print("\n" + "=" * 70)
    print("📊 تقرير شامل لاختبار النظام")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ نجح" if result else "❌ فشل"
        print(f"   {test_name}: {status}")
    
    print(f"\n📈 النتيجة الإجمالية: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 جميع الاختبارات نجحت! النظام جاهز للاستخدام")
        print("\n🚀 لتشغيل النظام:")
        print("   python launch_enhanced_system.py")
    elif passed >= total * 0.8:
        print("✅ معظم الاختبارات نجحت. النظام جاهز مع بعض التحذيرات")
    else:
        print("⚠️ عدة اختبارات فشلت. النظام يحتاج لمراجعة")
    
    return passed, total

def main():
    """الدالة الرئيسية"""
    print("=" * 70)
    print("🧪 اختبار شامل لجميع شاشات النظام")
    print("👨‍💻 تصميم: المهندس هشام المجمر - 773988932")
    print("🤖 نظام إدارة المخازن المتطور v3.0")
    print("=" * 70)
    
    try:
        # تشغيل الاختبارات
        passed, total = generate_test_report()
        
        # عرض معلومات إضافية
        print("\n" + "=" * 70)
        print("📋 معلومات النظام:")
        print("=" * 70)
        
        from database import Database
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # إحصائيات البيانات
        cursor.execute('SELECT COUNT(*) FROM products')
        products_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM customers')
        customers_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sales')
        sales_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM purchases')
        purchases_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(total) FROM sales')
        total_sales = cursor.fetchone()[0] or 0
        
        print(f"📦 المنتجات: {products_count}")
        print(f"👥 العملاء: {customers_count}")
        print(f"💰 المبيعات: {sales_count} فاتورة")
        print(f"📋 المشتريات: {purchases_count} فاتورة")
        print(f"💵 إجمالي المبيعات: {total_sales:.2f} ر.س")
        
        conn.close()
        
        print("\n" + "=" * 70)
        print("🎯 الميزات المتاحة:")
        print("=" * 70)
        print("🤖 الذكاء الاصطناعي والتحليلات المتقدمة")
        print("🛒 نقطة بيع ذكية مع التوصيات")
        print("🎛️ لوحة تحكم تحليلية متقدمة")
        print("📊 تقارير ذكية مع التوقعات")
        print("🔒 نظام أمان وصلاحيات متطور")
        print("👥 إدارة شاملة للعملاء والموردين")
        print("📦 إدارة متقدمة للمخزون والمنتجات")
        
        print("\n📞 للدعم الفني:")
        print("   المهندس هشام المجمر - 773988932")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ خطأ عام في الاختبار: {e}")

if __name__ == "__main__":
    main()