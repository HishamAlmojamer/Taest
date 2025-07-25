#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تشغيل مبسط للنظام
"""

import sys
import os

# إضافة المجلد الحالي إلى مسار Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """تشغيل النظام"""
    try:
        print("🚀 بدء تشغيل نظام إدارة المخازن المتطور...")
        print("👨‍💻 تصميم: المهندس هشام المجمر - 773988932")
        print("=" * 50)
        
        # استيراد وتشغيل نافذة تسجيل الدخول
        from login_window import LoginWindow
        
        print("✅ تم تحميل نافذة تسجيل الدخول")
        print("📋 بيانات تسجيل الدخول:")
        print("   اسم المستخدم: admin")
        print("   كلمة المرور: admin123")
        print("=" * 50)
        
        # إنشاء وتشغيل التطبيق
        app = LoginWindow()
        app.run()
        
    except Exception as e:
        print(f"❌ خطأ في تشغيل النظام: {e}")
        import traceback
        traceback.print_exc()
        input("اضغط Enter للخروج...")

if __name__ == "__main__":
    main()