#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف التشغيل المحسن لنظام إدارة المخازن
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import threading
import time

# إضافة المجلد الحالي إلى مسار Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_requirements():
    """فحص المتطلبات"""
    missing_modules = []
    
    try:
        import sqlite3
    except ImportError:
        missing_modules.append("sqlite3")
    
    try:
        import tkinter
    except ImportError:
        missing_modules.append("tkinter")
    
    # فحص المكتبات الاختيارية
    optional_modules = {
        'matplotlib': 'للرسوم البيانية',
        'pandas': 'لمعالجة البيانات',
        'reportlab': 'لإنشاء ملفات PDF',
        'pillow': 'لمعالجة الصور',
        'cryptography': 'للتشفير المتقدم'
    }
    
    missing_optional = []
    for module, description in optional_modules.items():
        try:
            __import__(module)
        except ImportError:
            missing_optional.append(f"{module} - {description}")
    
    return missing_modules, missing_optional

def show_startup_screen():
    """عرض شاشة البدء"""
    startup = tk.Tk()
    startup.title("نظام إدارة المخازن")
    startup.geometry("400x300")
    startup.resizable(False, False)
    
    # توسيط النافذة
    screen_width = startup.winfo_screenwidth()
    screen_height = startup.winfo_screenheight()
    x = (screen_width - 400) // 2
    y = (screen_height - 300) // 2
    startup.geometry(f"400x300+{x}+{y}")
    
    # إزالة شريط العنوان
    startup.overrideredirect(True)
    
    # الخلفية
    main_frame = tk.Frame(startup, bg="#2196F3", relief=tk.RAISED, bd=2)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # الشعار والعنوان
    title_frame = tk.Frame(main_frame, bg="#2196F3")
    title_frame.pack(expand=True)
    
    tk.Label(title_frame, text="🏪", font=("Arial", 48), 
             bg="#2196F3", fg="white").pack(pady=10)
    
    tk.Label(title_frame, text="نظام إدارة المخازن", 
             font=("Arial", 18, "bold"), bg="#2196F3", fg="white").pack()
    
    tk.Label(title_frame, text="نظام شامل لإدارة المخازن والمبيعات", 
             font=("Arial", 12), bg="#2196F3", fg="white").pack(pady=5)
    
    # شريط التقدم
    progress_frame = tk.Frame(main_frame, bg="#2196F3")
    progress_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)
    
    progress_bg = tk.Frame(progress_frame, bg="white", height=6)
    progress_bg.pack(fill=tk.X)
    
    progress_bar = tk.Frame(progress_bg, bg="#4CAF50", height=6)
    progress_bar.pack(side=tk.LEFT)
    
    status_label = tk.Label(progress_frame, text="جاري التحميل...", 
                           font=("Arial", 10), bg="#2196F3", fg="white")
    status_label.pack(pady=(10, 0))
    
    startup.update()
    
    # محاكاة التحميل
    steps = [
        "فحص المتطلبات...",
        "تحميل قاعدة البيانات...",
        "تهيئة الواجهات...",
        "تحميل الإعدادات...",
        "جاري البدء..."
    ]
    
    for i, step in enumerate(steps):
        status_label.config(text=step)
        progress_width = int((i + 1) / len(steps) * 360)  # 360 هو عرض شريط التقدم
        progress_bar.config(width=progress_width)
        startup.update()
        time.sleep(0.5)
    
    startup.destroy()

def initialize_database():
    """تهيئة قاعدة البيانات"""
    try:
        from database import Database
        db = Database()
        return True
    except Exception as e:
        messagebox.showerror("خطأ في قاعدة البيانات", 
                           f"فشل في تهيئة قاعدة البيانات:\n{str(e)}")
        return False

def optimize_system():
    """تحسين النظام"""
    try:
        from validation_utils import DatabaseOptimizer
        from security_utils import BackupManager
        
        # تحسين قاعدة البيانات
        optimizer = DatabaseOptimizer("warehouse_management.db")
        optimizer.create_indexes()
        
        # إنشاء نسخة احتياطية تلقائية
        backup_manager = BackupManager("warehouse_management.db")
        backup_manager.schedule_automatic_backup(24)  # كل 24 ساعة
        
        return True
    except Exception as e:
        print(f"تحذير: فشل في تحسين النظام: {e}")
        return True  # لا نوقف البرنامج بسبب هذا

def run_system_checks():
    """تشغيل فحوصات النظام"""
    try:
        from security_utils import DataIntegrityChecker
        
        checker = DataIntegrityChecker("warehouse_management.db")
        
        # فحص سلامة قاعدة البيانات
        if not checker.check_database_integrity():
            response = messagebox.askyesno("مشكلة في قاعدة البيانات",
                                         "تم اكتشاف مشكلة في قاعدة البيانات.\nهل تريد محاولة إصلاحها؟")
            if response:
                checker.fix_data_issues()
        
        # فحص سلامة المراجع
        is_valid, issues = checker.check_referential_integrity()
        if not is_valid:
            messagebox.showwarning("تحذير", 
                                 f"تم اكتشاف مشاكل في البيانات:\n" + "\n".join(issues))
        
        return True
    except Exception as e:
        print(f"تحذير: فشل في فحص النظام: {e}")
        return True

def main():
    """الدالة الرئيسية"""
    try:
        # فحص المتطلبات
        missing_required, missing_optional = check_requirements()
        
        if missing_required:
            messagebox.showerror("مكتبات مفقودة", 
                               f"المكتبات التالية مطلوبة:\n" + "\n".join(missing_required))
            return
        
        if missing_optional:
            response = messagebox.askyesno("مكتبات اختيارية مفقودة",
                                         f"المكتبات التالية اختيارية ولكن موصى بها:\n" + 
                                         "\n".join(missing_optional) + 
                                         "\n\nهل تريد المتابعة بدونها؟")
            if not response:
                return
        
        # عرض شاشة البدء
        show_startup_screen()
        
        # تهيئة قاعدة البيانات
        if not initialize_database():
            return
        
        # تشغيل فحوصات النظام
        run_system_checks()
        
        # تحسين النظام
        optimize_system()
        
        # تشغيل البرنامج الرئيسي
        from login_window import LoginWindow
        app = LoginWindow()
        app.run()
        
    except KeyboardInterrupt:
        print("\nتم إيقاف البرنامج بواسطة المستخدم")
    except Exception as e:
        messagebox.showerror("خطأ غير متوقع", 
                           f"حدث خطأ غير متوقع:\n{str(e)}\n\nيرجى إعادة تشغيل البرنامج")
        print(f"خطأ: {e}")

if __name__ == "__main__":
    main()