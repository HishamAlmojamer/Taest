#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار النافذة الرئيسية
"""

import sys
import os

# إضافة المجلد الحالي إلى مسار Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_main_window():
    """اختبار النافذة الرئيسية"""
    try:
        print("🧪 اختبار النافذة الرئيسية...")
        
        # إنشاء مستخدم تجريبي
        user = {
            'id': 1,
            'username': 'admin',
            'full_name': 'مدير النظام',
            'role': 'admin',
            'role_id': 1
        }
        
        print("✅ بيانات المستخدم التجريبي جاهزة")
        
        # استيراد النافذة الرئيسية
        from main_window import MainWindow
        print("✅ تم استيراد النافذة الرئيسية")
        
        # إنشاء النافذة
        print("🚀 إنشاء النافذة الرئيسية...")
        main_app = MainWindow(user)
        print("✅ تم إنشاء النافذة الرئيسية بنجاح")
        
        # تشغيل النافذة
        print("🎯 تشغيل النافذة الرئيسية...")
        print("📋 بيانات المستخدم:")
        print(f"   الاسم: {user['full_name']}")
        print(f"   اسم المستخدم: {user['username']}")
        print(f"   الدور: {user['role']}")
        print("=" * 50)
        print("🎉 النافذة الرئيسية جاهزة للاستخدام!")
        
        main_app.run()
        
    except Exception as e:
        print(f"❌ خطأ في النافذة الرئيسية: {e}")
        import traceback
        traceback.print_exc()
        input("اضغط Enter للخروج...")

if __name__ == "__main__":
    test_main_window()