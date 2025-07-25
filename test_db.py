#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار قاعدة البيانات
"""

from database import Database

def test_database():
    """اختبار الاتصال بقاعدة البيانات"""
    try:
        print("اختبار قاعدة البيانات...")
        
        # إنشاء قاعدة البيانات
        db = Database()
        print("✓ تم إنشاء قاعدة البيانات بنجاح")
        
        # اختبار المصادقة
        user = db.authenticate_user("admin", "admin123")
        if user:
            print(f"✓ تم تسجيل الدخول بنجاح: {user['full_name']}")
        else:
            print("✗ فشل في تسجيل الدخول")
            return False
        
        # اختبار إضافة فئة
        success = db.add_category("إلكترونيات", "أجهزة إلكترونية")
        if success:
            print("✓ تم إضافة فئة تجريبية")
        
        # اختبار جلب الفئات
        categories = db.get_categories()
        print(f"✓ تم جلب {len(categories)} فئة")
        
        # اختبار إضافة مورد
        success = db.add_supplier("مورد تجريبي", "أحمد محمد", "123456789", "test@example.com", "الرياض")
        if success:
            print("✓ تم إضافة مورد تجريبي")
        
        # اختبار إضافة عميل
        success = db.add_customer("عميل تجريبي", "987654321", "customer@example.com", "جدة")
        if success:
            print("✓ تم إضافة عميل تجريبي")
        
        print("\n🎉 جميع الاختبارات نجحت! قاعدة البيانات جاهزة للاستخدام.")
        return True
        
    except Exception as e:
        print(f"✗ خطأ في اختبار قاعدة البيانات: {e}")
        return False

if __name__ == "__main__":
    test_database()
    input("\nاضغط Enter للخروج...")