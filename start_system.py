#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف التشغيل الرئيسي للنظام المحسن
تصميم: المهندس هشام المجمر - 773988932
"""

import sys
import os
import subprocess
import tkinter as tk
from tkinter import messagebox

# إضافة المجلد الحالي إلى مسار Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_system_check():
    """تشغيل فحص النظام قبل البدء"""
    print("🔍 فحص النظام...")
    try:
        # تشغيل الفحص الشامل
        result = subprocess.run([sys.executable, "complete_system_fixer.py"], 
                              capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            print("✅ تم فحص وإصلاح النظام بنجاح")
            return True
        else:
            print(f"⚠️ تحذير في فحص النظام: {result.stderr}")
            return True  # لا نوقف النظام
    except Exception as e:
        print(f"⚠️ تحذير في فحص النظام: {e}")
        return True  # لا نوقف النظام

def show_startup_info():
    """عرض معلومات بدء التشغيل"""
    print("\n" + "=" * 70)
    print("🤖🏪 نظام إدارة المخازن المتطور v3.0 - Enhanced Edition")
    print("👨‍💻 تصميم وتطوير: المهندس هشام المجمر - 773988932")
    print("🚀 مع الذكاء الاصطناعي والتحليلات المتقدمة")
    print("© 2024 جميع الحقوق محفوظة")
    print("=" * 70)
    
    print("\n🎯 الميزات الرئيسية:")
    print("🤖 الذكاء الاصطناعي والتحليلات المتقدمة")
    print("🛒 نقطة بيع ذكية مع التوصيات")
    print("🎛️ لوحة تحكم تفاعلية")
    print("📊 تقارير ذكية مع التوقعات")
    print("🔒 نظام أمان متطور")
    
    print("\n📋 بيانات تسجيل الدخول:")
    print("   👤 اسم المستخدم: admin")
    print("   🔑 كلمة المرور: admin123")
    
    print("\n📞 الدعم الفني:")
    print("   المهندس هشام المجمر - 773988932")
    print("=" * 70)

def start_system():
    """تشغيل النظام الرئيسي"""
    print("\n🚀 بدء تشغيل النظام...")
    
    try:
        # محاولة تشغيل النظام المحسن أولاً
        if os.path.exists("RUN_SYSTEM.py"):
            print("🎯 تشغيل النظام المحسن...")
            from RUN_SYSTEM import main as run_main
            run_main()
        elif os.path.exists("launch_enhanced_system.py"):
            print("🎯 تشغيل النظام المتقدم...")
            from launch_enhanced_system import main as enhanced_main
            enhanced_main()
        elif os.path.exists("start_system.py"):
            print("🔄 تشغيل النظام العادي...")
            import start_system
            start_system.main()
        else:
            print("🔄 تشغيل النظام الأساسي...")
            from login_window import LoginWindow
            app = LoginWindow()
            app.run()
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في تشغيل النظام: {e}")
        messagebox.showerror("خطأ في النظام", 
                           f"فشل في تشغيل النظام:\n{str(e)}\n\n"
                           "للدعم الفني:\n"
                           "المهندس هشام المجمر - 773988932")
        return False

def main():
    """الدالة الرئيسية"""
    try:
        # عرض معلومات بدء التشغيل
        show_startup_info()
        
        # فحص النظام
        run_system_check()
        
        # تشغيل النظام
        if start_system():
            print("\n✅ تم تشغيل النظام بنجاح!")
        else:
            print("\n❌ فشل في تشغيل النظام")
        
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف النظام بواسطة المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        messagebox.showerror("خطأ غير متوقع", 
                           f"حدث خطأ غير متوقع:\n{str(e)}\n\n"
                           "يرجى التواصل مع المطور:\n"
                           "المهندس هشام المجمر - 773988932")
    finally:
        print("\n" + "=" * 70)
        print("👋 شكراً لاستخدام نظام إدارة المخازن المتطور!")
        print("📞 للدعم الفني: المهندس هشام المجمر - 773988932")
        print("🌟 نتمنى لك تجربة ممتازة مع النظام!")
        print("=" * 70)

if __name__ == "__main__":
    main()