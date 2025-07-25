#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أداة تشخيص مشاكل النظام
تصميم: المهندس هشام المجمر - 773988932
"""

import sys
import os
import sqlite3
import tkinter as tk
from tkinter import messagebox

# إضافة المجلد الحالي إلى مسار Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_python_version():
    """فحص إصدار Python"""
    print("🐍 فحص Python...")
    version = sys.version_info
    print(f"   الإصدار: {version.major}.{version.minor}.{version.micro}")
    
    if version >= (3, 7):
        print("   ✅ الإصدار مناسب")
        return True
    else:
        print("   ❌ الإصدار قديم (يتطلب 3.7 أو أحدث)")
        return False

def check_required_modules():
    """فحص المكتبات المطلوبة"""
    print("\n📚 فحص المكتبات...")
    
    required_modules = [
        'tkinter', 'sqlite3', 'hashlib', 'datetime', 
        'threading', 'json', 'csv', 'os', 'sys'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module} مفقود")
            missing_modules.append(module)
    
    return len(missing_modules) == 0

def check_database():
    """فحص قاعدة البيانات"""
    print("\n💾 فحص قاعدة البيانات...")
    
    db_path = "warehouse_management.db"
    
    if not os.path.exists(db_path):
        print("   ⚠️ قاعدة البيانات غير موجودة - سيتم إنشاؤها")
        try:
            from database import Database
            db = Database()
            print("   ✅ تم إنشاء قاعدة البيانات")
        except Exception as e:
            print(f"   ❌ فشل في إنشاء قاعدة البيانات: {e}")
            return False
    else:
        print("   ✅ قاعدة البيانات موجودة")
    
    # فحص الجداول
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['users', 'roles', 'permissions', 'products', 'categories']
        
        print("   الجداول الموجودة:")
        for table in tables:
            print(f"     ✅ {table}")
        
        missing_tables = [t for t in required_tables if t not in tables]
        if missing_tables:
            print("   الجداول المفقودة:")
            for table in missing_tables:
                print(f"     ❌ {table}")
        
        conn.close()
        return len(missing_tables) == 0
        
    except Exception as e:
        print(f"   ❌ خطأ في فحص قاعدة البيانات: {e}")
        return False

def check_admin_user():
    """فحص المستخدم الافتراضي"""
    print("\n👤 فحص المستخدم الافتراضي...")
    
    try:
        from database import Database
        db = Database()
        
        user = db.authenticate_user("admin", "admin123")
        
        if user:
            print("   ✅ المستخدم الافتراضي يعمل")
            print(f"     الاسم: {user['full_name']}")
            print(f"     الدور: {user['role']}")
            return True
        else:
            print("   ❌ فشل في تسجيل الدخول")
            return False
            
    except Exception as e:
        print(f"   ❌ خطأ في فحص المستخدم: {e}")
        return False

def check_gui():
    """فحص الواجهة الرسومية"""
    print("\n🖥️ فحص الواجهة الرسومية...")
    
    try:
        # اختبار إنشاء نافذة بسيطة
        root = tk.Tk()
        root.withdraw()  # إخفاء النافذة
        
        # اختبار المكونات الأساسية
        frame = tk.Frame(root)
        label = tk.Label(frame, text="اختبار")
        button = tk.Button(frame, text="اختبار")
        entry = tk.Entry(frame)
        
        print("   ✅ المكونات الأساسية تعمل")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"   ❌ خطأ في الواجهة الرسومية: {e}")
        return False

def check_system_files():
    """فحص ملفات النظام"""
    print("\n📁 فحص ملفات النظام...")
    
    required_files = [
        'database.py', 'login_window.py', 'main_window.py',
        'config.py', 'permissions_system.py', 'start.py'
    ]
    
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} مفقود")
            missing_files.append(file)
    
    return len(missing_files) == 0

def run_quick_test():
    """تشغيل اختبار سريع"""
    print("\n🧪 اختبار سريع...")
    
    try:
        # اختبار استيراد الملفات الأساسية
        from database import Database
        from login_window import LoginWindow
        from main_window import MainWindow
        
        print("   ✅ جميع الملفات قابلة للاستيراد")
        
        # اختبار إنشاء قاعدة البيانات
        db = Database()
        print("   ✅ قاعدة البيانات تعمل")
        
        # اختبار تسجيل الدخول
        user = db.authenticate_user("admin", "admin123")
        if user:
            print("   ✅ تسجيل الدخول يعمل")
        else:
            print("   ❌ تسجيل الدخول لا يعمل")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ خطأ في الاختبار السريع: {e}")
        return False

def show_solution(problem):
    """عرض الحلول للمشاكل الشائعة"""
    solutions = {
        'python_old': """
