#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف التشغيل النهائي للنظام المحسن مع الذكاء الاصطناعي
تصميم: المهندس هشام المجمر - 773988932
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import threading
import time

# إضافة المجلد الحالي إلى مسار Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def show_enhanced_splash():
    """عرض شاشة البدء المحسنة"""
    splash = tk.Tk()
    splash.title("نظام إدارة المخازن المتطور مع الذكاء الاصطناعي")
    splash.geometry("700x500")
    splash.resizable(False, False)
    splash.overrideredirect(True)
    
    # توسيط النافذة
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - 700) // 2
    y = (screen_height - 500) // 2
    splash.geometry(f"700x500+{x}+{y}")
    
    # الخلفية المتدرجة
    main_frame = tk.Frame(splash, bg="#0f3460", relief=tk.RAISED, bd=5)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # العنوان الرئيسي
    title_frame = tk.Frame(main_frame, bg="#0f3460")
    title_frame.pack(expand=True, pady=40)
    
    # أيقونة النظام
    tk.Label(title_frame, text="🤖🏪", font=("Arial", 64), 
             bg="#0f3460", fg="white").pack(pady=10)
    
    # اسم النظام
    tk.Label(title_frame, text="نظام إدارة المخازن المتطور", 
             font=("Arial", 28, "bold"), bg="#0f3460", fg="white").pack(pady=5)
    
    # مع الذكاء الاصطناعي
    tk.Label(title_frame, text="مع الذكاء الاصطناعي والتحليلات المتقدمة", 
             font=("Arial", 16), bg="#0f3460", fg="#00d4ff").pack(pady=2)
    
    # الإصدار
    tk.Label(title_frame, text="الإصدار 3.0 - Enhanced Edition", 
             font=("Arial", 14), bg="#0f3460", fg="#a8d8ff").pack(pady=2)
    
    # الميزات الجديدة
    features_frame = tk.Frame(main_frame, bg="#0f3460")
    features_frame.pack(pady=20)
    
    features = [
        "🤖 محرك ذكاء اصطناعي متقدم",
        "📊 تحليلات وتوقعات ذكية", 
        "🎯 نظام توصيات شخصي",
        "⚡ واجهة محسنة وسريعة",
        "🔒 أمان عالي المستوى"
    ]
    
    for feature in features:
        tk.Label(features_frame, text=feature, 
                font=("Arial", 12), bg="#0f3460", fg="#d0e8ff").pack(pady=2)
    
    # معلومات المطور
    developer_frame = tk.Frame(main_frame, bg="#0f3460")
    developer_frame.pack(side=tk.BOTTOM, pady=30)
    
    tk.Label(developer_frame, text="تصميم وتطوير: المهندس هشام المجمر", 
             font=("Arial", 14, "bold"), bg="#0f3460", fg="#ffd700").pack()
    
    tk.Label(developer_frame, text="رقم الهاتف: 773988932", 
             font=("Arial", 12), bg="#0f3460", fg="#ffd700").pack(pady=2)
    
    tk.Label(developer_frame, text="© 2024 جميع الحقوق محفوظة", 
             font=("Arial", 11), bg="#0f3460", fg="#a8d8ff").pack(pady=5)
    
    # شريط التقدم المحسن
    progress_frame = tk.Frame(main_frame, bg="#0f3460")
    progress_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=60, pady=30)
    
    # خلفية شريط التقدم
    progress_bg = tk.Frame(progress_frame, bg="white", height=10, relief=tk.SUNKEN, bd=2)
    progress_bg.pack(fill=tk.X)
    
    # شريط التقدم الفعلي
    progress_bar = tk.Frame(progress_bg, bg="#00ff88", height=6)
    progress_bar.pack(side=tk.LEFT, fill=tk.Y)
    
    # نص الحالة
    status_label = tk.Label(progress_frame, text="جاري التحميل...", 
                           font=("Arial", 12, "bold"), bg="#0f3460", fg="white")
    status_label.pack(pady=(15, 0))
    
    splash.update()
    
    # خطوات التحميل المحسنة
    loading_steps = [
        ("🔍 فحص متطلبات النظام...", 0.1),
        ("🤖 تهيئة محرك الذكاء الاصطناعي...", 0.2),
        ("💾 تحميل قاعدة البيانات...", 0.3),
        ("🔐 إعداد نظام الصلاحيات...", 0.4),
        ("📊 تحميل محرك التحليلات...", 0.5),
        ("🎯 إعداد نظام التوصيات...", 0.6),
        ("🖥️ تحميل الواجهات المحسنة...", 0.7),
        ("⚡ تحسين الأداء...", 0.8),
        ("🔒 فحص الأمان...", 0.9),
        ("🚀 إنهاء التحضيرات...", 1.0)
    ]
    
    for step_text, progress in loading_steps:
        status_label.config(text=step_text)
        progress_width = int(progress * 580)  # 580 هو العرض الأقصى
        progress_bar.config(width=progress_width)
        splash.update()
        time.sleep(0.6)
    
    # رسالة الترحيب النهائية
    status_label.config(text="🎉 مرحباً بك في النظام المتطور!", fg="#00ff88")
    splash.update()
    time.sleep(1)
    
    splash.destroy()

