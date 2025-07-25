#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام التقارير المحسن مع الذكاء الاصطناعي
تصميم: المهندس هشام المجمر - 773988932
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font
from datetime import datetime, timedelta
import json
import csv
import sqlite3
from ai_analytics import AIAnalyticsEngine
import threading

class EnhancedReportsWindow:
    """نافذة التقارير المحسنة"""
    
    def __init__(self, parent, db, user):
        self.parent = parent
        self.db = db
        self.user = user
        
        # محرك التحليلات
        self.ai_analytics = AIAnalyticsEngine(db.db_path)
        
        # إنشاء النافذة
        self.window = tk.Toplevel(parent)
        self.window.title("📊 التقارير الذكية - المطور: هشام المجمر 773988932")
        self.window.geometry("1200x700")
        self.window.state('zoomed')
        self.window.grab_set()
        
        # الألوان والخطوط
        self.setup_styles()
        
        # المتغيرات
        self.setup_variables()
        
        # إنشاء الواجهة
        self.create_widgets()
        
        # تحميل البيانات الأولية
        self.load_initial_data()
    
    def setup_styles(self):
        """إعداد الألوان والخطوط"""
        self.colors = {
            'primary': '#2196F3',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'danger': '#F44336',
            'info': '#00BCD4',
            'light': '#F5F5F5',
            'dark': '#333333'
        }
        
        self.fonts = {
            'title': font.Font(family="Arial", size=16, weight="bold"),
            'subtitle': font.Font(family="Arial", size=12, weight="bold"),
            'normal': font.Font(family="Arial", size=10),
            'small': font.Font(family="Arial", size=9)
        }
    
    def setup_variables(self):
        """إعداد المتغيرات"""
        # متغيرات التواريخ
        self.start_date_var = tk.StringVar(value=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        self.end_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        
        # متغيرات التصفية
        self.report_type_var = tk.StringVar(value="المبيعات")
        self.customer_filter_var = tk.StringVar()
        self.product_filter_var = tk.StringVar()
        self.category_filter_var = tk.StringVar()
        
        # متغيرات الإحصائيات
        self.total_records_var = tk.StringVar(value="0")
        self.total_amount_var = tk.StringVar(value="0.00")
        self.avg_amount_var = tk.StringVar(value="0.00")
        
        # بيانات التقارير
        self.report_data = []
        self.filtered_data = []
    
    def create_widgets(self):
        """إنشاء عناصر الواجهة"""
        # الإطار الرئيسي
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # شريط العنوان
        self.create_header(main_frame)
        
        # لوحة التحكم
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        # الجانب الأيسر - خيارات التقرير
        self.create_report_options(control_frame)
        
        # الجانب الأيمن - الإحصائيات السريعة
        self.create_quick_stats(control_frame)
        
        # منطقة التقرير الرئيسية
        report_frame = ttk.Frame(main_frame)
        report_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # تبويبات التقارير
        self.create_report_tabs(report_frame)
        
        # شريط الحالة
        self.create_status_bar(main_frame)
    
    def create_header(self, parent):
        """إنشاء شريط العنوان"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X)
        
        # العنوان
        title_label = ttk.Label(header_frame, text="📊 التقارير الذكية", 
                               font=self.fonts['title'])
        title_label.pack(side=tk.LEFT)
        
        # أزرار التحكم
        buttons_frame = ttk.Frame(header_frame)
        buttons_frame.pack(side=tk.RIGHT)
        
        ttk.Button(buttons_frame, text="🔄 تحديث", 
                  command=self.refresh_report).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(buttons_frame, text="📤 تصدير", 
                  command=self.export_report).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(buttons_frame, text="🖨️ طباعة", 
                  command=self.print_report).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(buttons_frame, text="🤖 تحليل ذكي", 
                  command=self.generate_ai_analysis).pack(side=tk.LEFT, padx=2)
    
    def create_report_options(self, parent):
        """إنشاء خيارات التقرير"""
        options_frame = ttk.LabelFrame(parent, text="⚙️ خيارات التقرير", padding="10")
        options_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # الصف الأول - نوع التقرير والتواريخ
        row1 = ttk.Frame(options_frame)
        row1.pack(fill=tk.X, pady=(0, 10))
        
        # نوع التقرير
        ttk.Label(row1, text="نوع التقرير:").pack(side=tk.LEFT)
        report_types = ["المبيعات", "المشتريات", "المخزون", "العملاء", "المنتجات", "الأرباح"]
        report_combo = ttk.Combobox(row1, textvariable=self.report_type_var,
                                   values=report_types, state="readonly", width=12)
        report_combo.pack(side=tk.LEFT, padx=(5, 15))
        report_combo.bind('<<ComboboxSelected>>', self.on_report_type_change)
        
        # تاريخ البداية
        ttk.Label(row1, text="من:").pack(side=tk.LEFT)
        start_date_entry = ttk.Entry(row1, textvariable=self.start_date_var, width=12)
        start_date_entry.pack(side=tk.LEFT, padx=(5, 15))
        
        # تاريخ النهاية
        ttk.Label(row1, text="إلى:").pack(side=tk.LEFT)
        end_date_entry = ttk.Entry(row1, textvariable=self.end_date_var, width=12)
        end_date_entry.pack(side=tk.LEFT, padx=(5, 15))
        
        # زر إنشاء التقرير
        ttk.Button(row1, text="📊 إنشاء التقرير", 
                  command=self.generate_report).pack(side=tk.LEFT, padx=(10, 0))
        
        # الصف الثاني - فلاتر إضافية
        row2 = ttk.Frame(options_frame)
        row2.pack(fill=tk.X)
        
        # فلتر العميل
        ttk.Label(row2, text="العميل:").pack(side=tk.LEFT)
        customer_combo = ttk.Combobox(row2, textvariable=self.customer_filter_var, width=15)
        customer_combo.pack(side=tk.LEFT, padx=(5, 15))
        
        # فلتر المنتج
        ttk.Label(row2, text="المنتج:").pack(side=tk.LEFT)
        product_combo = ttk.Combobox(row2, textvariable=self.product_filter_var, width=15)
        product_combo.pack(side=tk.LEFT, padx=(5, 15))
        
        # فلتر الفئة
        ttk.Label(row2, text="الفئة:").pack(side=tk.LEFT)
        category_combo = ttk.Combobox(row2, textvariable=self.category_filter_var, width=15)
        category_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # حفظ مراجع الكومبو بوكس
        self.customer_combo = customer_combo
        self.product_combo = product_combo
        self.category_combo = category_combo
    
    def create_quick_stats(self, parent):
        """إنشاء الإحصائيات السريعة"""
        stats_frame = ttk.LabelFrame(parent, text="📈 إحصائيات سريعة", padding="10")
        stats_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # عدد السجلات
        records_frame = ttk.Frame(stats_frame)
        records_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(records_frame, text="عدد السجلات:", font=self.fonts['small']).pack(side=tk.LEFT)
        ttk.Label(records_frame, textvariable=self.total_records_var, 
                 font=self.fonts['subtitle']).pack(side=tk.RIGHT)
        
        # الإجمالي
        total_frame = ttk.Frame(stats_frame)
        total_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(total_frame, text="الإجمالي:", font=self.fonts['small']).pack(side=tk.LEFT)
        ttk.Label(total_frame, textvariable=self.total_amount_var, 
                 font=self.fonts['subtitle']).pack(side=tk.RIGHT)
        
        # المتوسط
        avg_frame = ttk.Frame(stats_frame)
        avg_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(avg_frame, text="المتوسط:", font=self.fonts['small']).pack(side=tk.LEFT)
        ttk.Label(avg_frame, textvariable=self.avg_amount_var, 
                 font=self.fonts['subtitle']).pack(side=tk.RIGHT)
    
    def create_report_tabs(self, parent):
        """إنشاء تبويبات التقارير"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # تبويب البيانات الجدولية
        self.create_data_tab()
        
        # تبويب الرسوم البيانية
        self.create_charts_tab()
        
        # تبويب التحليل الذكي
        self.create_analysis_tab()
        
        # تبويب التوصيات
        self.create_recommendations_tab()
    
    def create_data_tab(self):
        """إنشاء تبويب البيانات"""
        data_frame = ttk.Frame(self.notebook)
        self.notebook.add(data_frame, text="📋 البيانات")
        
        # شريط البحث
        search_frame = ttk.Frame(data_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="🔍 البحث:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(5, 10))
        search_entry.bind('<KeyRelease>', self.on_search_change)
        
        ttk.Button(search_frame, text="🗑️ مسح", 
                  command=self.clear_search).pack(side=tk.LEFT)
        
        # جدول البيانات
        table_frame = ttk.Frame(data_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # إنشاء الجدول (سيتم تحديد الأعمدة حسب نوع التقرير)
        self.data_tree = ttk.Treeview(table_frame, show='headings', height=20)
        
        # شريط التمرير
        data_scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, 
                                        command=self.data_tree.yview)
        data_scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, 
                                        command=self.data_tree.xview)
        
        self.data_tree.configure(yscrollcommand=data_scrollbar_y.set,
                                xscrollcommand=data_scrollbar_x.set)
        
        self.data_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        data_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        data_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_charts_tab(self):
        """إنشاء تبويب الرسوم البيانية"""
        charts_frame = ttk.Frame(self.notebook)
        self.notebook.add(charts_frame, text="📊 الرسوم البيانية")
        
        # خيارات الرسم البياني
        chart_options_frame = ttk.LabelFrame(charts_frame, text="خيارات الرسم", padding="10")
        chart_options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.chart_type_var = tk.StringVar(value="خطي")
        chart_types = ["خطي", "أعمدة", "دائري", "منطقة"]
        
        ttk.Label(chart_options_frame, text="نوع الرسم:").pack(side=tk.LEFT)
        chart_type_combo = ttk.Combobox(chart_options_frame, textvariable=self.chart_type_var,
                                       values=chart_types, state="readonly", width=10)
        chart_type_combo.pack(side=tk.LEFT, padx=(5, 15))
        
        ttk.Button(chart_options_frame, text="📊 إنشاء الرسم", 
                  command=self.generate_chart).pack(side=tk.LEFT)
        
        # منطقة الرسم البياني
        chart_display_frame = ttk.LabelFrame(charts_frame, text="الرسم البياني", padding="10")
        chart_display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # رسم بياني نصي بسيط
        self.chart_text = tk.Text(chart_display_frame, height=20, font=self.fonts['small'])
        self.chart_text.pack(fill=tk.BOTH, expand=True)
        
        chart_scrollbar = ttk.Scrollbar(chart_display_frame, orient=tk.VERTICAL, 
                                       command=self.chart_text.yview)
        self.chart_text.configure(yscrollcommand=chart_scrollbar.set)
        chart_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_analysis_tab(self):
        """إنشاء تبويب التحليل الذكي"""
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="🤖 التحليل الذكي")
        
        # أزرار التحليل
        analysis_buttons_frame = ttk.Frame(analysis_frame)
        analysis_buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(analysis_buttons_frame, text="📈 تحليل الاتجاهات", 
                  command=self.analyze_trends).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(analysis_buttons_frame, text="🔍 كشف الأنماط", 
                  command=self.detect_patterns).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(analysis_buttons_frame, text="🎯 توقعات المبيعات", 
                  command=self.predict_sales).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(analysis_buttons_frame, text="💡 رؤى تجارية", 
                  command=self.generate_business_insights).pack(side=tk.LEFT, padx=2)
        
        # منطقة عرض التحليل
        analysis_display_frame = ttk.LabelFrame(analysis_frame, text="نتائج التحليل", padding="10")
        analysis_display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.analysis_text = tk.Text(analysis_display_frame, height=20, font=self.fonts['normal'])
        self.analysis_text.pack(fill=tk.BOTH, expand=True)
        
        analysis_scrollbar = ttk.Scrollbar(analysis_display_frame, orient=tk.VERTICAL, 
                                          command=self.analysis_text.yview)
        self.analysis_text.configure(yscrollcommand=analysis_scrollbar.set)
        analysis_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_recommendations_tab(self):
        """إنشاء تبويب التوصيات"""
        recommendations_frame = ttk.Frame(self.notebook)
        self.notebook.add(recommendations_frame, text="💡 التوصيات")
        
        # أنواع التوصيات
        rec_types_frame = ttk.Frame(recommendations_frame)
        rec_types_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(rec_types_frame, text="🛒 توصيات المنتجات", 
                  command=self.generate_product_recommendations).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(rec_types_frame, text="👥 توصيات العملاء", 
                  command=self.generate_customer_recommendations).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(rec_types_frame, text="💰 توصيات التسعير", 
                  command=self.generate_pricing_recommendations).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(rec_types_frame, text="📦 توصيات المخزون", 
                  command=self.generate_inventory_recommendations).pack(side=tk.LEFT, padx=2)
        
        # منطقة عرض التوصيات
        recommendations_display_frame = ttk.LabelFrame(recommendations_frame, text="التوصيات", padding="10")
        recommendations_display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.recommendations_text = tk.Text(recommendations_display_frame, height=20, font=self.fonts['normal'])
        self.recommendations_text.pack(fill=tk.BOTH, expand=True)
        
        recommendations_scrollbar = ttk.Scrollbar(recommendations_display_frame, orient=tk.VERTICAL, 
                                                 command=self.recommendations_text.yview)
        self.recommendations_text.configure(yscrollcommand=recommendations_scrollbar.set)
        recommendations_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_status_bar(self, parent):
        """إنشاء شريط الحالة"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_var = tk.StringVar(value="جاهز")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)
        
        # معلومات إضافية
        info_frame = ttk.Frame(status_frame)
        info_frame.pack(side=tk.RIGHT)
        
        self.time_var = tk.StringVar()
        ttk.Label(info_frame, textvariable=self.time_var).pack(side=tk.LEFT)
        
        self.update_time()
    
    def load_initial_data(self):
        """تحميل البيانات الأولية"""
        self.load_filter_options()
        self.generate_report()
    
    def load_filter_options(self):
        """تحميل خيارات الفلاتر"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # تحميل العملاء
            cursor.execute('SELECT name FROM customers ORDER BY name')
            customers = ["جميع العملاء"] + [row[0] for row in cursor.fetchall()]
            self.customer_combo['values'] = customers
            self.customer_combo.set("جميع العملاء")
            
            # تحميل المنتجات
            cursor.execute('SELECT name FROM products ORDER BY name')
            products = ["جميع المنتجات"] + [row[0] for row in cursor.fetchall()]
            self.product_combo['values'] = products
            self.product_combo.set("جميع المنتجات")
            
            # تحميل الفئات
            cursor.execute('SELECT name FROM categories ORDER BY name')
            categories = ["جميع الفئات"] + [row[0] for row in cursor.fetchall()]
            self.category_combo['values'] = categories
            self.category_combo.set("جميع الفئات")
            
        except Exception as e:
            print(f"خطأ في تحميل خيارات الفلاتر: {e}")
        finally:
            conn.close()
    
    def on_report_type_change(self, event=None):
        """عند تغيير نوع التقرير"""
        self.generate_report()
    
    def generate_report(self):
        """إنشاء التقرير"""
        def generate():
            try:
                self.status_var.set("جاري إنشاء التقرير...")
                
                report_type = self.report_type_var.get()
                start_date = self.start_date_var.get()
                end_date = self.end_date_var.get()
                
                if report_type == "المبيعات":
                    self.generate_sales_report(start_date, end_date)
                elif report_type == "المشتريات":
                    self.generate_purchases_report(start_date, end_date)
                elif report_type == "المخزون":
                    self.generate_inventory_report()
                elif report_type == "العملاء":
                    self.generate_customers_report(start_date, end_date)
                elif report_type == "المنتجات":
                    self.generate_products_report(start_date, end_date)
                elif report_type == "الأرباح":
                    self.generate_profit_report(start_date, end_date)
                
                self.update_quick_stats()
                self.status_var.set("تم إنشاء التقرير بنجاح")
                
            except Exception as e:
                self.status_var.set(f"خطأ في إنشاء التقرير: {e}")
                messagebox.showerror("خطأ", f"فشل في إنشاء التقرير: {e}")
        
        # تشغيل في خيط منفصل
        threading.Thread(target=generate, daemon=True).start()
    
    def generate_sales_report(self, start_date, end_date):
        """إنشاء تقرير المبيعات"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # تحديد أعمدة الجدول
            columns = ('date', 'invoice', 'customer', 'product', 'quantity', 'price', 'total')
            self.data_tree['columns'] = columns
            
            # تعريف الأعمدة
            self.data_tree.heading('date', text='التاريخ')
            self.data_tree.heading('invoice', text='رقم الفاتورة')
            self.data_tree.heading('customer', text='العميل')
            self.data_tree.heading('product', text='المنتج')
            self.data_tree.heading('quantity', text='الكمية')
            self.data_tree.heading('price', text='السعر')
            self.data_tree.heading('total', text='الإجمالي')
            
            # تحديد عرض الأعمدة
            self.data_tree.column('date', width=100)
            self.data_tree.column('invoice', width=80)
            self.data_tree.column('customer', width=150)
            self.data_tree.column('product', width=200)
            self.data_tree.column('quantity', width=80)
            self.data_tree.column('price', width=80)
            self.data_tree.column('total', width=100)
            
            # جلب البيانات
            cursor.execute('''
                SELECT 
                    DATE(s.sale_date) as sale_date,
                    s.id as invoice_id,
                    COALESCE(c.name, 'عميل مجهول') as customer_name,
                    p.name as product_name,
                    si.quantity,
                    si.unit_price,
                    si.total
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                JOIN sale_items si ON s.id = si.sale_id
                JOIN products p ON si.product_id = p.id
                WHERE DATE(s.sale_date) BETWEEN ? AND ?
                ORDER BY s.sale_date DESC, s.id DESC
            ''', (start_date, end_date))
            
            self.report_data = cursor.fetchall()
            self.filtered_data = self.report_data.copy()
            
            # مسح البيانات الحالية
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)
            
            # إضافة البيانات الجديدة
            for row in self.report_data:
                self.data_tree.insert('', tk.END, values=row)
            
        except Exception as e:
            raise e
        finally:
            conn.close()
    
    def generate_purchases_report(self, start_date, end_date):
        """إنشاء تقرير المشتريات"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            columns = ('date', 'invoice', 'supplier', 'product', 'quantity', 'price', 'total')
            self.data_tree['columns'] = columns
            
            self.data_tree.heading('date', text='التاريخ')
            self.data_tree.heading('invoice', text='رقم الفاتورة')
            self.data_tree.heading('supplier', text='المورد')
            self.data_tree.heading('product', text='المنتج')
            self.data_tree.heading('quantity', text='الكمية')
            self.data_tree.heading('price', text='السعر')
            self.data_tree.heading('total', text='الإجمالي')
            
            cursor.execute('''
                SELECT 
                    DATE(p.purchase_date) as purchase_date,
                    p.id as invoice_id,
                    COALESCE(s.name, 'مورد مجهول') as supplier_name,
                    pr.name as product_name,
                    pi.quantity,
                    pi.unit_price,
                    pi.total
                FROM purchases p
                LEFT JOIN suppliers s ON p.supplier_id = s.id
                JOIN purchase_items pi ON p.id = pi.purchase_id
                JOIN products pr ON pi.product_id = pr.id
                WHERE DATE(p.purchase_date) BETWEEN ? AND ?
                ORDER BY p.purchase_date DESC, p.id DESC
            ''', (start_date, end_date))
            
            self.report_data = cursor.fetchall()
            self.filtered_data = self.report_data.copy()
            
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)
            
            for row in self.report_data:
                self.data_tree.insert('', tk.END, values=row)
            
        except Exception as e:
            raise e
        finally:
            conn.close()
    
    def generate_inventory_report(self):
        """إنشاء تقرير المخزون"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            columns = ('product', 'category', 'stock', 'min_stock', 'price', 'value', 'status')
            self.data_tree['columns'] = columns
            
            self.data_tree.heading('product', text='المنتج')
            self.data_tree.heading('category', text='الفئة')
            self.data_tree.heading('stock', text='المخزون')
            self.data_tree.heading('min_stock', text='الحد الأدنى')
            self.data_tree.heading('price', text='السعر')
            self.data_tree.heading('value', text='القيمة')
            self.data_tree.heading('status', text='الحالة')
            
            cursor.execute('''
                SELECT 
                    p.name as product_name,
                    COALESCE(c.name, 'غير محدد') as category_name,
                    p.stock,
                    p.min_stock,
                    p.price,
                    (p.stock * p.price) as total_value,
                    CASE 
                        WHEN p.stock <= 0 THEN 'نفد'
                        WHEN p.stock <= p.min_stock THEN 'منخفض'
                        WHEN p.stock <= p.min_stock * 2 THEN 'تحذير'
                        ELSE 'طبيعي'
                    END as status
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                ORDER BY p.stock ASC
            ''')
            
            self.report_data = cursor.fetchall()
            self.filtered_data = self.report_data.copy()
            
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)
            
            for row in self.report_data:
                # تلوين الصفوف حسب الحالة
                item = self.data_tree.insert('', tk.END, values=row)
                status = row[6]
                if status == 'نفد':
                    self.data_tree.set(item, 'status', '🔴 نفد')
                elif status == 'منخفض':
                    self.data_tree.set(item, 'status', '🟡 منخفض')
                elif status == 'تحذير':
                    self.data_tree.set(item, 'status', '🟠 تحذير')
                else:
                    self.data_tree.set(item, 'status', '🟢 طبيعي')
            
        except Exception as e:
            raise e
        finally:
            conn.close()
    
    def generate_customers_report(self, start_date, end_date):
        """إنشاء تقرير العملاء"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            columns = ('customer', 'phone', 'orders', 'total_spent', 'avg_order', 'last_order')
            self.data_tree['columns'] = columns
            
            self.data_tree.heading('customer', text='العميل')
            self.data_tree.heading('phone', text='الهاتف')
            self.data_tree.heading('orders', text='عدد الطلبات')
            self.data_tree.heading('total_spent', text='إجمالي الإنفاق')
            self.data_tree.heading('avg_order', text='متوسط الطلب')
            self.data_tree.heading('last_order', text='آخر طلب')
            
            cursor.execute('''
                SELECT 
                    c.name,
                    c.phone,
                    COUNT(s.id) as order_count,
                    COALESCE(SUM(s.total), 0) as total_spent,
                    COALESCE(AVG(s.total), 0) as avg_order,
                    MAX(DATE(s.sale_date)) as last_order
                FROM customers c
                LEFT JOIN sales s ON c.id = s.customer_id 
                    AND DATE(s.sale_date) BETWEEN ? AND ?
                GROUP BY c.id, c.name, c.phone
                ORDER BY total_spent DESC
            ''', (start_date, end_date))
            
            self.report_data = cursor.fetchall()
            self.filtered_data = self.report_data.copy()
            
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)
            
            for row in self.report_data:
                formatted_row = (
                    row[0], row[1], row[2], 
                    f"{row[3]:.2f}", f"{row[4]:.2f}", 
                    row[5] or "لا يوجد"
                )
                self.data_tree.insert('', tk.END, values=formatted_row)
            
        except Exception as e:
            raise e
        finally:
            conn.close()
    
    def generate_products_report(self, start_date, end_date):
        """إنشاء تقرير المنتجات"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            columns = ('product', 'category', 'sold_qty', 'revenue', 'stock', 'profit_margin')
            self.data_tree['columns'] = columns
            
            self.data_tree.heading('product', text='المنتج')
            self.data_tree.heading('category', text='الفئة')
            self.data_tree.heading('sold_qty', text='الكمية المباعة')
            self.data_tree.heading('revenue', text='الإيرادات')
            self.data_tree.heading('stock', text='المخزون')
            self.data_tree.heading('profit_margin', text='هامش الربح')
            
            cursor.execute('''
                SELECT 
                    p.name,
                    COALESCE(c.name, 'غير محدد') as category_name,
                    COALESCE(SUM(si.quantity), 0) as sold_quantity,
                    COALESCE(SUM(si.total), 0) as revenue,
                    p.stock,
                    'N/A' as profit_margin
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN sale_items si ON p.id = si.product_id
                LEFT JOIN sales s ON si.sale_id = s.id 
                    AND DATE(s.sale_date) BETWEEN ? AND ?
                GROUP BY p.id, p.name, c.name, p.stock
                ORDER BY sold_quantity DESC
            ''', (start_date, end_date))
            
            self.report_data = cursor.fetchall()
            self.filtered_data = self.report_data.copy()
            
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)
            
            for row in self.report_data:
                formatted_row = (
                    row[0], row[1], row[2], 
                    f"{row[3]:.2f}", row[4], row[5]
                )
                self.data_tree.insert('', tk.END, values=formatted_row)
            
        except Exception as e:
            raise e
        finally:
            conn.close()
    
    def generate_profit_report(self, start_date, end_date):
        """إنشاء تقرير الأرباح"""
        # تقرير بسيط للأرباح (يحتاج لبيانات التكلفة الفعلية)
        self.generate_sales_report(start_date, end_date)
    
    def update_quick_stats(self):
        """تحديث الإحصائيات السريعة"""
        if not self.filtered_data:
            self.total_records_var.set("0")
            self.total_amount_var.set("0.00")
            self.avg_amount_var.set("0.00")
            return
        
        record_count = len(self.filtered_data)
        self.total_records_var.set(f"{record_count:,}")
        
        # حساب الإجمالي والمتوسط حسب نوع التقرير
        report_type = self.report_type_var.get()
        
        if report_type in ["المبيعات", "المشتريات"]:
            # العمود الأخير هو الإجمالي
            total_amount = sum(float(row[6]) for row in self.filtered_data)
            avg_amount = total_amount / record_count if record_count > 0 else 0
        elif report_type == "المخزون":
            # العمود الخامس هو القيمة
            total_amount = sum(float(row[5]) for row in self.filtered_data)
            avg_amount = total_amount / record_count if record_count > 0 else 0
        elif report_type == "العملاء":
            # العمود الثالث هو إجمالي الإنفاق
            total_amount = sum(float(row[3]) for row in self.filtered_data)
            avg_amount = total_amount / record_count if record_count > 0 else 0
        else:
            total_amount = 0
            avg_amount = 0
        
        self.total_amount_var.set(f"{total_amount:,.2f}")
        self.avg_amount_var.set(f"{avg_amount:.2f}")
    
    def on_search_change(self, event=None):
        """عند تغيير نص البحث"""
        search_term = self.search_var.get().lower()
        
        if not search_term:
            self.filtered_data = self.report_data.copy()
        else:
            self.filtered_data = [
                row for row in self.report_data
                if any(search_term in str(cell).lower() for cell in row)
            ]
        
        # تحديث الجدول
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        
        for row in self.filtered_data:
            self.data_tree.insert('', tk.END, values=row)
        
        self.update_quick_stats()
    
    def clear_search(self):
        """مسح البحث"""
        self.search_var.set("")
        self.on_search_change()
    
    def refresh_report(self):
        """تحديث التقرير"""
        self.generate_report()
    
    def export_report(self):
        """تصدير التقرير"""
        if not self.filtered_data:
            messagebox.showwarning("تحذير", "لا توجد بيانات للتصدير")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.export_to_csv(file_path)
                elif file_path.endswith('.xlsx'):
                    self.export_to_excel(file_path)
                else:
                    self.export_to_csv(file_path)
                
                messagebox.showinfo("نجح", f"تم تصدير التقرير إلى:\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل في تصدير التقرير: {e}")
    
    def export_to_csv(self, file_path):
        """تصدير إلى CSV"""
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # كتابة العناوين
            headers = [self.data_tree.heading(col)['text'] for col in self.data_tree['columns']]
            writer.writerow(headers)
            
            # كتابة البيانات
            for row in self.filtered_data:
                writer.writerow(row)
    
    def export_to_excel(self, file_path):
        """تصدير إلى Excel"""
        try:
            import openpyxl
            from openpyxl import Workbook
            
            wb = Workbook()
            ws = wb.active
            ws.title = self.report_type_var.get()
            
            # كتابة العناوين
            headers = [self.data_tree.heading(col)['text'] for col in self.data_tree['columns']]
            for col, header in enumerate(headers, 1):
                ws.cell(row=1, column=col, value=header)
            
            # كتابة البيانات
            for row_idx, row_data in enumerate(self.filtered_data, 2):
                for col_idx, cell_data in enumerate(row_data, 1):
                    ws.cell(row=row_idx, column=col_idx, value=cell_data)
            
            wb.save(file_path)
            
        except ImportError:
            messagebox.showerror("خطأ", "مكتبة openpyxl غير مثبتة\nاستخدم: pip install openpyxl")
    
    def print_report(self):
        """طباعة التقرير"""
        messagebox.showinfo("طباعة", "ميزة الطباعة قيد التطوير")
    
    def generate_ai_analysis(self):
        """إنشاء تحليل ذكي"""
        self.notebook.select(2)  # التبديل لتبويب التحليل الذكي
        self.analyze_trends()
    
    # دوال التحليل الذكي
    def analyze_trends(self):
        """تحليل الاتجاهات"""
        def analyze():
            try:
                self.analysis_text.delete(1.0, tk.END)
                self.analysis_text.insert(tk.END, "🔍 جاري تحليل الاتجاهات...\n\n")
                
                patterns = self.ai_analytics.analyze_sales_patterns()
                
                self.analysis_text.insert(tk.END, "📈 تحليل الاتجاهات\n")
                self.analysis_text.insert(tk.END, "=" * 50 + "\n\n")
                
                if patterns.get('daily_trends'):
                    daily = patterns['daily_trends']
                    self.analysis_text.insert(tk.END, "📅 الاتجاهات اليومية:\n")
                    self.analysis_text.insert(tk.END, f"• الاتجاه العام: {daily.get('trend', 'غير محدد')}\n")
                    self.analysis_text.insert(tk.END, f"• معدل النمو: {daily.get('growth_rate', 0):.1f}%\n")
                    self.analysis_text.insert(tk.END, f"• متوسط المبيعات اليومية: {daily.get('average_daily_sales', 0):.2f} ر.س\n\n")
                
                if patterns.get('weekly_trends'):
                    weekly = patterns['weekly_trends']
                    self.analysis_text.insert(tk.END, "📊 الاتجاهات الأسبوعية:\n")
                    self.analysis_text.insert(tk.END, f"• أفضل يوم: {weekly.get('best_day', 'غير محدد')}\n")
                    self.analysis_text.insert(tk.END, f"• أسوأ يوم: {weekly.get('worst_day', 'غير محدد')}\n\n")
                
                if patterns.get('hourly_trends'):
                    hourly = patterns['hourly_trends']
                    self.analysis_text.insert(tk.END, "🕐 الاتجاهات بالساعة:\n")
                    self.analysis_text.insert(tk.END, f"• ذروة المبيعات: {hourly.get('peak_hour', 'غير محدد')}:00\n")
                    self.analysis_text.insert(tk.END, f"• أقل المبيعات: {hourly.get('low_hour', 'غير محدد')}:00\n\n")
                
            except Exception as e:
                self.analysis_text.insert(tk.END, f"❌ خطأ في التحليل: {e}")
        
        threading.Thread(target=analyze, daemon=True).start()
    
    def detect_patterns(self):
        """كشف الأنماط"""
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(tk.END, "🔍 كشف الأنماط قيد التطوير...")
    
    def predict_sales(self):
        """توقعات المبيعات"""
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(tk.END, "🔮 توقعات المبيعات قيد التطوير...")
    
    def generate_business_insights(self):
        """رؤى تجارية"""
        def generate():
            try:
                self.analysis_text.delete(1.0, tk.END)
                self.analysis_text.insert(tk.END, "💡 جاري توليد الرؤى التجارية...\n\n")
                
                insights = self.ai_analytics.generate_business_insights()
                
                self.analysis_text.insert(tk.END, "💡 الرؤى التجارية\n")
                self.analysis_text.insert(tk.END, "=" * 50 + "\n\n")
                
                for i, insight in enumerate(insights, 1):
                    self.analysis_text.insert(tk.END, f"{i}. [{insight['type']}] {insight['title']}\n")
                    self.analysis_text.insert(tk.END, f"   {insight['message']}\n")
                    self.analysis_text.insert(tk.END, f"   الإجراء المقترح: {insight['action']}\n")
                    self.analysis_text.insert(tk.END, f"   الأولوية: {insight['priority']}\n\n")
                
                if not insights:
                    self.analysis_text.insert(tk.END, "لا توجد رؤى متاحة حالياً")
                
            except Exception as e:
                self.analysis_text.insert(tk.END, f"❌ خطأ في توليد الرؤى: {e}")
        
        threading.Thread(target=generate, daemon=True).start()
    
    # دوال التوصيات
    def generate_product_recommendations(self):
        """توصيات المنتجات"""
        self.recommendations_text.delete(1.0, tk.END)
        self.recommendations_text.insert(tk.END, "🛒 توصيات المنتجات قيد التطوير...")
    
    def generate_customer_recommendations(self):
        """توصيات العملاء"""
        self.recommendations_text.delete(1.0, tk.END)
        self.recommendations_text.insert(tk.END, "👥 توصيات العملاء قيد التطوير...")
    
    def generate_pricing_recommendations(self):
        """توصيات التسعير"""
        self.recommendations_text.delete(1.0, tk.END)
        self.recommendations_text.insert(tk.END, "💰 توصيات التسعير قيد التطوير...")
    
    def generate_inventory_recommendations(self):
        """توصيات المخزون"""
        self.recommendations_text.delete(1.0, tk.END)
        self.recommendations_text.insert(tk.END, "📦 توصيات المخزون قيد التطوير...")
    
    def generate_chart(self):
        """إنشاء رسم بياني"""
        if not self.filtered_data:
            messagebox.showwarning("تحذير", "لا توجد بيانات للرسم")
            return
        
        chart_type = self.chart_type_var.get()
        
        self.chart_text.delete(1.0, tk.END)
        self.chart_text.insert(tk.END, f"📊 الرسم البياني ({chart_type})\n")
        self.chart_text.insert(tk.END, "=" * 40 + "\n\n")
        
        # رسم بياني بسيط نصي
        if self.report_type_var.get() == "المبيعات":
            self.create_sales_chart()
        else:
            self.chart_text.insert(tk.END, "الرسم البياني متاح للمبيعات فقط حالياً")
    
    def create_sales_chart(self):
        """إنشاء رسم بياني للمبيعات"""
        # تجميع البيانات حسب التاريخ
        daily_sales = {}
        for row in self.filtered_data:
            date = row[0]
            amount = float(row[6])
            daily_sales[date] = daily_sales.get(date, 0) + amount
        
        if not daily_sales:
            self.chart_text.insert(tk.END, "لا توجد بيانات للرسم")
            return
        
        # رسم بياني بسيط
        max_sales = max(daily_sales.values())
        
        for date, sales in sorted(daily_sales.items()):
            bar_length = int((sales / max_sales) * 30) if max_sales > 0 else 0
            bar = "█" * bar_length
            self.chart_text.insert(tk.END, f"{date}: {bar} {sales:,.0f} ر.س\n")
    
    def update_time(self):
        """تحديث الوقت"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_var.set(current_time)
        self.window.after(1000, self.update_time)