🔧 حل مشكلة إصدار Python القديم:
1. قم بتحميل Python 3.7 أو أحدث من: https://python.org
2. تأكد من إضافة Python إلى PATH أثناء التثبيت
3. أعد تشغيل الكمبيوتر بعد التثبيت
        """,
        
        'missing_modules': """
🔧 حل مشكلة المكتبات المفقودة:
1. افتح Command Prompt كمدير
2. شغل الأمر: pip install --upgrade pip
3. إذا كانت tkinter مفقودة، أعد تثبيت Python مع "tcl/tk and IDLE"
        """,
        
        'database_error': """
🔧 حل مشكلة قاعدة البيانات:
1. احذف ملف warehouse_management.db إذا كان موجود
2. شغل الأمر: python database.py
3. أو شغل: python fix_database.py
        """,
        
        'login_error': """
🔧 حل مشكلة تسجيل الدخول:
1. تأكد من البيانات: admin / admin123
2. شغل: python fix_admin_password.py
3. أعد تشغيل البرنامج
        """,
        
        'gui_error': """
🔧 حل مشكلة الواجهة الرسومية:
1. تأكد من أن Windows ليس في وضع Server Core
2. أعد تثبيت Python مع دعم tkinter
3. جرب تشغيل: python -m tkinter
        """,
        
        'missing_files': """
🔧 حل مشكلة الملفات المفقودة:
1. تأكد من وجود جميع ملفات النظام في نفس المجلد
2. لا تحرك أو تحذف أي ملفات
3. أعد تحميل النظام إذا لزم الأمر
        """
    }
    
    if problem in solutions:
        print(solutions[problem])

def main():
    """الدالة الرئيسية للتشخيص"""
    print("="*60)
    print("🔍 أداة تشخيص نظام إدارة المخازن المتطور")
    print("👨‍💻 المهندس هشام المجمر - 773988932")
    print("="*60)
    
    problems = []
    
    # فحص Python
    if not check_python_version():
        problems.append('python_old')
    
    # فحص المكتبات
    if not check_required_modules():
        problems.append('missing_modules')
    
    # فحص قاعدة البيانات
    if not check_database():
        problems.append('database_error')
    
    # فحص المستخدم الافتراضي
    if not check_admin_user():
        problems.append('login_error')
    
    # فحص الواجهة الرسومية
    if not check_gui():
        problems.append('gui_error')
    
    # فحص ملفات النظام
    if not check_system_files():
        problems.append('missing_files')
    
    # اختبار سريع
    if not run_quick_test():
        problems.append('general_error')
    
    print("\n" + "="*60)
    print("📊 نتائج التشخيص:")
    
    if not problems:
        print("🎉 جميع الفحوصات نجحت!")
        print("✅ النظام جاهز للاستخدام")
        print("\n🚀 لتشغيل النظام:")
        print("   python start.py")
        print("   أو")
        print("   start.bat")
    else:
        print(f"⚠️ تم العثور على {len(problems)} مشكلة:")
        for i, problem in enumerate(problems, 1):
            print(f"   {i}. {problem}")
        
        print("\n🔧 الحلول المقترحة:")
        for problem in problems:
            show_solution(problem)
    
    print("\n📞 للدعم الفني:")
    print("   المهندس هشام المجمر")
    print("   رقم الهاتف: 773988932")
    print("="*60)

if __name__ == "__main__":
    main()