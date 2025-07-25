#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
لوحة التحكم الذكية
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from smart_features import SmartAnalytics, AutomationEngine

class DashboardWindow:
    def __init__(self, parent, db, user):
        self.parent = parent
        self.db = db
        self.user = user
        
        # إنشاء النافذة
        self.window = tk.Toplevel(parent)
        self.window.title("🎛️ لوحة التحكم الذكية")
        self.window.geometry("1400x800")
        self.window.grab_set()
        
        # الميزات الذكية
        self.analytics = SmartAnalytics(self.db)
        self.automation = AutomationEngine(self.db)
        
        # إنشاء الواجهة
        self.create_widgets()
        
        # تحديث البيانات
        self.refresh_dashboard()
    
    def create_widgets(self):
        # الإطار الرئيسي
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # شريط العنوان
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(title_frame, text="🎛️ لوحة التحكم الذكية", 
                 font=("Arial", 18, "bold")).pack(side=tk.LEFT)
        
        ttk.Button(title_frame, text="🔄 تحديث", 
                  command=self.refresh_dashboard).pack(side=tk.RIGHT)
        
        # إنشاء دفتر الملاحظات للتبويبات
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # تبويب التنبيهات
        self.create_alerts_tab()
        
        # تبويب التوقعات
        self.create_predictions_tab()
        
        # تبويب التحليلات
        self.create_analytics_tab()
        
        # تبويب الأتمتة
        self.create_automation_tab()
    
    def create_alerts_tab(self):
        """تبويب التنبيهات"""
        alerts_frame = ttk.Frame(self.notebook)
        self.notebook.add(alerts_frame, text="🚨 التنبيهات")
        
        # إطار التنبيهات الحرجة
        critical_frame = ttk.LabelFrame(alerts_frame, text="تنبيهات حرجة", padding="10")
        critical_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.critical_alerts_tree = ttk.Treeview(critical_frame, 
                                               columns=("المنتج", "المخزون الحالي", "الحد الأدنى", "الحالة"),
                                               show="headings", height=6)
        
        for col in self.critical_alerts_tree["columns"]:
            self.critical_alerts_tree.heading(col, text=col)
            self.critical_alerts_tree.column(col, width=150, anchor=tk.CENTER)
        
        self.critical_alerts_tree.pack(fill=tk.X)
        
        # إطار التنبيهات العامة
        general_frame = ttk.LabelFrame(alerts_frame, text="تنبيهات عامة", padding="10")
        general_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.general_alerts_tree = ttk.Treeview(general_frame,
                                              columns=("النوع", "الوصف", "التاريخ", "الأولوية"),
                                              show="headings", height=10)
        
        for col in self.general_alerts_tree["columns"]:
            self.general_alerts_tree.heading(col, text=col)
            self.general_alerts_tree.column(col, width=200, anchor=tk.CENTER)
        
        scrollbar_alerts = ttk.Scrollbar(general_frame, orient=tk.VERTICAL, 
                                       command=self.general_alerts_tree.yview)
        self.general_alerts_tree.configure(yscrollcommand=scrollbar_alerts.set)
        
        self.general_alerts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_alerts.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_predictions_tab(self):
        """تبويب التوقعات"""
        predictions_frame = ttk.Frame(self.notebook)
        self.notebook.add(predictions_frame, text="🔮 التوقعات")
        
        # إطار اختيار المنتج
        selection_frame = ttk.Frame(predictions_frame)
        selection_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(selection_frame, text="اختر المنتج:").pack(side=tk.LEFT)
        
        self.product_var = tk.StringVar()
        self.product_combo = ttk.Combobox(selection_frame, textvariable=self.product_var,
                                         width=30, state="readonly")
        self.product_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(selection_frame, text="🔍 تحليل", 
                  command=self.analyze_product).pack(side=tk.LEFT, padx=(10, 0))
        
        # إطار النتائج
        results_frame = ttk.LabelFrame(predictions_frame, text="نتائج التحليل", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.prediction_text = tk.Text(results_frame, wrap=tk.WORD, height=20)
        prediction_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL,
                                           command=self.prediction_text.yview)
        self.prediction_text.configure(yscrollcommand=prediction_scrollbar.set)
        
        self.prediction_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        prediction_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_analytics_tab(self):
        """تبويب التحليلات"""
        analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(analytics_frame, text="📊 التحليلات")
        
        # إطار المنتجات بطيئة الحركة
        slow_frame = ttk.LabelFrame(analytics_frame, text="المنتجات بطيئة الحركة", padding="10")
        slow_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.slow_products_tree = ttk.Treeview(slow_frame,
                                             columns=("المنتج", "المخزون", "رأس المال المقيد", "المبيعات (90 يوم)"),
                                             show="headings", height=8)
        
        for col in self.slow_products_tree["columns"]:
            self.slow_products_tree.heading(col, text=col)
            self.slow_products_tree.column(col, width=150, anchor=tk.CENTER)
        
        slow_scrollbar = ttk.Scrollbar(slow_frame, orient=tk.VERTICAL,
                                     command=self.slow_products_tree.yview)
        self.slow_products_tree.configure(yscrollcommand=slow_scrollbar.set)
        
        self.slow_products_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        slow_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # إطار تحليل العملاء
        customers_frame = ttk.LabelFrame(analytics_frame, text="أفضل العملاء", padding="10")
        customers_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.customers_tree = ttk.Treeview(customers_frame,
                                         columns=("العميل", "عدد المشتريات", "إجمالي الإنفاق", "آخر شراء"),
                                         show="headings", height=10)
        
        for col in self.customers_tree["columns"]:
            self.customers_tree.heading(col, text=col)
            self.customers_tree.column(col, width=150, anchor=tk.CENTER)
        
        customers_scrollbar = ttk.Scrollbar(customers_frame, orient=tk.VERTICAL,
                                          command=self.customers_tree.yview)
        self.customers_tree.configure(yscrollcommand=customers_scrollbar.set)
        
        self.customers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        customers_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_automation_tab(self):
        """تبويب الأتمتة"""
        automation_frame = ttk.Frame(self.notebook)
        self.notebook.add(automation_frame, text="🤖 الأتمتة")
        
        # إطار أوامر الشراء التلقائية
        purchase_frame = ttk.LabelFrame(automation_frame, text="أوامر الشراء المقترحة", padding="10")
        purchase_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.purchase_suggestions_tree = ttk.Treeview(purchase_frame,
                                                    columns=("المنتج", "المخزون الحالي", "الكمية المقترحة", "الأولوية"),
                                                    show="headings", height=8)
        
        for col in self.purchase_suggestions_tree["columns"]:
            self.purchase_suggestions_tree.heading(col, text=col)
            self.purchase_suggestions_tree.column(col, width=150, anchor=tk.CENTER)
        
        purchase_scrollbar = ttk.Scrollbar(purchase_frame, orient=tk.VERTICAL,
                                         command=self.purchase_suggestions_tree.yview)
        self.purchase_suggestions_tree.configure(yscrollcommand=purchase_scrollbar.set)
        
        self.purchase_suggestions_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        purchase_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # أزرار الأتمتة
        automation_buttons = ttk.Frame(automation_frame)
        automation_buttons.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(automation_buttons, text="🛒 إنشاء أوامر شراء تلقائية",
                  command=self.generate_purchase_orders).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(automation_buttons, text="⚙️ تحسين مستويات المخزون",
                  command=self.optimize_inventory).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(automation_buttons, text="🔍 اكتشاف الشذوذ",
                  command=self.detect_anomalies).pack(side=tk.LEFT)
        
        # إطار نتائج الأتمتة
        results_automation_frame = ttk.LabelFrame(automation_frame, text="نتائج الأتمتة", padding="10")
        results_automation_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.automation_text = tk.Text(results_automation_frame, wrap=tk.WORD, height=10)
        automation_text_scrollbar = ttk.Scrollbar(results_automation_frame, orient=tk.VERTICAL,
                                                 command=self.automation_text.yview)
        self.automation_text.configure(yscrollcommand=automation_text_scrollbar.set)
        
        self.automation_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        automation_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def refresh_dashboard(self):
        """تحديث لوحة التحكم"""
        try:
            # تحديث التنبيهات
            self.update_alerts()
            
            # تحديث قائمة المنتجات
            self.update_products_list()
            
            # تحديث التحليلات
            self.update_analytics()
            
            # تحديث الأتمتة
            self.update_automation()
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في تحديث لوحة التحكم: {str(e)}")
    
    def update_alerts(self):
        """تحديث التنبيهات"""
        # مسح البيانات الحالية
        for item in self.critical_alerts_tree.get_children():
            self.critical_alerts_tree.delete(item)
        
        for item in self.general_alerts_tree.get_children():
            self.general_alerts_tree.delete(item)
        
        # جلب التنبيهات
        alerts = self.analytics.generate_reorder_alerts()
        
        for alert in alerts:
            if alert['urgency'] == 'critical':
                self.critical_alerts_tree.insert('', tk.END, values=(
                    alert['product_name'],
                    alert['current_stock'],
                    alert['min_stock'],
                    "نفد المخزون" if alert['current_stock'] == 0 else "حرج"
                ))
            
            self.general_alerts_tree.insert('', tk.END, values=(
                "مخزون منخفض",
                f"{alert['product_name']} - المخزون: {alert['current_stock']}",
                datetime.now().strftime("%Y-%m-%d"),
                alert['urgency']
            ))
        
        # إضافة تنبيهات الشذوذ
        anomalies = self.automation.detect_anomalies()
        for anomaly in anomalies:
            self.general_alerts_tree.insert('', tk.END, values=(
                anomaly['type'],
                anomaly['description'],
                datetime.now().strftime("%Y-%m-%d"),
                "متوسط"
            ))
    
    def update_products_list(self):
        """تحديث قائمة المنتجات"""
        products = self.db.get_products()
        product_values = [f"{product[0]} - {product[1]}" for product in products]
        self.product_combo['values'] = product_values
    
    def update_analytics(self):
        """تحديث التحليلات"""
        # المنتجات بطيئة الحركة
        for item in self.slow_products_tree.get_children():
            self.slow_products_tree.delete(item)
        
        slow_products = self.analytics.detect_slow_moving_products()
        for product in slow_products:
            self.slow_products_tree.insert('', tk.END, values=(
                product[1],  # اسم المنتج
                product[2],  # المخزون
                f"{product[5]:.2f}",  # رأس المال المقيد
                product[4]   # المبيعات
            ))
        
        # أفضل العملاء
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        
        customers = self.analytics.analyze_customer_behavior()
        for customer in customers:
            self.customers_tree.insert('', tk.END, values=(
                customer[1],  # اسم العميل
                customer[2],  # عدد المشتريات
                f"{customer[3]:.2f}",  # إجمالي الإنفاق
                customer[4] or "غير محدد"  # آخر شراء
            ))
    
    def update_automation(self):
        """تحديث الأتمتة"""
        # مسح البيانات الحالية
        for item in self.purchase_suggestions_tree.get_children():
            self.purchase_suggestions_tree.delete(item)
        
        # جلب اقتراحات الشراء
        suggestions = self.automation.auto_generate_purchase_orders()
        for suggestion in suggestions:
            self.purchase_suggestions_tree.insert('', tk.END, values=(
                suggestion['product_name'],
                suggestion['current_stock'],
                f"{suggestion['suggested_quantity']:.0f}",
                suggestion['urgency']
            ))
    
    def analyze_product(self):
        """تحليل المنتج المحدد"""
        if not self.product_var.get():
            messagebox.showwarning("تحذير", "يرجى اختيار منتج للتحليل")
            return
        
        try:
            product_id = int(self.product_var.get().split(' - ')[0])
            
            # مسح النص الحالي
            self.prediction_text.delete(1.0, tk.END)
            
            # توقع احتياجات المخزون
            prediction = self.analytics.predict_stock_needs(product_id)
            
            if prediction:
                result = f"""
📊 تحليل توقعات المخزون
{'='*50}

المخزون الحالي: {prediction['current_stock']}
متوسط المبيعات اليومية: {prediction['avg_daily_sales']}
الطلب المتوقع (30 يوم): {prediction['predicted_demand']:.1f}
مخزون الأمان: {prediction['safety_stock']:.1f}
الكمية المقترحة للطلب: {prediction['recommended_order']:.1f}
الأيام حتى نفاد المخزون: {prediction['days_until_stockout']:.1f}

"""
                self.prediction_text.insert(tk.END, result)
            
            # تحليل الاتجاهات الموسمية
            trends = self.analytics.get_seasonal_trends(product_id)
            
            if trends:
                trends_text = f"""
📈 تحليل الاتجاهات الموسمية
{'='*50}

أفضل شهر للمبيعات: {trends['peak_month'] or 'غير محدد'}
أفضل يوم في الأسبوع: {trends['peak_weekday'] or 'غير محدد'}
أفضل ساعة في اليوم: {trends['peak_hour'] or 'غير محدد'}

المبيعات الشهرية:
"""
                
                for month, sales in trends['monthly_trends'].items():
                    trends_text += f"  {month}: {sales:.1f}\n"
                
                trends_text += "\nالمبيعات الأسبوعية:\n"
                for day, sales in trends['weekday_trends'].items():
                    trends_text += f"  {day}: {sales:.1f}\n"
                
                self.prediction_text.insert(tk.END, trends_text)
            
            # اقتراحات تحسين الأسعار
            pricing = self.analytics.suggest_pricing_optimization(product_id)
            
            if pricing:
                pricing_text = f"""

💰 تحليل الأسعار
{'='*50}

هامش الربح الحالي: {pricing['current_margin']:.1f}%

الاقتراحات:
"""
                
                for suggestion in pricing['suggestions']:
                    pricing_text += f"""
  النوع: {suggestion['type']}
  السعر الحالي: {suggestion['current_price']:.2f}
  السعر المقترح: {suggestion['suggested_price']:.2f}
  السبب: {suggestion['reason']}
"""
                
                self.prediction_text.insert(tk.END, pricing_text)
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في تحليل المنتج: {str(e)}")
    
    def generate_purchase_orders(self):
        """إنشاء أوامر شراء تلقائية"""
        try:
            suggestions = self.automation.auto_generate_purchase_orders()
            
            self.automation_text.delete(1.0, tk.END)
            
            if not suggestions:
                self.automation_text.insert(tk.END, "لا توجد أوامر شراء مقترحة حالياً.\n")
                return
            
            result = f"""
🛒 أوامر الشراء المقترحة
{'='*50}

تم إنشاء {len(suggestions)} اقتراح شراء:

"""
            
            for i, suggestion in enumerate(suggestions, 1):
                result += f"""
{i}. {suggestion['product_name']}
   المخزون الحالي: {suggestion['current_stock']}
   الكمية المقترحة: {suggestion['suggested_quantity']:.0f}
   الأولوية: {suggestion['urgency']}
   السبب: {suggestion['reason']}

"""
            
            self.automation_text.insert(tk.END, result)
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في إنشاء أوامر الشراء: {str(e)}")
    
    def optimize_inventory(self):
        """تحسين مستويات المخزون"""
        try:
            suggestions = self.automation.optimize_inventory_levels()
            
            self.automation_text.delete(1.0, tk.END)
            
            if not suggestions:
                self.automation_text.insert(tk.END, "مستويات المخزون محسنة بالفعل.\n")
                return
            
            result = f"""
⚙️ اقتراحات تحسين المخزون
{'='*50}

تم العثور على {len(suggestions)} اقتراح تحسين:

"""
            
            for i, suggestion in enumerate(suggestions, 1):
                result += f"""
{i}. المنتج ID: {suggestion['product_id']}
   الحد الأدنى الحالي: {suggestion['current_min_stock']}
   الحد الأدنى المقترح: {suggestion['suggested_min_stock']}
   السبب: {suggestion['reason']}

"""
            
            self.automation_text.insert(tk.END, result)
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في تحسين المخزون: {str(e)}")
    
    def detect_anomalies(self):
        """اكتشاف الشذوذ"""
        try:
            anomalies = self.automation.detect_anomalies()
            
            self.automation_text.delete(1.0, tk.END)
            
            if not anomalies:
                self.automation_text.insert(tk.END, "لم يتم اكتشاف أي شذوذ في البيانات.\n")
                return
            
            result = f"""
🔍 تقرير اكتشاف الشذوذ
{'='*50}

تم اكتشاف {len(anomalies)} حالة شذوذ:

"""
            
            for i, anomaly in enumerate(anomalies, 1):
                result += f"""
{i}. النوع: {anomaly['type']}
   الوصف: {anomaly['description']}
"""
                
                if anomaly['type'] == 'unusual_sale':
                    result += f"   رقم الفاتورة: {anomaly['sale_id']}\n"
                    result += f"   المبلغ: {anomaly['amount']:.2f}\n"
                    result += f"   العميل: {anomaly['customer']}\n"
                
                elif anomaly['type'] == 'stagnant_product':
                    result += f"   اسم المنتج: {anomaly['product_name']}\n"
                    result += f"   المخزون: {anomaly['stock']}\n"
                
                result += "\n"
            
            self.automation_text.insert(tk.END, result)
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في اكتشاف الشذوذ: {str(e)}")