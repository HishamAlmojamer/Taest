#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أدوات التحقق من صحة البيانات والتحسين
"""

import re
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import sqlite3

class DataValidator:
    """فئة للتحقق من صحة البيانات"""
    
    @staticmethod
    def validate_email(email):
        """التحقق من صحة البريد الإلكتروني"""
        if not email:
            return True  # البريد الإلكتروني اختياري
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone):
        """التحقق من صحة رقم الهاتف"""
        if not phone:
            return True  # رقم الهاتف اختياري
        
        # إزالة المسافات والرموز
        phone = re.sub(r'[^\d+]', '', phone)
        
        # التحقق من الطول والتنسيق
        if len(phone) < 10 or len(phone) > 15:
            return False
        
        # يجب أن يبدأ برقم أو +
        return phone[0].isdigit() or phone[0] == '+'
    
    @staticmethod
    def validate_price(price_str):
        """التحقق من صحة السعر"""
        try:
            price = float(price_str)
            return price >= 0
        except ValueError:
            return False
    
    @staticmethod
    def validate_quantity(quantity_str):
        """التحقق من صحة الكمية"""
        try:
            quantity = int(quantity_str)
            return quantity >= 0
        except ValueError:
            return False
    
    @staticmethod
    def validate_barcode(barcode):
        """التحقق من صحة الباركود"""
        if not barcode:
            return True  # الباركود اختياري
        
        # إزالة المسافات
        barcode = barcode.strip()
        
        # التحقق من أنه يحتوي على أرقام فقط
        if not barcode.isdigit():
            return False
        
        # التحقق من الطول (عادة 8, 12, أو 13 رقم)
        return len(barcode) in [8, 12, 13]
    
    @staticmethod
    def validate_date(date_str):
        """التحقق من صحة التاريخ"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_required_field(value, field_name):
        """التحقق من الحقول المطلوبة"""
        if not value or not value.strip():
            messagebox.showerror("خطأ", f"حقل {field_name} مطلوب")
            return False
        return True
    
    @staticmethod
    def validate_numeric_range(value_str, min_val=None, max_val=None, field_name="القيمة"):
        """التحقق من النطاق الرقمي"""
        try:
            value = float(value_str)
            
            if min_val is not None and value < min_val:
                messagebox.showerror("خطأ", f"{field_name} يجب أن يكون أكبر من أو يساوي {min_val}")
                return False
            
            if max_val is not None and value > max_val:
                messagebox.showerror("خطأ", f"{field_name} يجب أن يكون أقل من أو يساوي {max_val}")
                return False
            
            return True
            
        except ValueError:
            messagebox.showerror("خطأ", f"{field_name} يجب أن يكون رقماً صحيحاً")
            return False

class InputFormatter:
    """فئة لتنسيق المدخلات"""
    
    @staticmethod
    def format_price(price):
        """تنسيق السعر"""
        try:
            return f"{float(price):.2f}"
        except:
            return "0.00"
    
    @staticmethod
    def format_phone(phone):
        """تنسيق رقم الهاتف"""
        if not phone:
            return ""
        
        # إزالة كل شيء عدا الأرقام والعلامة +
        phone = re.sub(r'[^\d+]', '', phone)
        
        # إضافة مسافات للتنسيق
        if phone.startswith('+966'):  # السعودية
            return f"+966 {phone[4:7]} {phone[7:10]} {phone[10:]}"
        elif len(phone) == 10:
            return f"{phone[:3]} {phone[3:6]} {phone[6:]}"
        
        return phone
    
    @staticmethod
    def format_currency(amount):
        """تنسيق العملة"""
        try:
            return f"{float(amount):,.2f} ريال"
        except:
            return "0.00 ريال"
    
    @staticmethod
    def clean_text(text):
        """تنظيف النص"""
        if not text:
            return ""
        
        # إزالة المسافات الزائدة
        text = text.strip()
        
        # إزالة المسافات المتعددة
        text = re.sub(r'\s+', ' ', text)
        
        return text

