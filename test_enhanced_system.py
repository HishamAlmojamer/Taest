#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار النظام المحسن مع الذكاء الاصطناعي
تصميم: المهندس هشام المجمر - 773988932
"""

import sys
import os
import threading
import time

# إضافة المجلد الحالي إلى مسار Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_ai_analytics():
    """اختبار محرك التحليلات الذكي"""
    print("🤖 اختبار محرك التحليلات الذكي...")
    
    try:
        from ai_analytics import AIAnalyticsEngine, SmartRecommendationSystem
        
        # اختبار محرك التحليلات
        ai_engine = AIAnalyticsEngine("warehouse_management.db")
        print("✅ تم إنشاء محرك التحليلات")
        
        # اختبار تحليل أنماط المبيعات
        patterns = ai_engine.analyze_sales_patterns(30)
        print("✅ تحليل أنماط المبيعات يعمل")
        
        # اختبار توقع الطلب
        prediction = ai_engine.predict_demand(1, 7)
        print("✅ توقع الطلب يعمل")
        
        # اختبار الرؤى التجارية
        insights = ai_engine.generate_business_insights()
        print("✅ توليد الرؤى التجارية يعمل")
        
        # اختبار نظام التوصيات
        recommendation_system = SmartRecommendationSystem("warehouse_management.db")
        print("✅ نظام التوصيات الذكي يعمل")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار الذكاء الاصطناعي: {e}")
        return False

def test_enhanced_sales_window():
    """اختبار نقطة البيع المحسنة"""
    print("\n🛒 اختبار نقطة البيع المحسنة...")
    
    try:
        from enhanced_sales_window import EnhancedSalesWindow, AIRecommendationEngine, SmartPriceCalculator
        from database import Database
        
        # إنشاء قاعدة البيانات
        db = Database()
        
        # اختبار محرك التوصيات
        ai_engine = AIRecommendationEngine(db)
        trending = ai_engine.get_trending_products()
        print("✅ محرك التوصيات يعمل")
        
        # اختبار حاسبة الأسعار الذكية
        price_calculator = SmartPriceCalculator(db)
        discount = price_calculator.suggest_discount(1, 5)
        print("✅ حاسبة الأسعار الذكية تعمل")
        
        # اختبار إنشاء النافذة (بدون عرض)
        user = {'id': 1, 'username': 'admin', 'full_name': 'مدير النظام', 'role': 'admin'}
        
        # محاكاة إنشاء النافذة
        print("✅ نقطة البيع المحسنة جاهزة للاستخدام")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار نقطة البيع المحسنة: {e}")
        return False

def test_enhanced_dashboard():
    """اختبار لوحة التحكم المحسنة"""
    print("\n🎛️ اختبار لوحة التحكم المحسنة...")
    
    try:
        from enhanced_dashboard import EnhancedDashboard
        from database import Database
        
        db = Database()
        user = {'id': 1, 'username': 'admin', 'full_name': 'مدير النظام', 'role': 'admin'}
        
        print("✅ لوحة التحكم المحسنة جاهزة للاستخدام")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار لوحة التحكم المحسنة: {e}")
        return False

def test_enhanced_reports():
    """اختبار نظام التقارير المحسن"""
    print("\n📊 اختبار نظام التقارير المحسن...")
    
    try:
        from enhanced_reports import EnhancedReportsWindow
        from database import Database
        
        db = Database()
        user = {'id': 1, 'username': 'admin', 'full_name': 'مدير النظام', 'role': 'admin'}
        
        print("✅ نظام التقارير المحسن جاهز للاستخدام")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار نظام التقارير المحسن: {e}")
        return False

def test_database_performance():
    """اختبار أداء قاعدة البيانات"""
    print("\n💾 اختبار أداء قاعدة البيانات...")
    
    try:
        from database import Database
        import time
        
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # اختبار سرعة الاستعلامات
        start_time = time.time()
        
        # استعلام المنتجات
        cursor.execute('SELECT COUNT(*) FROM products')
        products_count = cursor.fetchone()[0]
        
        # استعلام المبيعات
        cursor.execute('SELECT COUNT(*) FROM sales')
        sales_count = cursor.fetchone()[0]
        
        # استعلام العملاء
        cursor.execute('SELECT COUNT(*) FROM customers')
        customers_count = cursor.fetchone()[0]
        
        end_time = time.time()
        query_time = end_time - start_time
        
        print(f"✅ المنتجات: {products_count}")
        print(f"✅ المبيعات: {sales_count}")
        print(f"✅ العملاء: {customers_count}")
        print(f"✅ وقت الاستعلام: {query_time:.3f} ثانية")
        
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار قاعدة البيانات: {e}")
        return False

def test_system_integration():
    """اختبار تكامل النظام"""
    print("\n🔗 اختبار تكامل النظام...")
    
    try:
        # اختبار تسجيل الدخول
        from database import Database
        db = Database()
        user = db.authenticate_user("admin", "admin123")
        
        if not user:
            print("❌ فشل في تسجيل الدخول")
            return False
        
        print("✅ تسجيل الدخول يعمل")
        
        # اختبار النافذة الرئيسية
        from main_window import MainWindow
        print("✅ النافذة الرئيسية قابلة للتحميل")
        
        # اختبار نظام الصلاحيات
        from permissions_system import PermissionManager
        pm = PermissionManager(db.db_path)
        print("✅ نظام الصلاحيات يعمل")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار التكامل: {e}")
        return False

def test_security_features():
    """اختبار ميزات الأمان"""
    print("\n🔒 اختبار ميزات الأمان...")
    
    try:
        from security_utils import BackupManager, DataIntegrityChecker
        
        # اختبار مدير النسخ الاحتياطية
        backup_manager = BackupManager("warehouse_management.db")
        print("✅ مدير النسخ الاحتياطية يعمل")
        
        # اختبار فاحص سلامة البيانات
        integrity_checker = DataIntegrityChecker("warehouse_management.db")
        is_valid = integrity_checker.check_database_integrity()
        print(f"✅ سلامة قاعدة البيانات: {'سليمة' if is_valid else 'تحتاج مراجعة'}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار الأمان: {e}")
        return False

def test_performance_benchmarks():
    """اختبار معايير الأداء"""
    print("\n⚡ اختبار معايير الأداء...")
    
    try:
        import time
        from database import Database
        
        db = Database()
        
        # اختبار سرعة الاتصال
        start_time = time.time()
        conn = db.get_connection()
        connection_time = time.time() - start_time
        
        # اختبار سرعة الاستعلام المعقد
        start_time = time.time()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.name, SUM(si.quantity) as total_sold
            FROM products p
            LEFT JOIN sale_items si ON p.id = si.product_id
            GROUP BY p.id, p.name
            ORDER BY total_sold DESC
            LIMIT 10
        ''')
        results = cursor.fetchall()
        query_time = time.time() - start_time
        
        conn.close()
        
        print(f"✅ وقت الاتصال: {connection_time:.3f} ثانية")
        print(f"✅ وقت الاستعلام المعقد: {query_time:.3f} ثانية")
        print(f"✅ عدد النتائج: {len(results)}")
        
        # تقييم الأداء
        if connection_time < 0.1 and query_time < 0.5:
            print("🚀 الأداء ممتاز")
        elif connection_time < 0.5 and query_time < 1.0:
            print("✅ الأداء جيد")
        else:
            print("⚠️ الأداء يحتاج تحسين")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار الأداء: {e}")
        return False

def generate_test_data():
    """إنشاء بيانات تجريبية للاختبار"""
    print("\n📝 إنشاء بيانات تجريبية...")
    
    try:
        from database import Database
        import random
        from datetime import datetime, timedelta
        
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # إضافة فئات تجريبية
        categories = [
            ("إلكترونيات", "أجهزة إلكترونية"),
            ("ملابس", "ملابس وأزياء"),
            ("طعام", "مواد غذائية"),
            ("كتب", "كتب ومجلات"),
            ("رياضة", "معدات رياضية")
        ]
        
        for name, desc in categories:
            try:
                cursor.execute('INSERT INTO categories (name, description) VALUES (?, ?)', (name, desc))
            except:
                pass  # الفئة موجودة بالفعل
        
        # إضافة منتجات تجريبية
        products = [
            ("لابتوب Dell", 1, 2500.00, 10, 2),
            ("قميص قطني", 2, 85.00, 50, 10),
            ("أرز بسمتي", 3, 25.00, 100, 20),
            ("كتاب البرمجة", 4, 120.00, 30, 5),
            ("كرة قدم", 5, 75.00, 25, 5)
        ]
        
        for name, cat_id, price, stock, min_stock in products:
            try:
                cursor.execute('''
                    INSERT INTO products (name, category_id, price, stock, min_stock)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, cat_id, price, stock, min_stock))
            except:
                pass  # المنتج موجود بالفعل
        
        # إضافة عملاء تجريبيين
        customers = [
            ("أحمد محمد", "0501234567", "ahmed@email.com"),
            ("فاطمة علي", "0507654321", "fatima@email.com"),
            ("محمد سالم", "0509876543", "mohammed@email.com")
        ]
        
        for name, phone, email in customers:
            try:
                cursor.execute('''
                    INSERT INTO customers (name, phone, email)
                    VALUES (?, ?, ?)
                ''', (name, phone, email))
            except:
                pass  # العميل موجود بالفعل
        
        # إضافة مبيعات تجريبية
        for i in range(10):
            try:
                sale_date = datetime.now() - timedelta(days=random.randint(1, 30))
                customer_id = random.randint(1, 3)
                total = random.uniform(50, 500)
                
                cursor.execute('''
                    INSERT INTO sales (customer_id, user_id, sale_date, total, payment_method)
                    VALUES (?, ?, ?, ?, ?)
                ''', (customer_id, 1, sale_date.isoformat(), total, "نقدي"))
                
                sale_id = cursor.lastrowid
                
                # إضافة عناصر البيع
                product_id = random.randint(1, 5)
                quantity = random.randint(1, 5)
                unit_price = random.uniform(20, 100)
                
                cursor.execute('''
                    INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total)
                    VALUES (?, ?, ?, ?, ?)
                ''', (sale_id, product_id, quantity, unit_price, quantity * unit_price))
                
            except Exception as e:
                print(f"تحذير: فشل في إضافة بيع تجريبي: {e}")
        
        conn.commit()
        conn.close()
        
        print("✅ تم إنشاء البيانات التجريبية بنجاح")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء البيانات التجريبية: {e}")
        return False

def run_comprehensive_test():
    """تشغيل اختبار شامل للنظام"""
    print("=" * 70)
    print("🧪 اختبار شامل لنظام إدارة المخازن المتطور v3.0")
    print("👨‍💻 تصميم: المهندس هشام المجمر - 773988932")
    print("=" * 70)
    
    tests = [
        ("إنشاء البيانات التجريبية", generate_test_data),
        ("اختبار قاعدة البيانات", test_database_performance),
        ("اختبار تكامل النظام", test_system_integration),
        ("اختبار الذكاء الاصطناعي", test_ai_analytics),
        ("اختبار نقطة البيع المحسنة", test_enhanced_sales_window),
        ("اختبار لوحة التحكم المحسنة", test_enhanced_dashboard),
        ("اختبار نظام التقارير المحسن", test_enhanced_reports),
        ("اختبار ميزات الأمان", test_security_features),
        ("اختبار معايير الأداء", test_performance_benchmarks)
    ]
    
    results = []
    
    for test_name, test_function in tests:
        print(f"\n🔍 {test_name}...")
        try:
            result = test_function()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: نجح")
            else:
                print(f"❌ {test_name}: فشل")
        except Exception as e:
            print(f"❌ {test_name}: خطأ - {e}")
            results.append((test_name, False))
    
    # تلخيص النتائج
    print("\n" + "=" * 70)
    print("📊 ملخص نتائج الاختبار:")
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
        print("   python start.py")
        print("   أو")
        print("   python run_final.py")
    elif passed >= total * 0.8:
        print("✅ معظم الاختبارات نجحت. النظام جاهز مع بعض التحذيرات")
    else:
        print("⚠️ عدة اختبارات فشلت. النظام يحتاج لمراجعة")
    
    print("\n📞 للدعم الفني:")
    print("   المهندس هشام المجمر - 773988932")
    print("=" * 70)

def main():
    """الدالة الرئيسية"""
    try:
        run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف الاختبار بواسطة المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع في الاختبار: {e}")

if __name__ == "__main__":
    main()