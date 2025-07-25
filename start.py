#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف التشغيل المبسط
تصميم: المهندس هشام المجمر - 773988932
"""

import sys
import os

# إضافة المجلد الحالي إلى مسار Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """تشغيل النظام"""
    print("🏪 نظام إدارة المخازن المتطور")
    print("👨‍💻 المهندس هشام المجمر - 773988932")
    print("-" * 40)
    
    try:
        from login_window import LoginWindow
        
        print("📋 بيانات الدخول:")
        print("   المستخدم: admin")
        print("   كلمة المرور: admin123")
        print("-" * 40)
        
        app = LoginWindow()
        app.run()
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        input("اضغط Enter للخروج...")

if __name__ == "__main__":
    main()