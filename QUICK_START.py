#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تشغيل سريع للنظام بدون فحص
تصميم: المهندس هشام المجمر - 773988932
"""

import sys
import os

# إضافة المجلد الحالي إلى مسار Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """تشغيل سريع للنظام"""
    print("⚡ تشغيل سريع لنظام إدارة المخازن المتطور")
    print("👨‍💻 المهندس هشام المجمر - 773988932")
    print("=" * 50)
    
    try:
        # تشغيل النظام مباشرة
        if os.path.exists("launch_enhanced_system.py"):
            print("🎯 تشغيل النظام المحسن...")
            from launch_enhanced_system import main as enhanced_main
            enhanced_main()
        else:
            print("🔄 تشغيل النظام الأساسي...")
            from login_window import LoginWindow
            app = LoginWindow()
            app.run()
            
    except Exception as e:
        print(f"❌ خطأ: {e}")
        print("📞 للدعم: المهندس هشام المجمر - 773988932")
        input("اضغط Enter للخروج...")

if __name__ == "__main__":
    main()