class DatabaseOptimizer:
    """فئة لتحسين قاعدة البيانات"""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def optimize_database(self):
        """تحسين قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # تحليل الجداول
            cursor.execute("ANALYZE")
            
            # إعادة بناء الفهارس
            cursor.execute("REINDEX")
            
            # ضغط قاعدة البيانات
            cursor.execute("VACUUM")
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"خطأ في تحسين قاعدة البيانات: {e}")
            return False
    
    def create_indexes(self):
        """إنشاء فهارس لتحسين الأداء"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # فهارس للمنتجات
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)
            ''')
            
            # فهارس للمبيعات
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(created_at)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id)
            ''')
            
            # فهارس للمشتريات
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_purchases_date ON purchases(created_at)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_purchases_supplier ON purchases(supplier_id)
            ''')
            
            # فهارس لعناصر المبيعات والمشتريات
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sale_items_product ON sale_items(product_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_purchase_items_product ON purchase_items(product_id)
            ''')
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"خطأ في إنشاء الفهارس: {e}")
            return False
    
    def cleanup_old_data(self, days_to_keep=365):
        """تنظيف البيانات القديمة"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # حذف المبيعات القديمة (الاحتفاظ بسنة واحدة)
            cursor.execute('''
                DELETE FROM sales 
                WHERE created_at < date('now', '-{} days')
            '''.format(days_to_keep))
            
            # حذف المشتريات القديمة
            cursor.execute('''
                DELETE FROM purchases 
                WHERE created_at < date('now', '-{} days')
            '''.format(days_to_keep))
            
            # حذف حركات المخزون القديمة
            cursor.execute('''
                DELETE FROM stock_movements 
                WHERE created_at < date('now', '-{} days')
            '''.format(days_to_keep))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"خطأ في تنظيف البيانات: {e}")
            return False

class UIEnhancer:
    """فئة لتحسين واجهة المستخدم"""
    
    @staticmethod
    def add_placeholder(entry_widget, placeholder_text):
        """إضافة نص توضيحي للحقول"""
        def on_focus_in(event):
            if entry_widget.get() == placeholder_text:
                entry_widget.delete(0, tk.END)
                entry_widget.config(fg='black')
        
        def on_focus_out(event):
            if not entry_widget.get():
                entry_widget.insert(0, placeholder_text)
                entry_widget.config(fg='grey')
        
        entry_widget.insert(0, placeholder_text)
        entry_widget.config(fg='grey')
        entry_widget.bind('<FocusIn>', on_focus_in)
        entry_widget.bind('<FocusOut>', on_focus_out)
    
    @staticmethod
    def add_tooltip(widget, text):
        """إضافة تلميح للعنصر"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, background="lightyellow",
                           relief=tk.SOLID, borderwidth=1, font=("Arial", 9))
            label.pack()
            
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    @staticmethod
    def create_loading_dialog(parent, message="جاري التحميل..."):
        """إنشاء نافذة تحميل"""
        loading_window = tk.Toplevel(parent)
        loading_window.title("يرجى الانتظار")
        loading_window.geometry("300x100")
        loading_window.resizable(False, False)
        loading_window.grab_set()
        
        # توسيط النافذة
        loading_window.geometry("+%d+%d" % (
            parent.winfo_rootx() + 100,
            parent.winfo_rooty() + 100
        ))
        
        frame = tk.Frame(loading_window, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text=message, font=("Arial", 12)).pack(pady=10)
        
        # شريط التقدم
        import tkinter.ttk as ttk
        progress = ttk.Progressbar(frame, mode='indeterminate')
        progress.pack(fill=tk.X, pady=10)
        progress.start()
        
        loading_window.update()
        
        return loading_window, progress
    
    @staticmethod
    def highlight_low_stock_items(tree_widget, stock_column_index, min_stock_column_index):
        """تمييز العناصر قليلة المخزون"""
        for item in tree_widget.get_children():
            values = tree_widget.item(item)['values']
            
            try:
                current_stock = int(values[stock_column_index])
                min_stock = int(values[min_stock_column_index])
                
                if current_stock <= min_stock:
                    tree_widget.item(item, tags=('low_stock',))
                elif current_stock <= min_stock * 1.5:
                    tree_widget.item(item, tags=('warning_stock',))
                    
            except (ValueError, IndexError):
                continue
        
        # تكوين الألوان
        tree_widget.tag_configure('low_stock', background='#ffcccc')
        tree_widget.tag_configure('warning_stock', background='#fff3cd')

class PerformanceMonitor:
    """مراقب الأداء"""
    
    def __init__(self):
        self.start_time = None
        self.operations = []
    
    def start_operation(self, operation_name):
        """بدء مراقبة عملية"""
        self.start_time = datetime.now()
        self.current_operation = operation_name
    
    def end_operation(self):
        """انتهاء مراقبة العملية"""
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            self.operations.append({
                'operation': self.current_operation,
                'duration': duration,
                'timestamp': datetime.now()
            })
            
            # تحذير إذا كانت العملية بطيئة
            if duration > 2.0:  # أكثر من ثانيتين
                print(f"تحذير: العملية '{self.current_operation}' استغرقت {duration:.2f} ثانية")
    
    def get_performance_report(self):
        """الحصول على تقرير الأداء"""
        if not self.operations:
            return "لا توجد عمليات مسجلة"
        
        report = "تقرير الأداء:\n"
        report += "=" * 50 + "\n"
        
        for op in self.operations[-10:]:  # آخر 10 عمليات
            report += f"{op['operation']}: {op['duration']:.2f} ثانية\n"
        
        # متوسط الأداء
        avg_duration = sum(op['duration'] for op in self.operations) / len(self.operations)
        report += f"\nمتوسط وقت العمليات: {avg_duration:.2f} ثانية"
        
        return report