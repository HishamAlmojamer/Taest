#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
لوحة التحكم الذكية المحسنة
تصميم: المهندس هشام المجمر - 773988932
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
from datetime import datetime, timedelta
import threading
import time
import json
from ai_analytics import AIAnalyticsEngine, SmartRecommendationSystem

class EnhancedDashboard:
    """لوحة التحكم الذكية المحسنة"""
    
    def __init__(self, parent, db, user):
        self.parent = parent
        self.db = db
        self.user = user
        
        # محركات الذكاء الاصطناعي
        self.ai_analytics = AIAnalyticsEngine(db.db_path)
        self.recommendation_system = SmartRecommendationSystem(db.db_path)
        
        # إنشاء النافذة
        self.window = tk.Toplevel(parent)
        self.window.title("🎛️ لوحة التحكم الذكية - المطور: هشام المجمر 773988932")
        self.window.geometry("1400x800")
        self.window.state('zoomed')
        self.window.grab_set()
        
        # الألوان والخطوط
        self.setup_styles()
        
        # المتغيرات
        self.setup_variables()
        
        # إنشاء الواجهة
        self.create_widgets()
        
        # تحميل البيانات
        self.load_dashboard_data()
        
        # بدء التحديث التلقائي
        self.start_auto_refresh()
    
    def setup_styles(self):
        """إعداد الألوان والخطوط"""
        self.colors = {
            'primary': '#2196F3',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'danger': '#F44336',
            'info': '#00BCD4',
            'light': '#F5F5F5',
            'dark': '#333333',
            'purple': '#9C27B0',
            'teal': '#009688'
        }
        
        self.fonts = {
            'title': font.Font(family="Arial", size=18, weight="bold"),
            'subtitle': font.Font(family="Arial", size=14, weight="bold"),
            'normal': font.Font(family="Arial", size=11),
            'small': font.Font(family="Arial", size=9),
            'large': font.Font(family="Arial", size=24, weight="bold")
        }
    
    def setup_variables(self):
        """إعداد المتغيرات"""
        # متغيرات الإحصائيات
        self.total_sales_var = tk.StringVar(value="0.00")
        self.total_orders_var = tk.StringVar(value="0")
        self.total_customers_var = tk.StringVar(value="0")
        self.total_products_var = tk.StringVar(value="0")
        
        # متغيرات التحليلات
        self.growth_rate_var = tk.StringVar(value="0%")
        self.avg_order_var = tk.StringVar(value="0.00")
        self.top_product_var = tk.StringVar(value="غير محدد")
        self.low_stock_count_var = tk.StringVar(value="0")
        
        # متغيرات الوقت
        self.last_update_var = tk.StringVar()
        self.current_time_var = tk.StringVar()
        
        # بيانات الرسوم البيانية
        self.sales_chart_data = []
        self.products_chart_data = []
        self.insights_data = []
    
    def create_widgets(self):
        """إنشاء عناصر الواجهة"""
        # الإطار الرئيسي
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # شريط العنوان
        self.create_header(main_frame)
        
        # الإطار الأوسط
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # الصف الأول - بطاقات الإحصائيات
        self.create_stats_cards(content_frame)
        
        # الصف الثاني - الرسوم البيانية والتحليلات
        charts_frame = ttk.Frame(content_frame)
        charts_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # الجانب الأيسر - الرسوم البيانية
        self.create_charts_panel(charts_frame)
        
        # الجانب الأيمن - الرؤى الذكية والتوصيات
        self.create_insights_panel(charts_frame)
        
        # شريط الحالة
        self.create_status_bar(main_frame)
    
    def create_header(self, parent):
        """إنشاء شريط العنوان"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # العنوان الرئيسي
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT)
        
        title_label = ttk.Label(title_frame, text="🎛️ لوحة التحكم الذكية", 
                               font=self.fonts['title'])
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(title_frame, 
                                  text=f"مرحباً {self.user['full_name']} | آخر تحديث: جاري التحميل...", 
                                  font=self.fonts['small'])
        subtitle_label.pack(anchor=tk.W)
        
        # أزرار التحكم
        controls_frame = ttk.Frame(header_frame)
        controls_frame.pack(side=tk.RIGHT)
        
        ttk.Button(controls_frame, text="🔄 تحديث", 
                  command=self.refresh_dashboard).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(controls_frame, text="📊 تقرير مفصل", 
                  command=self.generate_detailed_report).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(controls_frame, text="🤖 رؤى ذكية", 
                  command=self.show_ai_insights).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(controls_frame, text="⚙️ إعدادات", 
                  command=self.show_settings).pack(side=tk.LEFT, padx=2)
    
    def create_stats_cards(self, parent):
        """إنشاء بطاقات الإحصائيات"""
        stats_frame = ttk.Frame(parent)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        # بطاقة إجمالي المبيعات
        self.create_stat_card(stats_frame, "💰", "إجمالي المبيعات", 
                             self.total_sales_var, "ر.س", self.colors['success'])
        
        # بطاقة عدد الطلبات
        self.create_stat_card(stats_frame, "📦", "عدد الطلبات", 
                             self.total_orders_var, "طلب", self.colors['info'])
        
        # بطاقة عدد العملاء
        self.create_stat_card(stats_frame, "👥", "عدد العملاء", 
                             self.total_customers_var, "عميل", self.colors['purple'])
        
        # بطاقة عدد المنتجات
        self.create_stat_card(stats_frame, "🏷️", "عدد المنتجات", 
                             self.total_products_var, "منتج", self.colors['teal'])
        
        # بطاقة معدل النمو
        self.create_stat_card(stats_frame, "📈", "معدل النمو", 
                             self.growth_rate_var, "", self.colors['warning'])
        
        # بطاقة متوسط الطلب
        self.create_stat_card(stats_frame, "💳", "متوسط الطلب", 
                             self.avg_order_var, "ر.س", self.colors['primary'])
    
    def create_stat_card(self, parent, icon, title, value_var, unit, color):
        """إنشاء بطاقة إحصائية واحدة"""
        card_frame = ttk.LabelFrame(parent, text="", padding="15")
        card_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # الأيقونة
        icon_label = ttk.Label(card_frame, text=icon, font=self.fonts['large'])
        icon_label.pack()
        
        # العنوان
        title_label = ttk.Label(card_frame, text=title, font=self.fonts['small'])
        title_label.pack(pady=(5, 0))
        
        # القيمة
        value_frame = ttk.Frame(card_frame)
        value_frame.pack(pady=(5, 0))
        
        value_label = ttk.Label(value_frame, textvariable=value_var, 
                               font=self.fonts['subtitle'])
        value_label.pack(side=tk.LEFT)
        
        if unit:
            unit_label = ttk.Label(value_frame, text=unit, font=self.fonts['small'])
            unit_label.pack(side=tk.LEFT, padx=(5, 0))
    
    def create_charts_panel(self, parent):
        """إنشاء لوحة الرسوم البيانية"""
        charts_frame = ttk.Frame(parent)
        charts_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # تبويبات الرسوم البيانية
        notebook = ttk.Notebook(charts_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # تبويب المبيعات
        sales_frame = ttk.Frame(notebook)
        notebook.add(sales_frame, text="📈 المبيعات")
        self.create_sales_chart(sales_frame)
        
        # تبويب المنتجات
        products_frame = ttk.Frame(notebook)
        notebook.add(products_frame, text="🏷️ المنتجات")
        self.create_products_chart(products_frame)
        
        # تبويب العملاء
        customers_frame = ttk.Frame(notebook)
        notebook.add(customers_frame, text="👥 العملاء")
        self.create_customers_chart(customers_frame)
        
        # تبويب التوقعات
        predictions_frame = ttk.Frame(notebook)
        notebook.add(predictions_frame, text="🔮 التوقعات")
        self.create_predictions_chart(predictions_frame)
    
    def create_sales_chart(self, parent):
        """إنشاء رسم بياني للمبيعات"""
        chart_frame = ttk.LabelFrame(parent, text="📈 اتجاه المبيعات (آخر 30 يوم)", padding="10")
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # رسم بياني بسيط باستخدام النصوص
        self.sales_chart_text = tk.Text(chart_frame, height=15, font=self.fonts['small'])
        self.sales_chart_text.pack(fill=tk.BOTH, expand=True)
        
        # شريط تمرير
        sales_scrollbar = ttk.Scrollbar(chart_frame, orient=tk.VERTICAL, 
                                       command=self.sales_chart_text.yview)
        self.sales_chart_text.configure(yscrollcommand=sales_scrollbar.set)
        sales_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_products_chart(self, parent):
        """إنشاء رسم بياني للمنتجات"""
        chart_frame = ttk.LabelFrame(parent, text="🏷️ أفضل المنتجات مبيعاً", padding="10")
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # جدول المنتجات الأكثر مبيعاً
        columns = ('rank', 'product', 'sales', 'revenue')
        self.products_tree = ttk.Treeview(chart_frame, columns=columns, show='headings', height=12)
        
        self.products_tree.heading('rank', text='الترتيب')
        self.products_tree.heading('product', text='المنتج')
        self.products_tree.heading('sales', text='المبيعات')
        self.products_tree.heading('revenue', text='الإيرادات')
        
        self.products_tree.column('rank', width=80, anchor=tk.CENTER)
        self.products_tree.column('product', width=200)
        self.products_tree.column('sales', width=100, anchor=tk.CENTER)
        self.products_tree.column('revenue', width=120, anchor=tk.CENTER)
        
        self.products_tree.pack(fill=tk.BOTH, expand=True)
        
        # شريط تمرير
        products_scrollbar = ttk.Scrollbar(chart_frame, orient=tk.VERTICAL, 
                                         command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=products_scrollbar.set)
        products_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_customers_chart(self, parent):
        """إنشاء رسم بياني للعملاء"""
        chart_frame = ttk.LabelFrame(parent, text="👥 تحليل العملاء", padding="10")
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # إحصائيات العملاء
        stats_frame = ttk.Frame(chart_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        # عملاء جدد
        new_customers_frame = ttk.LabelFrame(stats_frame, text="عملاء جدد (هذا الشهر)", padding="10")
        new_customers_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.new_customers_var = tk.StringVar(value="0")
        ttk.Label(new_customers_frame, textvariable=self.new_customers_var, 
                 font=self.fonts['large']).pack()
        
        # عملاء نشطون
        active_customers_frame = ttk.LabelFrame(stats_frame, text="عملاء نشطون", padding="10")
        active_customers_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.active_customers_var = tk.StringVar(value="0")
        ttk.Label(active_customers_frame, textvariable=self.active_customers_var, 
                 font=self.fonts['large']).pack()
        
        # أفضل العملاء
        top_customers_frame = ttk.LabelFrame(chart_frame, text="🏆 أفضل العملاء", padding="5")
        top_customers_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('rank', 'customer', 'orders', 'total')
        self.customers_tree = ttk.Treeview(top_customers_frame, columns=columns, show='headings', height=10)
        
        self.customers_tree.heading('rank', text='الترتيب')
        self.customers_tree.heading('customer', text='العميل')
        self.customers_tree.heading('orders', text='الطلبات')
        self.customers_tree.heading('total', text='الإجمالي')
        
        self.customers_tree.column('rank', width=80, anchor=tk.CENTER)
        self.customers_tree.column('customer', width=200)
        self.customers_tree.column('orders', width=100, anchor=tk.CENTER)
        self.customers_tree.column('total', width=120, anchor=tk.CENTER)
        
        self.customers_tree.pack(fill=tk.BOTH, expand=True)
    
    def create_predictions_chart(self, parent):
        """إنشاء رسم بياني للتوقعات"""
        chart_frame = ttk.LabelFrame(parent, text="🔮 التوقعات الذكية", padding="10")
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # تبويبات التوقعات
        predictions_notebook = ttk.Notebook(chart_frame)
        predictions_notebook.pack(fill=tk.BOTH, expand=True)
        
        # توقعات المبيعات
        sales_pred_frame = ttk.Frame(predictions_notebook)
        predictions_notebook.add(sales_pred_frame, text="المبيعات")
        
        self.sales_prediction_text = tk.Text(sales_pred_frame, height=10, font=self.fonts['small'])
        self.sales_prediction_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # توقعات المخزون
        stock_pred_frame = ttk.Frame(predictions_notebook)
        predictions_notebook.add(stock_pred_frame, text="المخزون")
        
        self.stock_prediction_text = tk.Text(stock_pred_frame, height=10, font=self.fonts['small'])
        self.stock_prediction_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_insights_panel(self, parent):
        """إنشاء لوحة الرؤى الذكية"""
        insights_frame = ttk.Frame(parent)
        insights_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        insights_frame.configure(width=400)
        
        # الرؤى الذكية
        ai_insights_frame = ttk.LabelFrame(insights_frame, text="🤖 الرؤى الذكية", padding="10")
        ai_insights_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # قائمة الرؤى
        self.insights_listbox = tk.Listbox(ai_insights_frame, height=8, font=self.fonts['small'])
        self.insights_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # زر تحديث الرؤى
        ttk.Button(ai_insights_frame, text="🔄 تحديث الرؤى", 
                  command=self.update_ai_insights).pack(fill=tk.X)
        
        # التنبيهات والتحذيرات
        alerts_frame = ttk.LabelFrame(insights_frame, text="⚠️ التنبيهات", padding="10")
        alerts_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.alerts_listbox = tk.Listbox(alerts_frame, height=6, font=self.fonts['small'])
        self.alerts_listbox.pack(fill=tk.BOTH, expand=True)
        
        # الإجراءات السريعة
        actions_frame = ttk.LabelFrame(insights_frame, text="⚡ إجراءات سريعة", padding="10")
        actions_frame.pack(fill=tk.X)
        
        ttk.Button(actions_frame, text="📦 إنشاء أمر شراء", 
                  command=self.create_purchase_order).pack(fill=tk.X, pady=2)
        
        ttk.Button(actions_frame, text="🎯 حملة تسويقية", 
                  command=self.create_marketing_campaign).pack(fill=tk.X, pady=2)
        
        ttk.Button(actions_frame, text="📊 تقرير مخصص", 
                  command=self.create_custom_report).pack(fill=tk.X, pady=2)
    
    def create_status_bar(self, parent):
        """إنشاء شريط الحالة"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        # معلومات الحالة
        self.status_var = tk.StringVar(value="جاري تحميل البيانات...")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)
        
        # معلومات إضافية
        info_frame = ttk.Frame(status_frame)
        info_frame.pack(side=tk.RIGHT)
        
        # آخر تحديث
        ttk.Label(info_frame, text="آخر تحديث:").pack(side=tk.LEFT)
        ttk.Label(info_frame, textvariable=self.last_update_var).pack(side=tk.LEFT, padx=(5, 15))
        
        # الوقت الحالي
        ttk.Label(info_frame, textvariable=self.current_time_var).pack(side=tk.LEFT)
        
        # تحديث الوقت
        self.update_time()
    
    def load_dashboard_data(self):
        """تحميل بيانات لوحة التحكم"""
        def load_data():
            try:
                self.status_var.set("جاري تحميل الإحصائيات...")
                self.load_statistics()
                
                self.status_var.set("جاري تحميل الرسوم البيانية...")
                self.load_charts_data()
                
                self.status_var.set("جاري تحليل البيانات...")
                self.load_ai_insights()
                
                self.status_var.set("جاري تحميل التنبيهات...")
                self.load_alerts()
                
                self.last_update_var.set(datetime.now().strftime("%H:%M:%S"))
                self.status_var.set("تم تحميل البيانات بنجاح")
                
            except Exception as e:
                self.status_var.set(f"خطأ في تحميل البيانات: {e}")
        
        # تشغيل التحميل في خيط منفصل
        threading.Thread(target=load_data, daemon=True).start()
    
    def load_statistics(self):
        """تحميل الإحصائيات الأساسية"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # إجمالي المبيعات
            cursor.execute('''
                SELECT COALESCE(SUM(total), 0), COUNT(*)
                FROM sales
                WHERE DATE(sale_date) >= DATE('now', '-30 days')
            ''')
            total_sales, total_orders = cursor.fetchone()
            
            self.total_sales_var.set(f"{total_sales:,.2f}")
            self.total_orders_var.set(f"{total_orders:,}")
            
            # عدد العملاء
            cursor.execute('SELECT COUNT(*) FROM customers')
            total_customers = cursor.fetchone()[0]
            self.total_customers_var.set(f"{total_customers:,}")
            
            # عدد المنتجات
            cursor.execute('SELECT COUNT(*) FROM products WHERE stock > 0')
            total_products = cursor.fetchone()[0]
            self.total_products_var.set(f"{total_products:,}")
            
            # معدل النمو
            cursor.execute('''
                SELECT COALESCE(SUM(total), 0)
                FROM sales
                WHERE DATE(sale_date) >= DATE('now', '-60 days')
                AND DATE(sale_date) < DATE('now', '-30 days')
            ''')
            previous_month_sales = cursor.fetchone()[0]
            
            if previous_month_sales > 0:
                growth_rate = ((total_sales - previous_month_sales) / previous_month_sales) * 100
                self.growth_rate_var.set(f"{growth_rate:+.1f}%")
            else:
                self.growth_rate_var.set("N/A")
            
            # متوسط الطلب
            if total_orders > 0:
                avg_order = total_sales / total_orders
                self.avg_order_var.set(f"{avg_order:.2f}")
            else:
                self.avg_order_var.set("0.00")
            
            # عدد المنتجات منخفضة المخزون
            cursor.execute('SELECT COUNT(*) FROM products WHERE stock <= min_stock')
            low_stock_count = cursor.fetchone()[0]
            self.low_stock_count_var.set(f"{low_stock_count}")
            
        except Exception as e:
            print(f"خطأ في تحميل الإحصائيات: {e}")
        finally:
            conn.close()
    
    def load_charts_data(self):
        """تحميل بيانات الرسوم البيانية"""
        self.load_sales_chart_data()
        self.load_products_chart_data()
        self.load_customers_chart_data()
        self.load_predictions_data()
    
    def load_sales_chart_data(self):
        """تحميل بيانات رسم المبيعات"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT DATE(sale_date) as sale_date, SUM(total) as daily_total
                FROM sales
                WHERE DATE(sale_date) >= DATE('now', '-30 days')
                GROUP BY DATE(sale_date)
                ORDER BY sale_date
            ''')
            
            sales_data = cursor.fetchall()
            
            # تحديث الرسم البياني النصي
            self.sales_chart_text.delete(1.0, tk.END)
            self.sales_chart_text.insert(tk.END, "📈 اتجاه المبيعات اليومية (آخر 30 يوم)\n")
            self.sales_chart_text.insert(tk.END, "=" * 50 + "\n\n")
            
            if sales_data:
                max_sales = max(row[1] for row in sales_data)
                
                for date, total in sales_data:
                    # رسم شريط بسيط
                    bar_length = int((total / max_sales) * 30) if max_sales > 0 else 0
                    bar = "█" * bar_length
                    
                    self.sales_chart_text.insert(tk.END, 
                        f"{date}: {bar} {total:,.0f} ر.س\n")
            else:
                self.sales_chart_text.insert(tk.END, "لا توجد بيانات مبيعات للفترة المحددة")
            
        except Exception as e:
            self.sales_chart_text.delete(1.0, tk.END)
            self.sales_chart_text.insert(tk.END, f"خطأ في تحميل بيانات المبيعات: {e}")
        finally:
            conn.close()
    
    def load_products_chart_data(self):
        """تحميل بيانات رسم المنتجات"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT p.name, SUM(si.quantity) as total_qty, SUM(si.total) as total_revenue
                FROM products p
                JOIN sale_items si ON p.id = si.product_id
                JOIN sales s ON si.sale_id = s.id
                WHERE DATE(s.sale_date) >= DATE('now', '-30 days')
                GROUP BY p.id, p.name
                ORDER BY total_qty DESC
                LIMIT 10
            ''')
            
            products_data = cursor.fetchall()
            
            # مسح البيانات الحالية
            for item in self.products_tree.get_children():
                self.products_tree.delete(item)
            
            # إضافة البيانات الجديدة
            for i, (name, qty, revenue) in enumerate(products_data, 1):
                self.products_tree.insert('', tk.END, values=(
                    i, name, f"{qty:,}", f"{revenue:,.2f} ر.س"
                ))
            
        except Exception as e:
            print(f"خطأ في تحميل بيانات المنتجات: {e}")
        finally:
            conn.close()
    
    def load_customers_chart_data(self):
        """تحميل بيانات رسم العملاء"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # عملاء جدد هذا الشهر
            cursor.execute('''
                SELECT COUNT(*)
                FROM customers
                WHERE DATE(created_at) >= DATE('now', 'start of month')
            ''')
            new_customers = cursor.fetchone()[0] or 0
            self.new_customers_var.set(str(new_customers))
            
            # عملاء نشطون (لديهم مشتريات في آخر 30 يوم)
            cursor.execute('''
                SELECT COUNT(DISTINCT customer_id)
                FROM sales
                WHERE DATE(sale_date) >= DATE('now', '-30 days')
            ''')
            active_customers = cursor.fetchone()[0] or 0
            self.active_customers_var.set(str(active_customers))
            
            # أفضل العملاء
            cursor.execute('''
                SELECT c.name, COUNT(s.id) as order_count, SUM(s.total) as total_spent
                FROM customers c
                JOIN sales s ON c.id = s.customer_id
                WHERE DATE(s.sale_date) >= DATE('now', '-30 days')
                GROUP BY c.id, c.name
                ORDER BY total_spent DESC
                LIMIT 10
            ''')
            
            top_customers = cursor.fetchall()
            
            # مسح البيانات الحالية
            for item in self.customers_tree.get_children():
                self.customers_tree.delete(item)
            
            # إضافة البيانات الجديدة
            for i, (name, orders, total) in enumerate(top_customers, 1):
                self.customers_tree.insert('', tk.END, values=(
                    i, name, f"{orders:,}", f"{total:,.2f} ر.س"
                ))
            
        except Exception as e:
            print(f"خطأ في تحميل بيانات العملاء: {e}")
        finally:
            conn.close()
    
    def load_predictions_data(self):
        """تحميل بيانات التوقعات"""
        try:
            # تحليل أنماط المبيعات
            patterns = self.ai_analytics.analyze_sales_patterns()
            
            # توقعات المبيعات
            self.sales_prediction_text.delete(1.0, tk.END)
            self.sales_prediction_text.insert(tk.END, "🔮 توقعات المبيعات\n")
            self.sales_prediction_text.insert(tk.END, "=" * 30 + "\n\n")
            
            if patterns.get('daily_trends'):
                daily = patterns['daily_trends']
                self.sales_prediction_text.insert(tk.END, f"الاتجاه العام: {daily.get('trend', 'غير محدد')}\n")
                self.sales_prediction_text.insert(tk.END, f"معدل النمو: {daily.get('growth_rate', 0):.1f}%\n")
                self.sales_prediction_text.insert(tk.END, f"متوسط المبيعات اليومية: {daily.get('average_daily_sales', 0):.2f} ر.س\n\n")
            
            if patterns.get('hourly_trends'):
                hourly = patterns['hourly_trends']
                self.sales_prediction_text.insert(tk.END, f"أفضل ساعة للمبيعات: {hourly.get('peak_hour', 'غير محدد')}:00\n")
                self.sales_prediction_text.insert(tk.END, f"أقل ساعة للمبيعات: {hourly.get('low_hour', 'غير محدد')}:00\n\n")
            
            if patterns.get('weekly_trends'):
                weekly = patterns['weekly_trends']
                self.sales_prediction_text.insert(tk.END, f"أفضل يوم: {weekly.get('best_day', 'غير محدد')}\n")
                self.sales_prediction_text.insert(tk.END, f"أسوأ يوم: {weekly.get('worst_day', 'غير محدد')}\n")
            
            # توقعات المخزون
            self.stock_prediction_text.delete(1.0, tk.END)
            self.stock_prediction_text.insert(tk.END, "📦 توقعات المخزون\n")
            self.stock_prediction_text.insert(tk.END, "=" * 30 + "\n\n")
            
            # جلب بعض المنتجات للتوقع
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, stock
                FROM products
                WHERE stock > 0
                ORDER BY stock ASC
                LIMIT 5
            ''')
            
            products = cursor.fetchall()
            
            for product_id, name, current_stock in products:
                prediction = self.ai_analytics.predict_demand(product_id, 7)
                predicted_demand = prediction.get('predicted_demand', 0)
                confidence = prediction.get('confidence_level', 'منخفض')
                
                self.stock_prediction_text.insert(tk.END, 
                    f"المنتج: {name}\n"
                    f"المخزون الحالي: {current_stock}\n"
                    f"الطلب المتوقع (7 أيام): {predicted_demand}\n"
                    f"مستوى الثقة: {confidence}\n\n")
            
            conn.close()
            
        except Exception as e:
            print(f"خطأ في تحميل التوقعات: {e}")
    
    def load_ai_insights(self):
        """تحميل الرؤى الذكية"""
        try:
            insights = self.ai_analytics.generate_business_insights()
            
            self.insights_listbox.delete(0, tk.END)
            
            for insight in insights:
                insight_text = f"[{insight['type']}] {insight['title']}: {insight['message']}"
                self.insights_listbox.insert(tk.END, insight_text)
            
            if not insights:
                self.insights_listbox.insert(tk.END, "لا توجد رؤى متاحة حالياً")
            
        except Exception as e:
            self.insights_listbox.delete(0, tk.END)
            self.insights_listbox.insert(tk.END, f"خطأ في تحميل الرؤى: {e}")
    
    def load_alerts(self):
        """تحميل التنبيهات"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            self.alerts_listbox.delete(0, tk.END)
            
            # تنبيهات المخزون المنخفض
            cursor.execute('''
                SELECT name, stock, min_stock
                FROM products
                WHERE stock <= min_stock
                ORDER BY (stock - min_stock) ASC
                LIMIT 5
            ''')
            
            low_stock_products = cursor.fetchall()
            
            for name, stock, min_stock in low_stock_products:
                self.alerts_listbox.insert(tk.END, f"⚠️ مخزون منخفض: {name} ({stock}/{min_stock})")
            
            # تنبيهات المنتجات منتهية الصلاحية (إذا كان هناك تاريخ انتهاء)
            # يمكن إضافة المزيد من التنبيهات هنا
            
            if not low_stock_products:
                self.alerts_listbox.insert(tk.END, "✅ لا توجد تنبيهات")
            
        except Exception as e:
            self.alerts_listbox.delete(0, tk.END)
            self.alerts_listbox.insert(tk.END, f"خطأ في تحميل التنبيهات: {e}")
        finally:
            conn.close()
    
    def refresh_dashboard(self):
        """تحديث لوحة التحكم"""
        self.load_dashboard_data()
    
    def update_ai_insights(self):
        """تحديث الرؤى الذكية"""
        self.load_ai_insights()
    
    def start_auto_refresh(self):
        """بدء التحديث التلقائي"""
        def auto_refresh():
            while True:
                time.sleep(300)  # تحديث كل 5 دقائق
                try:
                    self.window.after(0, self.refresh_dashboard)
                except:
                    break
        
        thread = threading.Thread(target=auto_refresh, daemon=True)
        thread.start()
    
    def update_time(self):
        """تحديث الوقت"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.current_time_var.set(current_time)
        self.window.after(1000, self.update_time)
    
    # دوال الإجراءات
    def generate_detailed_report(self):
        """إنشاء تقرير مفصل"""
        messagebox.showinfo("تقرير مفصل", "ميزة التقرير المفصل قيد التطوير")
    
    def show_ai_insights(self):
        """عرض الرؤى الذكية"""
        messagebox.showinfo("رؤى ذكية", "ميزة الرؤى الذكية المتقدمة قيد التطوير")
    
    def show_settings(self):
        """عرض الإعدادات"""
        messagebox.showinfo("إعدادات", "ميزة الإعدادات قيد التطوير")
    
    def create_purchase_order(self):
        """إنشاء أمر شراء"""
        messagebox.showinfo("أمر شراء", "ميزة إنشاء أمر الشراء التلقائي قيد التطوير")
    
    def create_marketing_campaign(self):
        """إنشاء حملة تسويقية"""
        messagebox.showinfo("حملة تسويقية", "ميزة الحملات التسويقية قيد التطوير")
    
    def create_custom_report(self):
        """إنشاء تقرير مخصص"""
        messagebox.showinfo("تقرير مخصص", "ميزة التقارير المخصصة قيد التطوير")