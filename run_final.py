#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف التشغيل النهائي المحسن
تصميم: المهندس هشام المجمر - 773988932
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import sqlite3

# إضافة المجلد الحالي إلى مسار Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_and_fix_database():
    """فحص وإصلاح قاعدة البيانات"""
    print("🔍 فحص قاعدة البيانات...")
    
    try:
        from database import Database
        db = Database()
        
        # فحص الجداول الأساسية
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['users', 'roles', 'permissions', 'products', 'categories']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print(f"⚠️ جداول مفقودة: {missing_tables}")
        else:
            print("✅ جميع الجداول الأساسية موجودة")
        
        # فحص المستخدم الافتراضي
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            print("⚠️ المستخدم الافتراضي غير موجود")
            # إنشاء المستخدم الافتراضي
            db.create_default_admin()
            print("✅ تم إنشاء المستخدم الافتراضي")
        else:
            print("✅ المستخدم الافتراضي موجود")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ خطأ في قاعدة البيانات: {e}")
        return False

def test_login_system():
    """اختبار نظام تسجيل الدخول"""
    print("🔐 اختبار نظام تسجيل الدخول...")
    
    try:
        from database import Database
        db = Database()
        
        # اختبار تسجيل الدخول
        user = db.authenticate_user("admin", "admin123")
        
        if user:
            print("✅ نظام تسجيل الدخول يعمل بشكل صحيح")
            return True
        else:
            print("❌ فشل في تسجيل الدخول")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في نظام تسجيل الدخول: {e}")
        return False

def start_application():
    """بدء التطبيق"""
    print("🚀 بدء التطبيق...")
    
    try:
        from login_window import LoginWindow
        
        # إنشاء وتشغيل نافذة تسجيل الدخول
        app = LoginWindow()
        
        print("✅ تم تحميل نافذة تسجيل الدخول")
        print("\n" + "="*50)
        print("📋 بيانات تسجيل الدخول الافتراضية:")
        print("   اسم المستخدم: admin")
        print("   كلمة المرور: admin123")
        print("="*50)
        print("🎯 النافذة جاهزة للاستخدام!")
        
        app.run()
        
    except Exception as e:
        print(f"❌ خطأ في بدء التطبيق: {e}")
        messagebox.showerror("خطأ", f"فشل في بدء التطبيق:\n{str(e)}")
        return False
    
    return True

def main():
    """الدالة الرئيسية"""
    print("="*60)
    print("🏪 نظام إدارة المخازن المتطور v3.0")
    print("👨‍💻 تصميم وتطوير: المهندس هشام المجمر")
    print("📞 رقم الهاتف: 773988932")
    print("© 2024 جميع الحقوق محفوظة")
    print("="*60)
    
    try:
        # فحص Python
        print(f"🐍 Python {sys.version.split()[0]}")
        
        # فحص المكتبات الأساسية
        print("📚 فحص المكتبات...")
        try:
            import tkinter
            import sqlite3
            import hashlib
            print("✅ جميع المكتبات الأساسية متوفرة")
        except ImportError as e:
            print(f"❌ مكتبة مفقودة: {e}")
            return
        
        # فحص وإصلاح قاعدة البيانات
        if not check_and_fix_database():
            print("❌ فشل في إعداد قاعدة البيانات")
            return
        
        # اختبار نظام تسجيل الدخول
        if not test_login_system():
            print("❌ فشل في نظام تسجيل الدخول")
            return
        
        print("\n✅ جميع الفحوصات نجحت!")
        print("🎉 النظام جاهز للاستخدام!")
        print("-"*60)
        
        # بدء التطبيق
        start_application()
        
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف النظام بواسطة المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        messagebox.showerror("خطأ غير متوقع", 
                           f"حدث خطأ غير متوقع:\n{str(e)}\n\n"
                           "للدعم الفني:\n"
                           "المهندس هشام المجمر - 773988932")
    finally:
        print("\n👋 شكراً لاستخدام نظام إدارة المخازن المتطور!")
        print("="*60)

if __name__ == "__main__":
    main()