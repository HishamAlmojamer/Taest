#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف التشغيل النهائي المحسن للنظام
تصميم: المهندس هشام المجمر - 773988932
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import time

# إضافة المجلد الحالي إلى مسار Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def show_enhanced_splash():
    """عرض شاشة بدء محسنة"""
    splash = tk.Tk()
    splash.title("نظام إدارة المخازن المتطور")
    splash.geometry("700x500")
    splash.resizable(False, False)
    splash.overrideredirect(True)
    
    # توسيط النافذة
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - 700) // 2
    y = (screen_height - 500) // 2
    splash.geometry(f"700x500+{x}+{y}")
    
    # خلفية متدرجة
    main_frame = tk.Frame(splash, bg="#0f2027", relief=tk.RAISED, bd=5)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # إطار العنوان
    title_frame = tk.Frame(main_frame, bg="#0f2027")
    title_frame.pack(expand=True, pady=40)
    
    # أيقونة النظام المحسنة
    icon_frame = tk.Frame(title_frame, bg="#0f2027")
    icon_frame.pack(pady=20)
    
    tk.Label(icon_frame, text="🏪", font=("Arial", 48), 
             bg="#0f2027", fg="#00d4ff").pack(side=tk.LEFT, padx=5)
    tk.Label(icon_frame, text="🤖", font=("Arial", 48), 
             bg="#0f2027", fg="#ff6b35").pack(side=tk.LEFT, padx=5)
    tk.Label(icon_frame, text="⚡", font=("Arial", 48), 
             bg="#0f2027", fg="#ffd700").pack(side=tk.LEFT, padx=5)
    
    # اسم النظام
    tk.Label(title_frame, text="نظام إدارة المخازن المتطور", 
             font=("Arial", 28, "bold"), bg="#0f2027", fg="white").pack(pady=10)
    
    # الإصدار والوصف
    tk.Label(title_frame, text="الإصدار 3.0 - Enhanced AI Edition", 
             font=("Arial", 16), bg="#0f2027", fg="#00d4ff").pack(pady=5)
    
    tk.Label(title_frame, text="مع الذكاء الاصطناعي والتحليلات المتقدمة", 
             font=("Arial", 14), bg="#0f2027", fg="#a0a0a0").pack(pady=5)
    
    # الميزات
    features_frame = tk.Frame(title_frame, bg="#0f2027")
    features_frame.pack(pady=20)
    
    features = [
        "🛒 نقطة بيع ذكية",
        "📊 تحليلات متقدمة", 
        "🔒 أمان عالي",
        "⚡ أداء فائق"
    ]
    
    for i, feature in enumerate(features):
        row = i // 2
        col = i % 2
        tk.Label(features_frame, text=feature, font=("Arial", 12), 
                bg="#0f2027", fg="#ffd700").grid(row=row, column=col, padx=20, pady=5)
    
    # معلومات المطور
    developer_frame = tk.Frame(main_frame, bg="#0f2027")
    developer_frame.pack(side=tk.BOTTOM, pady=30)
    
    tk.Label(developer_frame, text="تصميم وتطوير: المهندس هشام المجمر", 
             font=("Arial", 14, "bold"), bg="#0f2027", fg="#ff6b35").pack()
    
    tk.Label(developer_frame, text="📞 773988932", 
             font=("Arial", 12), bg="#0f2027", fg="#00d4ff").pack(pady=2)
    
    tk.Label(developer_frame, text="© 2024 جميع الحقوق محفوظة", 
             font=("Arial", 10), bg="#0f2027", fg="#a0a0a0").pack(pady=5)
    
    # شريط التقدم المحسن
    progress_frame = tk.Frame(main_frame, bg="#0f2027")
    progress_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=60, pady=30)
    
    # خلفية شريط التقدم
    progress_bg = tk.Frame(progress_frame, bg="#2a2a2a", height=12, relief=tk.SUNKEN, bd=2)
    progress_bg.pack(fill=tk.X)
    
    # شريط التقدم الفعلي
    progress_bar = tk.Frame(progress_bg, bg="#00ff88", height=8)
    progress_bar.pack(side=tk.LEFT, fill=tk.Y)
    
    # نص الحالة
    status_label = tk.Label(progress_frame, text="جاري التحميل...", 
                           font=("Arial", 12, "bold"), bg="#0f2027", fg="white")
    status_label.pack(pady=(15, 0))
    
    splash.update()
    
    # خطوات التحميل المحسنة
    loading_steps = [
        ("🔍 فحص متطلبات النظام المتقدمة...", 0.1),
        ("🤖 تهيئة محرك الذكاء الاصطناعي...", 0.2),
        ("💾 تحميل قاعدة البيانات المحسنة...", 0.3),
        ("🔐 إعداد نظام الأمان المتطور...", 0.4),
        ("🛒 تحميل نقطة البيع الذكية...", 0.5),
        ("🎛️ إعداد لوحة التحكم التفاعلية...", 0.6),
        ("📊 تحميل نظام التقارير الذكية...", 0.7),
        ("⚡ تحسين الأداء والسرعة...", 0.8),
        ("🔒 فحص الأمان والحماية...", 0.9),
        ("🚀 إنهاء التحضيرات النهائية...", 1.0)
    ]
    
    for step_text, progress in loading_steps:
        status_label.config(text=step_text)
        progress_width = int(progress * 580)  # 580 هو العرض الأقصى
        progress_bar.config(width=progress_width)
        
        # تأثير لوني للشريط
        if progress < 0.3:
            progress_bar.config(bg="#ff6b35")  # برتقالي
        elif progress < 0.7:
            progress_bar.config(bg="#ffd700")  # ذهبي
        else:
            progress_bar.config(bg="#00ff88")  # أخضر
        
        splash.update()
        time.sleep(0.8)
    
    # رسالة الترحيب النهائية
    status_label.config(text="🎉 مرحباً بك في النظام المتطور!", fg="#00ff88")
    splash.update()
    time.sleep(1.5)
    
    splash.destroy()

