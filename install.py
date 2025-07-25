#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إعداد وتثبيت نظام إدارة المخازن
"""

import os
import sys
import subprocess

def install_requirements():
    """تثبيت المتطلبات"""
    try:
        print("تثبيت المتطلبات...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ تم تثبيت المتطلبات بنجاح")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ فشل في تثبيت المتطلبات: {e}")
        return False

def setup_database():
    """إعداد قاعدة البيانات"""
    try:
        print("إعداد قاعدة البيانات...")
        from database import Database
        db = Database()
        print("✓ تم إعداد قاعدة البيانات بنجاح")
        return True
    except Exception as e:
        print(f"✗ فشل في إعداد قاعدة البيانات: {e}")
        return False

def main():
    """الدالة الرئيسية للإعداد"""
    print("=" * 50)
    print("إعداد نظام إدارة المخازن")
    print("=" * 50)
    
    # التحقق من Python
    if sys.version_info < (3, 7):
        print("✗ يتطلب Python 3.7 أو أحدث")
        return False
    
    print(f"✓ إصدار Python: {sys.version}")
    
    # تثبيت المتطلبات
    if not install_requirements():
        return False
    
    # إعداد قاعدة البيانات
    if not setup_database():
        return False
    
    print("\n" + "=" * 50)
    print("🎉 تم إعداد النظام بنجاح!")
    print("=" * 50)
    print("لتشغيل البرنامج:")
    print("  python main.py")
    print("أو:")
    print("  run.bat")
    print("\nمعلومات تسجيل الدخول:")
    print("  اسم المستخدم: admin")
    print("  كلمة المرور: admin123")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n✗ فشل في الإعداد")
        sys.exit(1)
    
    input("\nاضغط Enter للخروج...")