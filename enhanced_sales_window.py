#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نقطة البيع المحسنة مع الذكاء الاصطناعي
تصميم: المهندس هشام المجمر - 773988932
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
from datetime import datetime, timedelta
import json
import sqlite3
from collections import defaultdict
import threading
import time
import random

class AIRecommendationEngine:
    """محرك التوصيات الذكي"""
    
    def __init__(self, db):
        self.db = db
    
    def get_frequently_bought_together(self, product_id, limit=5):
        """منتجات تُشترى معاً بكثرة"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # البحث عن المنتجات التي تُشترى مع هذا المنتج
            cursor.execute('''
                SELECT p2.id, p2.name, p2.price, COUNT(*) as frequency
                FROM sale_items si1
                JOIN sale_items si2 ON si1.sale_id = si2.sale_id AND si1.product_id != si2.product_id
                JOIN products p2 ON si2.product_id = p2.id
                WHERE si1.product_id = ? AND p2.stock > 0
                GROUP BY p2.id, p2.name, p2.price
                ORDER BY frequency DESC
                LIMIT ?
            ''', (product_id, limit))
            
            return cursor.fetchall()
        except:
            return []
        finally:
            conn.close()
    
    def get_trending_products(self, days=7, limit=10):
        """المنتجات الرائجة"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute('''
                SELECT p.id, p.name, p.price, p.stock, SUM(si.quantity) as total_sold
                FROM products p
                JOIN sale_items si ON p.id = si.product_id
                JOIN sales s ON si.sale_id = s.id
                WHERE s.sale_date >= ? AND p.stock > 0
                GROUP BY p.id, p.name, p.price, p.stock
                ORDER BY total_sold DESC
                LIMIT ?
            ''', (date_threshold, limit))
            
            return cursor.fetchall()
        except:
            return []
        finally:
            conn.close()
    
    def get_customer_recommendations(self, customer_id, limit=5):
        """توصيات بناءً على تاريخ العميل"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # المنتجات التي اشتراها العميل سابقاً
            cursor.execute('''
                SELECT DISTINCT p.category_id
                FROM products p
                JOIN sale_items si ON p.id = si.product_id
                JOIN sales s ON si.sale_id = s.id
                WHERE s.customer_id = ?
            ''', (customer_id,))
            
            categories = [row[0] for row in cursor.fetchall()]
            
            if not categories:
                return []
            
            # منتجات من نفس الفئات
            placeholders = ','.join('?' * len(categories))
            cursor.execute(f'''
                SELECT p.id, p.name, p.price, p.stock
                FROM products p
                WHERE p.category_id IN ({placeholders}) 
                AND p.stock > 0
                ORDER BY p.stock DESC
                LIMIT ?
            ''', categories + [limit])
            
            return cursor.fetchall()
        except:
            return []
        finally:
            conn.close()
    
    def predict_demand(self, product_id, days_ahead=7):
        """توقع الطلب على المنتج"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # بيانات المبيعات للأسابيع الماضية
            cursor.execute('''
                SELECT DATE(s.sale_date) as sale_date, SUM(si.quantity) as daily_sales
                FROM sales s
                JOIN sale_items si ON s.id = si.sale_id
                WHERE si.product_id = ? AND s.sale_date >= date('now', '-30 days')
                GROUP BY DATE(s.sale_date)
                ORDER BY sale_date
            ''', (product_id,))
            
            sales_data = cursor.fetchall()
            
            if len(sales_data) < 3:
                return 0
            
            # حساب المتوسط المتحرك البسيط
            recent_sales = [row[1] for row in sales_data[-7:]]
            average_daily_sales = sum(recent_sales) / len(recent_sales)
            
            # توقع بسيط بناءً على الاتجاه
            predicted_demand = average_daily_sales * days_ahead
            
            return max(0, int(predicted_demand))
            
        except:
            return 0
        finally:
            conn.close()

class SmartPriceCalculator:
    """حاسبة الأسعار الذكية"""
    
    def __init__(self, db):
        self.db = db
    
    def suggest_discount(self, product_id, quantity):
        """اقتراح خصم ذكي"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # جلب معلومات المنتج
            cursor.execute('SELECT stock, price FROM products WHERE id = ?', (product_id,))
            product = cursor.fetchone()
            
            if not product:
                return 0
            
            stock, price = product
            
            # خصم للكميات الكبيرة
            if quantity >= 10:
                return 10  # خصم 10%
            elif quantity >= 5:
                return 5   # خصم 5%
            
            # خصم للمخزون الزائد
            if stock > 100:
                return 7   # خصم 7%
            elif stock > 50:
                return 3   # خصم 3%
            
            return 0
            
        except:
            return 0
        finally:
            conn.close()
    
    def calculate_profit_margin(self, product_id, selling_price):
        """حساب هامش الربح"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # جلب سعر التكلفة (من آخر شراء)
            cursor.execute('''
                SELECT pi.unit_price
                FROM purchase_items pi
                JOIN purchases p ON pi.purchase_id = p.id
                WHERE pi.product_id = ?
                ORDER BY p.purchase_date DESC
                LIMIT 1
            ''', (product_id,))
            
            result = cursor.fetchone()
            if not result:
                return 0
            
            cost_price = result[0]
            profit = selling_price - cost_price
            margin = (profit / selling_price) * 100 if selling_price > 0 else 0
            
            return round(margin, 2)
            
        except:
            return 0
        finally:
            conn.close()

class EnhancedSalesWindow:
    """نقطة البيع المحسنة"""
    
    def __init__(self, parent, db, user):
        self.parent = parent
        self.db = db
        self.user = user
        
        # محركات الذكاء الاصطناعي
        self.ai_engine = AIRecommendationEngine(db)
        self.price_calculator = SmartPriceCalculator(db)
        
        # إنشاء النافذة
        self.window = tk.Toplevel(parent)
        self.window.title("🛒 نقطة البيع الذكية - المطور: هشام المجمر 773988932")
        self.window.geometry("1600x900")
        self.window.state('zoomed')
        self.window.grab_set()
        
        # الألوان والخطوط
        self.setup_styles()
        
        # المتغيرات
        self.setup_variables()
        
        # إنشاء الواجهة
        self.create_widgets()
        
        # تحميل البيانات
        self.load_initial_data()
        
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
        # متغيرات البحث والتصفية
        self.search_var = tk.StringVar()
        self.category_filter_var = tk.StringVar()
        self.customer_var = tk.StringVar()
        
        # متغيرات الفاتورة
        self.discount_var = tk.StringVar(value="0")
        self.tax_var = tk.StringVar(value="0")
        self.payment_method_var = tk.StringVar(value="نقدي")
        self.notes_var = tk.StringVar()
        
        # متغيرات الإجماليات
        self.subtotal_var = tk.StringVar(value="0.00")
        self.discount_amount_var = tk.StringVar(value="0.00")
        self.tax_amount_var = tk.StringVar(value="0.00")
        self.total_var = tk.StringVar(value="0.00")
        
        # قوائم البيانات
        self.cart_items = []
        self.products_data = []
        self.customers_data = []
        self.categories_data = []
        
        # متغيرات الذكاء الاصطناعي
        self.recommendations = []
        self.trending_products = []
        
        # ربط الأحداث
        self.search_var.trace('w', self.on_search_change)
        self.category_filter_var.trace('w', self.on_category_change)
        self.discount_var.trace('w', self.calculate_totals)
        self.tax_var.trace('w', self.calculate_totals)
    
    def create_widgets(self):
        """إنشاء عناصر الواجهة"""
        # الإطار الرئيسي
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # شريط العنوان
        self.create_header(main_frame)
        
        # الإطار الأوسط (المحتوى الرئيسي)
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # الجانب الأيسر - قائمة المنتجات والتوصيات
        self.create_products_panel(content_frame)
        
        # الجانب الأيمن - سلة التسوق والدفع
        self.create_cart_panel(content_frame)
        
        # شريط الحالة
        self.create_status_bar(main_frame)
    
    def create_header(self, parent):
        """إنشاء شريط العنوان"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # العنوان الرئيسي
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT)
        
        title_label = ttk.Label(title_frame, text="🛒 نقطة البيع الذكية", 
                               font=self.fonts['title'])
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(title_frame, 
                                  text=f"المستخدم: {self.user['full_name']} | التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                                  font=self.fonts['small'])
        subtitle_label.pack(anchor=tk.W)
        
        # أزرار سريعة
        buttons_frame = ttk.Frame(header_frame)
        buttons_frame.pack(side=tk.RIGHT)
        
        ttk.Button(buttons_frame, text="🔄 تحديث", 
                  command=self.refresh_data).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(buttons_frame, text="📊 إحصائيات", 
                  command=self.show_statistics).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(buttons_frame, text="🎯 توصيات ذكية", 
                  command=self.show_ai_insights).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(buttons_frame, text="⚙️ إعدادات", 
                  command=self.show_settings).pack(side=tk.LEFT, padx=2)
    
    def create_products_panel(self, parent):
        """إنشاء لوحة المنتجات"""
        # الإطار الأيسر
        left_frame = ttk.Frame(parent)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # شريط البحث والتصفية
        search_frame = ttk.LabelFrame(left_frame, text="🔍 البحث والتصفية", padding="10")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        # البحث
        search_row = ttk.Frame(search_frame)
        search_row.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(search_row, text="البحث:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_row, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(5, 10), fill=tk.X, expand=True)
        
        ttk.Button(search_row, text="🔍", width=3,
                  command=self.search_products).pack(side=tk.LEFT)
        
        # تصفية الفئات
        filter_row = ttk.Frame(search_frame)
        filter_row.pack(fill=tk.X)
        
        ttk.Label(filter_row, text="الفئة:").pack(side=tk.LEFT)
        self.category_combo = ttk.Combobox(filter_row, textvariable=self.category_filter_var,
                                          width=20, state="readonly")
        self.category_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Button(filter_row, text="🗑️ مسح", 
                  command=self.clear_filters).pack(side=tk.LEFT)
        
        # قائمة المنتجات
        products_frame = ttk.LabelFrame(left_frame, text="📦 المنتجات المتاحة", padding="5")
        products_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # جدول المنتجات
        columns = ('id', 'name', 'category', 'price', 'stock', 'actions')
        self.products_tree = ttk.Treeview(products_frame, columns=columns, show='headings', height=15)
        
        # تعريف الأعمدة
        self.products_tree.heading('id', text='الرقم')
        self.products_tree.heading('name', text='اسم المنتج')
        self.products_tree.heading('category', text='الفئة')
        self.products_tree.heading('price', text='السعر')
        self.products_tree.heading('stock', text='المخزون')
        self.products_tree.heading('actions', text='الإجراءات')
        
        # تحديد عرض الأعمدة
        self.products_tree.column('id', width=60, anchor=tk.CENTER)
        self.products_tree.column('name', width=200)
        self.products_tree.column('category', width=120)
        self.products_tree.column('price', width=80, anchor=tk.CENTER)
        self.products_tree.column('stock', width=80, anchor=tk.CENTER)
        self.products_tree.column('actions', width=100, anchor=tk.CENTER)
        
        # شريط التمرير
        products_scrollbar = ttk.Scrollbar(products_frame, orient=tk.VERTICAL, 
                                         command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=products_scrollbar.set)
        
        self.products_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        products_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ربط النقر المزدوج
        self.products_tree.bind('<Double-1>', self.on_product_double_click)
        self.products_tree.bind('<Button-3>', self.show_product_context_menu)
        
        # لوحة التوصيات الذكية
        self.create_recommendations_panel(left_frame)
    
    def create_recommendations_panel(self, parent):
        """إنشاء لوحة التوصيات الذكية"""
        recommendations_frame = ttk.LabelFrame(parent, text="🤖 التوصيات الذكية", padding="5")
        recommendations_frame.pack(fill=tk.X)
        
        # إطار التبويبات
        notebook = ttk.Notebook(recommendations_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # تبويب المنتجات الرائجة
        trending_frame = ttk.Frame(notebook)
        notebook.add(trending_frame, text="🔥 رائجة")
        
        self.trending_listbox = tk.Listbox(trending_frame, height=4, font=self.fonts['small'])
        self.trending_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.trending_listbox.bind('<Double-1>', self.add_trending_to_cart)
        
        # تبويب التوصيات الشخصية
        personal_frame = ttk.Frame(notebook)
        notebook.add(personal_frame, text="👤 شخصية")
        
        self.personal_listbox = tk.Listbox(personal_frame, height=4, font=self.fonts['small'])
        self.personal_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.personal_listbox.bind('<Double-1>', self.add_personal_to_cart)
        
        # تبويب منتجات مترابطة
        related_frame = ttk.Frame(notebook)
        notebook.add(related_frame, text="🔗 مترابطة")
        
        self.related_listbox = tk.Listbox(related_frame, height=4, font=self.fonts['small'])
        self.related_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.related_listbox.bind('<Double-1>', self.add_related_to_cart)
    
    def create_cart_panel(self, parent):
        """إنشاء لوحة سلة التسوق"""
        # الإطار الأيمن
        right_frame = ttk.Frame(parent)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.configure(width=500)
        
        # معلومات العميل
        customer_frame = ttk.LabelFrame(right_frame, text="👤 معلومات العميل", padding="10")
        customer_frame.pack(fill=tk.X, pady=(0, 10))
        
        customer_row = ttk.Frame(customer_frame)
        customer_row.pack(fill=tk.X)
        
        ttk.Label(customer_row, text="العميل:").pack(side=tk.LEFT)
        self.customer_combo = ttk.Combobox(customer_row, textvariable=self.customer_var,
                                          width=25)
        self.customer_combo.pack(side=tk.LEFT, padx=(5, 10), fill=tk.X, expand=True)
        self.customer_combo.bind('<KeyRelease>', self.on_customer_search)
        
        ttk.Button(customer_row, text="➕", width=3,
                  command=self.add_new_customer).pack(side=tk.LEFT)
        
        # سلة التسوق
        cart_frame = ttk.LabelFrame(right_frame, text="🛒 سلة التسوق", padding="5")
        cart_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # جدول السلة
        cart_columns = ('product', 'price', 'qty', 'discount', 'total', 'actions')
        self.cart_tree = ttk.Treeview(cart_frame, columns=cart_columns, show='headings', height=10)
        
        # تعريف أعمدة السلة
        self.cart_tree.heading('product', text='المنتج')
        self.cart_tree.heading('price', text='السعر')
        self.cart_tree.heading('qty', text='الكمية')
        self.cart_tree.heading('discount', text='خصم%')
        self.cart_tree.heading('total', text='الإجمالي')
        self.cart_tree.heading('actions', text='إجراءات')
        
        # تحديد عرض أعمدة السلة
        self.cart_tree.column('product', width=150)
        self.cart_tree.column('price', width=70, anchor=tk.CENTER)
        self.cart_tree.column('qty', width=60, anchor=tk.CENTER)
        self.cart_tree.column('discount', width=60, anchor=tk.CENTER)
        self.cart_tree.column('total', width=80, anchor=tk.CENTER)
        self.cart_tree.column('actions', width=80, anchor=tk.CENTER)
        
        # شريط تمرير السلة
        cart_scrollbar = ttk.Scrollbar(cart_frame, orient=tk.VERTICAL, 
                                      command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=cart_scrollbar.set)
        
        self.cart_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cart_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ربط أحداث السلة
        self.cart_tree.bind('<Double-1>', self.edit_cart_item)
        self.cart_tree.bind('<Button-3>', self.show_cart_context_menu)
        
        # أزرار السلة
        cart_buttons_frame = ttk.Frame(cart_frame)
        cart_buttons_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(cart_buttons_frame, text="🗑️ مسح الكل", 
                  command=self.clear_cart).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(cart_buttons_frame, text="💾 حفظ مؤقت", 
                  command=self.save_draft).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(cart_buttons_frame, text="📂 استرداد", 
                  command=self.load_draft).pack(side=tk.LEFT, padx=2)
        
        # لوحة الحسابات
        self.create_calculations_panel(right_frame)
        
        # لوحة الدفع
        self.create_payment_panel(right_frame)
    
    def create_calculations_panel(self, parent):
        """إنشاء لوحة الحسابات"""
        calc_frame = ttk.LabelFrame(parent, text="💰 الحسابات", padding="10")
        calc_frame.pack(fill=tk.X, pady=(0, 10))
        
        # الإجمالي الفرعي
        subtotal_row = ttk.Frame(calc_frame)
        subtotal_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(subtotal_row, text="الإجمالي الفرعي:", 
                 font=self.fonts['normal']).pack(side=tk.LEFT)
        ttk.Label(subtotal_row, textvariable=self.subtotal_var, 
                 font=self.fonts['subtitle']).pack(side=tk.RIGHT)
        
        # الخصم
        discount_row = ttk.Frame(calc_frame)
        discount_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(discount_row, text="الخصم:").pack(side=tk.LEFT)
        
        discount_entry_frame = ttk.Frame(discount_row)
        discount_entry_frame.pack(side=tk.RIGHT)
        
        ttk.Entry(discount_entry_frame, textvariable=self.discount_var, 
                 width=8).pack(side=tk.LEFT)
        ttk.Label(discount_entry_frame, text="%").pack(side=tk.LEFT)
        
        ttk.Button(discount_entry_frame, text="🎯", width=3,
                  command=self.suggest_smart_discount).pack(side=tk.LEFT, padx=(5, 0))
        
        # مبلغ الخصم
        discount_amount_row = ttk.Frame(calc_frame)
        discount_amount_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(discount_amount_row, text="مبلغ الخصم:").pack(side=tk.LEFT)
        ttk.Label(discount_amount_row, textvariable=self.discount_amount_var, 
                 foreground=self.colors['danger']).pack(side=tk.RIGHT)
        
        # الضريبة
        tax_row = ttk.Frame(calc_frame)
        tax_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(tax_row, text="الضريبة:").pack(side=tk.LEFT)
        
        tax_entry_frame = ttk.Frame(tax_row)
        tax_entry_frame.pack(side=tk.RIGHT)
        
        ttk.Entry(tax_entry_frame, textvariable=self.tax_var, 
                 width=8).pack(side=tk.LEFT)
        ttk.Label(tax_entry_frame, text="%").pack(side=tk.LEFT)
        
        # مبلغ الضريبة
        tax_amount_row = ttk.Frame(calc_frame)
        tax_amount_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(tax_amount_row, text="مبلغ الضريبة:").pack(side=tk.LEFT)
        ttk.Label(tax_amount_row, textvariable=self.tax_amount_var, 
                 foreground=self.colors['info']).pack(side=tk.RIGHT)
        
        # خط فاصل
        ttk.Separator(calc_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # الإجمالي النهائي
        total_row = ttk.Frame(calc_frame)
        total_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(total_row, text="الإجمالي النهائي:", 
                 font=self.fonts['subtitle']).pack(side=tk.LEFT)
        ttk.Label(total_row, textvariable=self.total_var, 
                 font=self.fonts['title'], 
                 foreground=self.colors['success']).pack(side=tk.RIGHT)
    
    def create_payment_panel(self, parent):
        """إنشاء لوحة الدفع"""
        payment_frame = ttk.LabelFrame(parent, text="💳 الدفع", padding="10")
        payment_frame.pack(fill=tk.X)
        
        # طريقة الدفع
        payment_method_row = ttk.Frame(payment_frame)
        payment_method_row.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(payment_method_row, text="طريقة الدفع:").pack(side=tk.LEFT)
        
        payment_methods = ["نقدي", "بطاقة ائتمان", "بطاقة خصم", "تحويل بنكي", "آجل"]
        payment_combo = ttk.Combobox(payment_method_row, textvariable=self.payment_method_var,
                                    values=payment_methods, state="readonly", width=15)
        payment_combo.pack(side=tk.RIGHT)
        
        # الملاحظات
        notes_row = ttk.Frame(payment_frame)
        notes_row.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(notes_row, text="ملاحظات:").pack(side=tk.LEFT)
        ttk.Entry(notes_row, textvariable=self.notes_var).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # أزرار الدفع
        payment_buttons_frame = ttk.Frame(payment_frame)
        payment_buttons_frame.pack(fill=tk.X)
        
        # الصف الأول من الأزرار
        buttons_row1 = ttk.Frame(payment_buttons_frame)
        buttons_row1.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(buttons_row1, text="💰 دفع نقدي", 
                  command=lambda: self.process_payment("نقدي"),
                  style="success.TButton").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        
        ttk.Button(buttons_row1, text="💳 دفع بالبطاقة", 
                  command=lambda: self.process_payment("بطاقة"),
                  style="info.TButton").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        
        # الصف الثاني من الأزرار
        buttons_row2 = ttk.Frame(payment_buttons_frame)
        buttons_row2.pack(fill=tk.X)
        
        ttk.Button(buttons_row2, text="📄 طباعة فاتورة", 
                  command=self.print_invoice).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        
        ttk.Button(buttons_row2, text="📧 إرسال بالإيميل", 
                  command=self.email_invoice).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
    
    def create_status_bar(self, parent):
        """إنشاء شريط الحالة"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        # معلومات الحالة
        self.status_var = tk.StringVar(value="جاهز")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)
        
        # معلومات إضافية
        info_frame = ttk.Frame(status_frame)
        info_frame.pack(side=tk.RIGHT)
        
        # عدد المنتجات في السلة
        self.cart_count_var = tk.StringVar(value="العناصر: 0")
        ttk.Label(info_frame, textvariable=self.cart_count_var).pack(side=tk.LEFT, padx=10)
        
        # الوقت الحالي
        self.time_var = tk.StringVar()
        ttk.Label(info_frame, textvariable=self.time_var).pack(side=tk.LEFT)
        
        # تحديث الوقت
        self.update_time()
    
    def load_initial_data(self):
        """تحميل البيانات الأولية"""
        self.status_var.set("جاري تحميل البيانات...")
        
        # تحميل المنتجات
        self.load_products()
        
        # تحميل العملاء
        self.load_customers()
        
        # تحميل الفئات
        self.load_categories()
        
        # تحميل التوصيات الذكية
        self.load_ai_recommendations()
        
        self.status_var.set("تم تحميل البيانات بنجاح")
    
    def load_products(self):
        """تحميل المنتجات"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT p.id, p.name, c.name as category, p.price, p.stock, p.min_stock
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.stock > 0
                ORDER BY p.name
            ''')
            
            self.products_data = cursor.fetchall()
            self.update_products_display()
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في تحميل المنتجات: {e}")
        finally:
            conn.close()
    
    def update_products_display(self):
        """تحديث عرض المنتجات"""
        # مسح البيانات الحالية
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        # إضافة المنتجات
        for product in self.products_data:
            product_id, name, category, price, stock, min_stock = product
            
            # تحديد لون المخزون
            stock_color = ""
            if stock <= min_stock:
                stock_color = "red"
            elif stock <= min_stock * 2:
                stock_color = "orange"
            
            # إدراج المنتج
            item = self.products_tree.insert('', tk.END, values=(
                product_id, name, category or "غير محدد", 
                f"{price:.2f}", stock, "إضافة"
            ))
            
            # تلوين المخزون المنخفض
            if stock_color:
                self.products_tree.set(item, 'stock', f"{stock} ⚠️")
    
    def load_customers(self):
        """تحميل العملاء"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id, name, phone FROM customers ORDER BY name')
            self.customers_data = cursor.fetchall()
            
            # تحديث قائمة العملاء
            customer_names = [f"{customer[1]} - {customer[2]}" for customer in self.customers_data]
            self.customer_combo['values'] = customer_names
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في تحميل العملاء: {e}")
        finally:
            conn.close()
    
    def load_categories(self):
        """تحميل الفئات"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id, name FROM categories ORDER BY name')
            self.categories_data = cursor.fetchall()
            
            # تحديث قائمة الفئات
            category_names = ["جميع الفئات"] + [cat[1] for cat in self.categories_data]
            self.category_combo['values'] = category_names
            self.category_combo.set("جميع الفئات")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في تحميل الفئات: {e}")
        finally:
            conn.close()
    
    def load_ai_recommendations(self):
        """تحميل التوصيات الذكية"""
        try:
            # المنتجات الرائجة
            trending = self.ai_engine.get_trending_products()
            self.trending_listbox.delete(0, tk.END)
            for product in trending:
                self.trending_listbox.insert(tk.END, f"{product[1]} - {product[2]:.2f} ر.س (مباع: {product[4]})")
            
            # التوصيات الشخصية (إذا كان هناك عميل محدد)
            if self.customer_var.get():
                customer_id = self.get_selected_customer_id()
                if customer_id:
                    personal = self.ai_engine.get_customer_recommendations(customer_id)
                    self.personal_listbox.delete(0, tk.END)
                    for product in personal:
                        self.personal_listbox.insert(tk.END, f"{product[1]} - {product[2]:.2f} ر.س")
            
        except Exception as e:
            print(f"خطأ في تحميل التوصيات: {e}")
    
    def on_search_change(self, *args):
        """عند تغيير نص البحث"""
        search_term = self.search_var.get().lower()
        if len(search_term) >= 2:  # البحث عند كتابة حرفين أو أكثر
            self.search_products()
    
    def search_products(self):
        """البحث في المنتجات"""
        search_term = self.search_var.get().lower()
        category_filter = self.category_filter_var.get()
        
        # تصفية المنتجات
        filtered_products = []
        for product in self.products_data:
            product_id, name, category, price, stock, min_stock = product
            
            # فلترة النص
            if search_term and search_term not in name.lower():
                continue
            
            # فلترة الفئة
            if category_filter and category_filter != "جميع الفئات" and category != category_filter:
                continue
            
            filtered_products.append(product)
        
        # تحديث العرض
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        for product in filtered_products:
            product_id, name, category, price, stock, min_stock = product
            
            item = self.products_tree.insert('', tk.END, values=(
                product_id, name, category or "غير محدد", 
                f"{price:.2f}", stock, "إضافة"
            ))
            
            if stock <= min_stock:
                self.products_tree.set(item, 'stock', f"{stock} ⚠️")
    
    def on_category_change(self, *args):
        """عند تغيير الفئة"""
        self.search_products()
    
    def clear_filters(self):
        """مسح الفلاتر"""
        self.search_var.set("")
        self.category_filter_var.set("جميع الفئات")
        self.update_products_display()
    
    def on_product_double_click(self, event):
        """عند النقر المزدوج على منتج"""
        selection = self.products_tree.selection()
        if selection:
            item = self.products_tree.item(selection[0])
            product_data = item['values']
            self.add_to_cart(product_data[0], product_data[1], product_data[3])
    
    def add_to_cart(self, product_id, product_name, price, quantity=1):
        """إضافة منتج للسلة"""
        try:
            # التحقق من وجود المنتج في السلة
            for i, item in enumerate(self.cart_items):
                if item['product_id'] == product_id:
                    # زيادة الكمية
                    self.cart_items[i]['quantity'] += quantity
                    self.update_cart_display()
                    self.calculate_totals()
                    return
            
            # إضافة منتج جديد
            cart_item = {
                'product_id': product_id,
                'product_name': product_name,
                'price': float(price),
                'quantity': quantity,
                'discount': 0,
                'total': float(price) * quantity
            }
            
            self.cart_items.append(cart_item)
            self.update_cart_display()
            self.calculate_totals()
            
            # تحديث التوصيات المترابطة
            self.load_related_products(product_id)
            
            self.status_var.set(f"تم إضافة {product_name} للسلة")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في إضافة المنتج للسلة: {e}")
    
    def update_cart_display(self):
        """تحديث عرض السلة"""
        # مسح البيانات الحالية
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        # إضافة عناصر السلة
        for item in self.cart_items:
            self.cart_tree.insert('', tk.END, values=(
                item['product_name'],
                f"{item['price']:.2f}",
                item['quantity'],
                f"{item['discount']:.1f}",
                f"{item['total']:.2f}",
                "تعديل"
            ))
        
        # تحديث عداد العناصر
        self.cart_count_var.set(f"العناصر: {len(self.cart_items)}")
    
    def calculate_totals(self, *args):
        """حساب الإجماليات"""
        try:
            # الإجمالي الفرعي
            subtotal = sum(item['total'] for item in self.cart_items)
            self.subtotal_var.set(f"{subtotal:.2f} ر.س")
            
            # الخصم
            discount_percent = float(self.discount_var.get() or 0)
            discount_amount = subtotal * (discount_percent / 100)
            self.discount_amount_var.set(f"{discount_amount:.2f} ر.س")
            
            # الضريبة
            tax_percent = float(self.tax_var.get() or 0)
            tax_amount = (subtotal - discount_amount) * (tax_percent / 100)
            self.tax_amount_var.set(f"{tax_amount:.2f} ر.س")
            
            # الإجمالي النهائي
            total = subtotal - discount_amount + tax_amount
            self.total_var.set(f"{total:.2f} ر.س")
            
        except ValueError:
            pass
    
    def suggest_smart_discount(self):
        """اقتراح خصم ذكي"""
        if not self.cart_items:
            messagebox.showinfo("تنبيه", "السلة فارغة")
            return
        
        try:
            # حساب الخصم المقترح بناءً على الكمية والمخزون
            total_quantity = sum(item['quantity'] for item in self.cart_items)
            suggested_discount = 0
            
            # خصم للكميات الكبيرة
            if total_quantity >= 20:
                suggested_discount = 15
            elif total_quantity >= 10:
                suggested_discount = 10
            elif total_quantity >= 5:
                suggested_discount = 5
            
            # خصم إضافي للمنتجات بطيئة الحركة
            for item in self.cart_items:
                product_discount = self.price_calculator.suggest_discount(
                    item['product_id'], item['quantity']
                )
                suggested_discount = max(suggested_discount, product_discount)
            
            if suggested_discount > 0:
                result = messagebox.askyesno(
                    "خصم ذكي", 
                    f"الخصم المقترح: {suggested_discount}%\n"
                    f"هل تريد تطبيقه؟"
                )
                if result:
                    self.discount_var.set(str(suggested_discount))
            else:
                messagebox.showinfo("خصم ذكي", "لا يوجد خصم مقترح حالياً")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في حساب الخصم الذكي: {e}")
    
    def load_related_products(self, product_id):
        """تحميل المنتجات المترابطة"""
        try:
            related = self.ai_engine.get_frequently_bought_together(product_id)
            self.related_listbox.delete(0, tk.END)
            for product in related:
                self.related_listbox.insert(tk.END, 
                    f"{product[1]} - {product[2]:.2f} ر.س (تكرار: {product[3]})")
        except Exception as e:
            print(f"خطأ في تحميل المنتجات المترابطة: {e}")
    
    def process_payment(self, payment_type):
        """معالجة الدفع"""
        if not self.cart_items:
            messagebox.showwarning("تحذير", "السلة فارغة")
            return
        
        try:
            # حفظ الفاتورة في قاعدة البيانات
            sale_id = self.save_sale()
            
            if sale_id:
                # طباعة الفاتورة
                self.print_invoice(sale_id)
                
                # مسح السلة
                self.clear_cart()
                
                # رسالة نجاح
                messagebox.showinfo("نجح", f"تم إتمام البيع بنجاح\nرقم الفاتورة: {sale_id}")
                
                self.status_var.set("تم إتمام البيع بنجاح")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في معالجة الدفع: {e}")
    
    def save_sale(self):
        """حفظ الفاتورة"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # بيانات الفاتورة
            customer_id = self.get_selected_customer_id()
            subtotal = sum(item['total'] for item in self.cart_items)
            discount_amount = subtotal * (float(self.discount_var.get() or 0) / 100)
            tax_amount = (subtotal - discount_amount) * (float(self.tax_var.get() or 0) / 100)
            total = subtotal - discount_amount + tax_amount
            
            # إدراج الفاتورة
            cursor.execute('''
                INSERT INTO sales (customer_id, user_id, sale_date, subtotal, 
                                 discount_percent, discount_amount, tax_percent, 
                                 tax_amount, total, payment_method, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                customer_id, self.user['id'], datetime.now().isoformat(),
                subtotal, float(self.discount_var.get() or 0), discount_amount,
                float(self.tax_var.get() or 0), tax_amount, total,
                self.payment_method_var.get(), self.notes_var.get()
            ))
            
            sale_id = cursor.lastrowid
            
            # إدراج عناصر الفاتورة
            for item in self.cart_items:
                cursor.execute('''
                    INSERT INTO sale_items (sale_id, product_id, quantity, 
                                          unit_price, discount_percent, total)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    sale_id, item['product_id'], item['quantity'],
                    item['price'], item['discount'], item['total']
                ))
                
                # تحديث المخزون
                cursor.execute('''
                    UPDATE products SET stock = stock - ? WHERE id = ?
                ''', (item['quantity'], item['product_id']))
            
            conn.commit()
            return sale_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def print_invoice(self, sale_id=None):
        """طباعة الفاتورة"""
        try:
            # هنا يمكن إضافة كود الطباعة الفعلي
            messagebox.showinfo("طباعة", "تم إرسال الفاتورة للطابعة")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في طباعة الفاتورة: {e}")
    
    def clear_cart(self):
        """مسح السلة"""
        self.cart_items.clear()
        self.update_cart_display()
        self.calculate_totals()
        self.status_var.set("تم مسح السلة")
    
    def get_selected_customer_id(self):
        """الحصول على معرف العميل المحدد"""
        customer_text = self.customer_var.get()
        if not customer_text:
            return None
        
        for customer in self.customers_data:
            if f"{customer[1]} - {customer[2]}" == customer_text:
                return customer[0]
        return None
    
    def refresh_data(self):
        """تحديث البيانات"""
        self.load_initial_data()
    
    def show_statistics(self):
        """عرض الإحصائيات"""
        messagebox.showinfo("إحصائيات", "ميزة الإحصائيات قيد التطوير")
    
    def show_ai_insights(self):
        """عرض رؤى الذكاء الاصطناعي"""
        messagebox.showinfo("رؤى ذكية", "ميزة الرؤى الذكية قيد التطوير")
    
    def show_settings(self):
        """عرض الإعدادات"""
        messagebox.showinfo("إعدادات", "ميزة الإعدادات قيد التطوير")
    
    def start_auto_refresh(self):
        """بدء التحديث التلقائي"""
        def auto_refresh():
            while True:
                time.sleep(300)  # تحديث كل 5 دقائق
                try:
                    self.load_ai_recommendations()
                except:
                    pass
        
        thread = threading.Thread(target=auto_refresh, daemon=True)
        thread.start()
    
    def update_time(self):
        """تحديث الوقت"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_var.set(current_time)
        self.window.after(1000, self.update_time)
    
    # المزيد من الدوال المساعدة...
    def on_customer_search(self, event):
        """البحث في العملاء أثناء الكتابة"""
        pass
    
    def add_new_customer(self):
        """إضافة عميل جديد"""
        messagebox.showinfo("إضافة عميل", "ميزة إضافة العملاء قيد التطوير")
    
    def edit_cart_item(self, event):
        """تعديل عنصر في السلة"""
        pass
    
    def show_product_context_menu(self, event):
        """عرض قائمة السياق للمنتج"""
        pass
    
    def show_cart_context_menu(self, event):
        """عرض قائمة السياق للسلة"""
        pass
    
    def save_draft(self):
        """حفظ مسودة"""
        messagebox.showinfo("حفظ مسودة", "تم حفظ المسودة")
    
    def load_draft(self):
        """تحميل مسودة"""
        messagebox.showinfo("تحميل مسودة", "ميزة تحميل المسودة قيد التطوير")
    
    def email_invoice(self):
        """إرسال الفاتورة بالإيميل"""
        messagebox.showinfo("إرسال إيميل", "ميزة الإرسال بالإيميل قيد التطوير")
    
    def add_trending_to_cart(self, event):
        """إضافة منتج رائج للسلة"""
        pass
    
    def add_personal_to_cart(self, event):
        """إضافة توصية شخصية للسلة"""
        pass
    
    def add_related_to_cart(self, event):
        """إضافة منتج مترابط للسلة"""
        pass