def run_system_diagnostics():
    """تشغيل تشخيص سريع للنظام"""
    print("🔧 تشغيل تشخيص سريع للنظام...")
    
    try:
        # فحص قاعدة البيانات
        from database import Database
        db = Database()
        conn = db.get_connection()
        
        # فحص الجداول الأساسية
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if len(tables) < 10:
            print("⚠️ تحذير: قد تكون بعض الجداول مفقودة")
        else:
            print("✅ قاعدة البيانات سليمة")
        
        # فحص بيانات المبيعات
        cursor.execute("SELECT COUNT(*) FROM sales")
        sales_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM products")
        products_count = cursor.fetchone()[0]
        
        print(f"📊 الإحصائيات: {products_count} منتج، {sales_count} فاتورة")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"⚠️ تحذير في التشخيص: {e}")
        return True  # لا نوقف النظام

def start_system():
    """تشغيل النظام الرئيسي"""
    print("🚀 بدء تشغيل النظام...")
    
    try:
        # محاولة تشغيل النظام المحسن أولاً
        if os.path.exists("launch_enhanced_system.py"):
            print("🎯 تشغيل النظام المحسن...")
            from launch_enhanced_system import main as enhanced_main
            enhanced_main()
        elif os.path.exists("start_system.py"):
            print("🔄 تشغيل النظام المتقدم...")
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

def show_welcome_message():
    """عرض رسالة الترحيب"""
    print("\n" + "=" * 80)
    print("🎉 مرحباً بك في نظام إدارة المخازن المتطور v3.0")
    print("=" * 80)
    
    print("\n🎯 الميزات الرئيسية:")
    print("🤖 الذكاء الاصطناعي والتحليلات المتقدمة")
    print("🛒 نقطة بيع ذكية مع التوصيات الفورية")
    print("🎛️ لوحة تحكم تفاعلية مع الرسوم البيانية")
    print("📊 تقارير ذكية مع التوقعات المستقبلية")
    print("🔒 نظام أمان متطور مع الصلاحيات المتقدمة")
    print("👥 إدارة شاملة للعملاء والموردين")
    print("📦 إدارة متقدمة للمخزون مع التنبيهات الذكية")
    
    print("\n📋 بيانات تسجيل الدخول:")
    print("   👤 اسم المستخدم: admin")
    print("   🔑 كلمة المرور: admin123")
    print("   🎭 الدور: مدير عام (صلاحيات كاملة)")
    
    print("\n📞 الدعم الفني:")
    print("   المهندس هشام المجمر")
    print("   📱 773988932")
    print("   ⏰ متاح: السبت - الخميس (9 ص - 6 م)")
    
    print("\n💡 نصائح للاستخدام:")
    print("• استخدم الذكاء الاصطناعي للحصول على رؤى تجارية")
    print("• راجع التقارير الذكية لتحسين الأداء")
    print("• فعّل التنبيهات للمخزون المنخفض")
    print("• استفد من التوصيات في نقطة البيع")
    
    print("=" * 80)

def main():
    """الدالة الرئيسية المحسنة"""
    print("=" * 80)
    print("🤖🏪 نظام إدارة المخازن المتطور v3.0 - Enhanced AI Edition")
    print("👨‍💻 تصميم وتطوير: المهندس هشام المجمر - 773988932")
    print("🚀 مع الذكاء الاصطناعي والتحليلات المتقدمة")
    print("© 2024 جميع الحقوق محفوظة")
    print("=" * 80)
    
    try:
        # عرض شاشة البدء المحسنة
        show_enhanced_splash()
        
        # تشغيل التشخيص السريع
        run_system_diagnostics()
        
        # عرض رسالة الترحيب
        show_welcome_message()
        
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
        print("\n" + "=" * 80)
        print("👋 شكراً لاستخدام نظام إدارة المخازن المتطور!")
        print("📞 للدعم الفني: المهندس هشام المجمر - 773988932")
        print("🌟 نتمنى لك تجربة ممتازة مع النظام!")
        print("=" * 80)

if __name__ == "__main__":
    main()