def check_enhanced_requirements():
    """فحص متطلبات النظام المحسن"""
    print("🔍 فحص متطلبات النظام المحسن...")
    
    try:
        # فحص Python
        if sys.version_info < (3, 7):
            messagebox.showerror("خطأ في النظام", 
                               "يتطلب النظام Python 3.7 أو أحدث")
            return False
        
        # فحص المكتبات الأساسية
        required_modules = [
            'tkinter', 'sqlite3', 'datetime', 'hashlib', 
            'threading', 'json', 'csv', 'statistics'
        ]
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                messagebox.showerror("مكتبة مفقودة", f"المكتبة {module} مطلوبة")
                return False
        
        # فحص الملفات الأساسية
        required_files = [
            'database.py', 'login_window.py', 'main_window.py',
            'config.py', 'permissions_system.py', 'ai_analytics.py',
            'enhanced_sales_window.py', 'enhanced_dashboard.py',
            'enhanced_reports.py'
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            messagebox.showerror("ملفات مفقودة", 
                               f"الملفات التالية مطلوبة:\n" + "\n".join(missing_files))
            return False
        
        print("✅ جميع المتطلبات متوفرة")
        return True
        
    except Exception as e:
        messagebox.showerror("خطأ في الفحص", f"فشل في فحص المتطلبات: {e}")
        return False

def initialize_enhanced_system():
    """تهيئة النظام المحسن"""
    print("🚀 تهيئة النظام المحسن...")
    
    try:
        # تهيئة قاعدة البيانات
        from database import Database
        db = Database()
        print("✅ قاعدة البيانات جاهزة")
        
        # تهيئة نظام الصلاحيات
        from permissions_system import PermissionManager
        pm = PermissionManager(db.db_path)
        print("✅ نظام الصلاحيات جاهز")
        
        # تهيئة محرك الذكاء الاصطناعي
        from ai_analytics import AIAnalyticsEngine
        ai_engine = AIAnalyticsEngine(db.db_path)
        print("✅ محرك الذكاء الاصطناعي جاهز")
        
        # إصلاح قاعدة البيانات إذا لزم الأمر
        try:
            from fix_database_schema import fix_sales_table, fix_purchases_table
            fix_sales_table()
            fix_purchases_table()
            print("✅ تم إصلاح قاعدة البيانات")
        except:
            print("⚠️ تحذير: فشل في إصلاح قاعدة البيانات")
        
        return True
        
    except Exception as e:
        messagebox.showerror("خطأ في التهيئة", f"فشل في تهيئة النظام: {e}")
        return False

def start_enhanced_application():
    """بدء التطبيق المحسن"""
    print("🎯 بدء التطبيق المحسن...")
    
    try:
        from login_window import LoginWindow
        
        print("✅ تم تحميل نافذة تسجيل الدخول")
        print("\n" + "="*60)
        print("🎉 نظام إدارة المخازن المتطور v3.0 جاهز!")
        print("🤖 مع الذكاء الاصطناعي والتحليلات المتقدمة")
        print("="*60)
        print("📋 بيانات تسجيل الدخول:")
        print("   اسم المستخدم: admin")
        print("   كلمة المرور: admin123")
        print("="*60)
        print("🚀 الميزات الجديدة:")
        print("   • نقطة بيع ذكية مع التوصيات")
        print("   • لوحة تحكم تحليلية متقدمة")
        print("   • تقارير ذكية مع التوقعات")
        print("   • نظام أمان محسن")
        print("="*60)
        
        app = LoginWindow()
        app.run()
        
    except Exception as e:
        messagebox.showerror("خطأ في التطبيق", f"فشل في بدء التطبيق: {e}")
        return False
    
    return True

def show_system_info():
    """عرض معلومات النظام"""
    info_window = tk.Tk()
    info_window.title("معلومات النظام")
    info_window.geometry("500x400")
    info_window.resizable(False, False)
    
    # توسيط النافذة
    screen_width = info_window.winfo_screenwidth()
    screen_height = info_window.winfo_screenheight()
    x = (screen_width - 500) // 2
    y = (screen_height - 400) // 2
    info_window.geometry(f"500x400+{x}+{y}")
    
    main_frame = tk.Frame(info_window, bg="#f0f0f0", padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # العنوان
    tk.Label(main_frame, text="🤖 نظام إدارة المخازن المتطور v3.0", 
             font=("Arial", 16, "bold"), bg="#f0f0f0").pack(pady=10)
    
    # معلومات النظام
    info_text = """
🚀 الميزات الجديدة:

🤖 الذكاء الاصطناعي:
   • تحليل أنماط المبيعات
   • توقع الطلب على المنتجات
   • توصيات ذكية للعملاء
   • كشف الاتجاهات التجارية

📊 التحليلات المتقدمة:
   • رؤى تجارية ذكية
   • تحليل سلوك العملاء
   • توقعات المخزون
   • تحليل الربحية

🛒 نقطة البيع المحسنة:
   • واجهة سهلة ومتطورة
   • توصيات فورية
   • حساب خصومات ذكي
   • تحليل هامش الربح

🎛️ لوحة التحكم الذكية:
   • إحصائيات فورية
   • رسوم بيانية تفاعلية
   • تنبيهات ذكية
   • توقعات مستقبلية

📈 نظام التقارير المتطور:
   • تقارير تفاعلية
   • تحليل ذكي للبيانات
   • تصدير متقدم
   • رؤى تجارية

🔒 الأمان المحسن:
   • تشفير متقدم
   • نسخ احتياطية ذكية
   • فحص سلامة البيانات
   • نظام صلاحيات متطور
    """
    
    text_widget = tk.Text(main_frame, wrap=tk.WORD, height=15, width=50,
                         font=("Arial", 10), bg="white", relief=tk.SUNKEN, bd=2)
    text_widget.pack(fill=tk.BOTH, expand=True, pady=10)
    text_widget.insert(tk.END, info_text.strip())
    text_widget.config(state=tk.DISABLED)
    
    # معلومات المطور
    dev_frame = tk.Frame(main_frame, bg="#e0e0e0", relief=tk.RAISED, bd=2)
    dev_frame.pack(fill=tk.X, pady=10)
    
    tk.Label(dev_frame, text="👨‍💻 تصميم وتطوير: المهندس هشام المجمر", 
             font=("Arial", 12, "bold"), bg="#e0e0e0").pack(pady=5)
    tk.Label(dev_frame, text="📞 رقم الهاتف: 773988932", 
             font=("Arial", 11), bg="#e0e0e0").pack()
    tk.Label(dev_frame, text="© 2024 جميع الحقوق محفوظة", 
             font=("Arial", 10), bg="#e0e0e0").pack(pady=2)
    
    # زر الإغلاق
    tk.Button(main_frame, text="إغلاق", command=info_window.destroy,
              font=("Arial", 12), bg="#4CAF50", fg="white", 
              padx=20, pady=5).pack(pady=10)
    
    info_window.mainloop()

def main():
    """الدالة الرئيسية"""
    print("="*70)
    print("🤖 نظام إدارة المخازن المتطور v3.0 - Enhanced Edition")
    print("👨‍💻 تصميم وتطوير: المهندس هشام المجمر - 773988932")
    print("🚀 مع الذكاء الاصطناعي والتحليلات المتقدمة")
    print("© 2024 جميع الحقوق محفوظة")
    print("="*70)
    
    try:
        # عرض شاشة البدء المحسنة
        show_enhanced_splash()
        
        # فحص المتطلبات
        if not check_enhanced_requirements():
            return
        
        # تهيئة النظام
        if not initialize_enhanced_system():
            return
        
        # عرض معلومات النظام (اختياري)
        # show_system_info()
        
        # بدء التطبيق
        start_enhanced_application()
        
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف النظام بواسطة المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        messagebox.showerror("خطأ غير متوقع", 
                           f"حدث خطأ غير متوقع:\n{str(e)}\n\n"
                           "للدعم الفني:\n"
                           "المهندس هشام المجمر - 773988932")
    finally:
        print("\n🎉 شكراً لاستخدام نظام إدارة المخازن المتطور!")
        print("📞 للدعم الفني: المهندس هشام المجمر - 773988932")
        print("="*70)

if __name__ == "__main__":
    main()