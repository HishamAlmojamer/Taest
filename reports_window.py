import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import sqlite3
from print_utils import PrintManager, ReportGenerator

class ReportsWindow:
    def __init__(self, parent, db, user):
        self.parent = parent
        self.db = db
        self.user = user
        
        # إنشاء النافذة
        self.window = tk.Toplevel(parent)
        self.window.title("📊 التقارير والإحصائيات")
        self.window.geometry("1200x800")
        self.window.grab_set()
        
        # مدير الطباعة ومولد التقارير
        self.print_manager = PrintManager(self.window)
        self.report_generator = ReportGenerator(self.db)
        
        # المتغيرات
        self.setup_variables()
        
        # إنشاء الواجهة
        self.create_widgets()
        
        # تحديث الإحصائيات
        self.update_statistics()
    
    def setup_variables(self):
        self.from_date_var = tk.StringVar()
        self.to_date_var = tk.StringVar()
        self.report_type_var = tk.StringVar(value="المبيعات")
        
        # تعيين التواريخ الافتراضية (آخر 30 يوم)
        today = datetime.now()
        month_ago = today - timedelta(days=30)
        self.from_date_var.set(month_ago.strftime("%Y-%m-%d"))
        self.to_date_var.set(today.strftime("%Y-%m-%d"))
        
        # متغيرات الإحصائيات
        self.total_sales_var = tk.StringVar(value="0.00")
        self.total_purchases_var = tk.StringVar(value="0.00")
        self.profit_var = tk.StringVar(value="0.00")
        self.low_stock_count_var = tk.StringVar(value="0")
    
    def create_widgets(self):
        # الإطار الرئيسي
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # الجزء العلوي - فلاتر التقارير
        self.create_filters_frame(main_frame)
        
        # الجزء الأوسط - الإحصائيات السريعة
        self.create_statistics_frame(main_frame)
        
        # الجزء السفلي - عرض التقارير
        self.create_reports_frame(main_frame)
    
    def create_filters_frame(self, parent):
        filters_frame = ttk.LabelFrame(parent, text="فلاتر التقارير", padding="10")
        filters_frame.pack(fill=tk.X, pady=(0, 10))
        
        # الصف الأول - التواريخ
        dates_frame = ttk.Frame(filters_frame)
        dates_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(dates_frame, text="من تاريخ:").pack(side=tk.LEFT)
        from_date_entry = ttk.Entry(dates_frame, textvariable=self.from_date_var, width=12)
        from_date_entry.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(dates_frame, text="إلى تاريخ:").pack(side=tk.LEFT)
        to_date_entry = ttk.Entry(dates_frame, textvariable=self.to_date_var, width=12)
        to_date_entry.pack(side=tk.LEFT, padx=(5, 20))
        
        # نوع التقرير
        ttk.Label(dates_frame, text="نوع التقرير:").pack(side=tk.LEFT)
        report_combo = ttk.Combobox(dates_frame, textvariable=self.report_type_var,
                                   values=["المبيعات", "المشتريات", "المخزون", "الأرباح", 
                                          "أفضل المنتجات", "تحليل العملاء", "تقييم المخزون"],
                                   state="readonly", width=15)
        report_combo.pack(side=tk.LEFT, padx=(5, 20))
        
        # أزرار
        ttk.Button(dates_frame, text="عرض التقرير", 
                  command=self.generate_report).pack(side=tk.LEFT, padx=(20, 5))
        ttk.Button(dates_frame, text="تحديث الإحصائيات", 
                  command=self.update_statistics).pack(side=tk.LEFT)
    
    def create_statistics_frame(self, parent):
        stats_frame = ttk.LabelFrame(parent, text="الإحصائيات السريعة", padding="10")
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        # إنشاء شبكة الإحصائيات
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X)
        
        # إجمالي المبيعات
        sales_frame = ttk.Frame(stats_grid)
        sales_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        ttk.Label(sales_frame, text="إجمالي المبيعات", font=("Arial", 10)).pack()
        ttk.Label(sales_frame, textvariable=self.total_sales_var, 
                 font=("Arial", 14, "bold"), foreground="green").pack()
        
        # إجمالي المشتريات
        purchases_frame = ttk.Frame(stats_grid)
        purchases_frame.grid(row=0, column=1, padx=20, pady=10, sticky="ew")
        ttk.Label(purchases_frame, text="إجمالي المشتريات", font=("Arial", 10)).pack()
        ttk.Label(purchases_frame, textvariable=self.total_purchases_var, 
                 font=("Arial", 14, "bold"), foreground="red").pack()
        
        # الربح المتوقع
        profit_frame = ttk.Frame(stats_grid)
        profit_frame.grid(row=0, column=2, padx=20, pady=10, sticky="ew")
        ttk.Label(profit_frame, text="الربح المتوقع", font=("Arial", 10)).pack()
        ttk.Label(profit_frame, textvariable=self.profit_var, 
                 font=("Arial", 14, "bold"), foreground="blue").pack()
        
        # المنتجات قليلة المخزون
        low_stock_frame = ttk.Frame(stats_grid)
        low_stock_frame.grid(row=0, column=3, padx=20, pady=10, sticky="ew")
        ttk.Label(low_stock_frame, text="منتجات قليلة المخزون", font=("Arial", 10)).pack()
        ttk.Label(low_stock_frame, textvariable=self.low_stock_count_var, 
                 font=("Arial", 14, "bold"), foreground="orange").pack()
        
        # تكوين الشبكة
        for i in range(4):
            stats_grid.columnconfigure(i, weight=1)
    
    def create_reports_frame(self, parent):
        reports_frame = ttk.LabelFrame(parent, text="عرض التقارير", padding="10")
        reports_frame.pack(fill=tk.BOTH, expand=True)
        
        # جدول التقارير
        self.reports_tree = ttk.Treeview(reports_frame, show="headings", height=15)
        
        # شريط التمرير
        scrollbar_y = ttk.Scrollbar(reports_frame, orient=tk.VERTICAL, command=self.reports_tree.yview)
        scrollbar_x = ttk.Scrollbar(reports_frame, orient=tk.HORIZONTAL, command=self.reports_tree.xview)
        self.reports_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # تخطيط الجدول وأشرطة التمرير
        self.reports_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        # تكوين الشبكة
        reports_frame.grid_rowconfigure(0, weight=1)
        reports_frame.grid_columnconfigure(0, weight=1)
        
        # أزرار التقارير
        buttons_frame = ttk.Frame(reports_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        ttk.Button(buttons_frame, text="🖨️ طباعة التقرير", 
                  command=self.print_report).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="📊 تصدير إلى Excel", 
                  command=self.export_current_report).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="📈 عرض الرسم البياني", 
                  command=self.show_chart).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="💾 حفظ التقرير", 
                  command=self.save_report).pack(side=tk.LEFT)
    
    def update_statistics(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # إجمالي المبيعات
            cursor.execute("SELECT COALESCE(SUM(final_amount), 0) FROM sales")
            total_sales = cursor.fetchone()[0]
            self.total_sales_var.set(f"{total_sales:.2f}")
            
            # إجمالي المشتريات
            cursor.execute("SELECT COALESCE(SUM(final_amount), 0) FROM purchases")
            total_purchases = cursor.fetchone()[0]
            self.total_purchases_var.set(f"{total_purchases:.2f}")
            
            # الربح المتوقع (تقدير بسيط)
            profit = total_sales - total_purchases
            self.profit_var.set(f"{profit:.2f}")
            
            # المنتجات قليلة المخزون
            cursor.execute("SELECT COUNT(*) FROM products WHERE current_stock <= min_stock")
            low_stock_count = cursor.fetchone()[0]
            self.low_stock_count_var.set(str(low_stock_count))
            
        except Exception as e:
            print(f"خطأ في تحديث الإحصائيات: {e}")
        finally:
            conn.close()
    
    def generate_report(self):
        report_type = self.report_type_var.get()
        from_date = self.from_date_var.get()
        to_date = self.to_date_var.get()
        
        # مسح البيانات الحالية
        for item in self.reports_tree.get_children():
            self.reports_tree.delete(item)
        
        if report_type == "المبيعات":
            self.generate_sales_report(from_date, to_date)
        elif report_type == "المشتريات":
            self.generate_purchases_report(from_date, to_date)
        elif report_type == "المخزون":
            self.generate_inventory_report()
        elif report_type == "الأرباح":
            self.generate_profit_report(from_date, to_date)
        elif report_type == "أفضل المنتجات":
            self.generate_top_products_report(from_date, to_date)
        elif report_type == "تحليل العملاء":
            self.generate_customer_analysis_report(from_date, to_date)
        elif report_type == "تقييم المخزون":
            self.generate_inventory_valuation_report()
    
    def generate_sales_report(self, from_date, to_date):
        # تكوين أعمدة تقرير المبيعات
        columns = ("رقم الفاتورة", "التاريخ", "العميل", "المبلغ الإجمالي", "الخصم", "المبلغ النهائي")
        self.reports_tree["columns"] = columns
        
        for col in columns:
            self.reports_tree.heading(col, text=col)
            self.reports_tree.column(col, width=120, anchor=tk.CENTER)
        
        # جلب بيانات المبيعات
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.id, DATE(s.created_at), COALESCE(c.name, 'عميل عادي'), 
                   s.total_amount, s.discount, s.final_amount
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
            WHERE DATE(s.created_at) BETWEEN ? AND ?
            ORDER BY s.created_at DESC
        ''', (from_date, to_date))
        
        sales = cursor.fetchall()
        
        for sale in sales:
            self.reports_tree.insert('', tk.END, values=sale)
        
        conn.close()
    
    def generate_purchases_report(self, from_date, to_date):
        # تكوين أعمدة تقرير المشتريات
        columns = ("رقم الفاتورة", "التاريخ", "المورد", "المبلغ الإجمالي", "الخصم", "المبلغ النهائي", "حالة الدفع")
        self.reports_tree["columns"] = columns
        
        for col in columns:
            self.reports_tree.heading(col, text=col)
            self.reports_tree.column(col, width=120, anchor=tk.CENTER)
        
        # جلب بيانات المشتريات
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id, DATE(p.created_at), s.name, 
                   p.total_amount, p.discount, p.final_amount, p.payment_status
            FROM purchases p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE DATE(p.created_at) BETWEEN ? AND ?
            ORDER BY p.created_at DESC
        ''', (from_date, to_date))
        
        purchases = cursor.fetchall()
        
        for purchase in purchases:
            self.reports_tree.insert('', tk.END, values=purchase)
        
        conn.close()
    
    def generate_inventory_report(self):
        # تكوين أعمدة تقرير المخزون
        columns = ("اسم المنتج", "الباركود", "الفئة", "المخزون الحالي", "الحد الأدنى", "الحالة")
        self.reports_tree["columns"] = columns
        
        for col in columns:
            self.reports_tree.heading(col, text=col)
            self.reports_tree.column(col, width=120, anchor=tk.CENTER)
        
        # جلب بيانات المخزون
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.name, p.barcode, COALESCE(c.name, 'غير محدد'), 
                   p.current_stock, p.min_stock
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            ORDER BY p.name
        ''')
        
        products = cursor.fetchall()
        
        for product in products:
            status = "طبيعي"
            if product[3] <= product[4]:
                status = "قليل المخزون"
            if product[3] == 0:
                status = "نفد المخزون"
            
            values = list(product) + [status]
            self.reports_tree.insert('', tk.END, values=values)
        
        conn.close()
    
    def generate_profit_report(self, from_date, to_date):
        # تكوين أعمدة تقرير الأرباح
        columns = ("المنتج", "الكمية المباعة", "إجمالي المبيعات", "تكلفة البضاعة", "الربح")
        self.reports_tree["columns"] = columns
        
        for col in columns:
            self.reports_tree.heading(col, text=col)
            self.reports_tree.column(col, width=120, anchor=tk.CENTER)
        
        # جلب بيانات الأرباح
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.name, 
                   COALESCE(SUM(si.quantity), 0) as total_sold,
                   COALESCE(SUM(si.total_price), 0) as total_sales,
                   COALESCE(SUM(si.quantity * p.purchase_price), 0) as total_cost
            FROM products p
            LEFT JOIN sale_items si ON p.id = si.product_id
            LEFT JOIN sales s ON si.sale_id = s.id
            WHERE s.created_at IS NULL OR DATE(s.created_at) BETWEEN ? AND ?
            GROUP BY p.id, p.name
            HAVING total_sold > 0
            ORDER BY total_sales DESC
        ''', (from_date, to_date))
        
        profits = cursor.fetchall()
        
        for profit_data in profits:
            profit = profit_data[2] - profit_data[3]  # المبيعات - التكلفة
            values = list(profit_data) + [f"{profit:.2f}"]
            self.reports_tree.insert('', tk.END, values=values)
        
        conn.close()
    
    def generate_top_products_report(self, from_date, to_date):
        """تقرير أفضل المنتجات مبيعاً"""
        columns = ("المنتج", "الكمية المباعة", "إجمالي الإيرادات", "متوسط السعر", "عدد المعاملات")
        self.reports_tree["columns"] = columns
        
        for col in columns:
            self.reports_tree.heading(col, text=col)
            self.reports_tree.column(col, width=150, anchor=tk.CENTER)
        
        data = self.report_generator.generate_top_products_report(from_date, to_date)
        for row in data:
            formatted_row = (
                row[0],  # اسم المنتج
                f"{row[1]:.0f}",  # الكمية
                f"{row[2]:.2f}",  # الإيرادات
                f"{row[3]:.2f}",  # متوسط السعر
                f"{row[4]:.0f}"   # عدد المعاملات
            )
            self.reports_tree.insert('', tk.END, values=formatted_row)
    
    def generate_customer_analysis_report(self, from_date, to_date):
        """تقرير تحليل العملاء"""
        columns = ("العميل", "عدد المشتريات", "إجمالي الإنفاق", "متوسط الشراء", "آخر شراء")
        self.reports_tree["columns"] = columns
        
        for col in columns:
            self.reports_tree.heading(col, text=col)
            self.reports_tree.column(col, width=150, anchor=tk.CENTER)
        
        data = self.report_generator.generate_customer_analysis_report(from_date, to_date)
        for row in data:
            formatted_row = (
                row[0],  # اسم العميل
                f"{row[1]:.0f}",  # عدد المشتريات
                f"{row[2]:.2f}",  # إجمالي الإنفاق
                f"{row[3]:.2f}",  # متوسط الشراء
                row[4] or "غير محدد"  # آخر شراء
            )
            self.reports_tree.insert('', tk.END, values=formatted_row)
    
    def generate_inventory_valuation_report(self):
        """تقرير تقييم المخزون"""
        columns = ("المنتج", "المخزون", "سعر الشراء", "سعر البيع", "قيمة التكلفة", "قيمة البيع", "الربح المحتمل")
        self.reports_tree["columns"] = columns
        
        for col in columns:
            self.reports_tree.heading(col, text=col)
            self.reports_tree.column(col, width=120, anchor=tk.CENTER)
        
        data = self.report_generator.generate_inventory_valuation_report()
        for row in data:
            formatted_row = (
                row[0],  # اسم المنتج
                f"{row[1]:.0f}",  # المخزون
                f"{row[2]:.2f}",  # سعر الشراء
                f"{row[3]:.2f}",  # سعر البيع
                f"{row[4]:.2f}",  # قيمة التكلفة
                f"{row[5]:.2f}",  # قيمة البيع
                f"{row[6]:.2f}"   # الربح المحتمل
            )
            self.reports_tree.insert('', tk.END, values=formatted_row)
    
    def print_report(self):
        """طباعة التقرير الحالي"""
        if not self.reports_tree.get_children():
            messagebox.showwarning("تحذير", "لا توجد بيانات للطباعة")
            return
        
        # جمع بيانات التقرير
        report_data = []
        columns = self.reports_tree["columns"]
        
        # إضافة العناوين
        report_data.append(columns)
        
        # إضافة البيانات
        for item in self.reports_tree.get_children():
            values = self.reports_tree.item(item)["values"]
            report_data.append(values)
        
        # إنشاء محتوى التقرير
        content = []
        content.append("=" * 80)
        content.append(f"                    تقرير {self.report_type_var.get()}")
        content.append("=" * 80)
        content.append(f"الفترة: من {self.from_date_var.get()} إلى {self.to_date_var.get()}")
        content.append(f"تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        content.append("")
        
        # تنسيق البيانات
        if report_data:
            # حساب عرض الأعمدة
            col_widths = [max(len(str(row[i])) for row in report_data) + 2 for i in range(len(columns))]
            
            # طباعة العناوين
            header = " | ".join(str(columns[i]).ljust(col_widths[i]) for i in range(len(columns)))
            content.append(header)
            content.append("-" * len(header))
            
            # طباعة البيانات
            for row in report_data[1:]:  # تخطي العناوين
                row_str = " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row)))
                content.append(row_str)
        
        content.append("=" * 80)
        
        # طباعة التقرير
        try:
            temp_file = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(content))
            
            import os
            os.system(f'notepad /p {temp_file}')
            
            # حذف الملف المؤقت
            try:
                os.remove(temp_file)
            except:
                pass
                
            messagebox.showinfo("نجح", "تم إرسال التقرير للطابعة")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في طباعة التقرير: {str(e)}")
    
    def export_current_report(self):
        """تصدير التقرير الحالي"""
        if not self.reports_tree.get_children():
            messagebox.showwarning("تحذير", "لا توجد بيانات للتصدير")
            return
        
        # جمع بيانات التقرير
        report_data = []
        columns = self.reports_tree["columns"]
        
        # إضافة العناوين
        report_data.append(columns)
        
        # إضافة البيانات
        for item in self.reports_tree.get_children():
            values = self.reports_tree.item(item)["values"]
            report_data.append(values)
        
        # تصدير البيانات
        filename_prefix = f"{self.report_type_var.get()}_{self.from_date_var.get()}_to_{self.to_date_var.get()}"
        self.print_manager.export_to_excel(report_data, filename_prefix)
    
    def save_report(self):
        """حفظ التقرير"""
        if not self.reports_tree.get_children():
            messagebox.showwarning("تحذير", "لا توجد بيانات لحفظها")
            return
        
        try:
            from tkinter import filedialog
            import json
            
            # جمع بيانات التقرير
            report_data = {
                'report_type': self.report_type_var.get(),
                'from_date': self.from_date_var.get(),
                'to_date': self.to_date_var.get(),
                'generated_at': datetime.now().isoformat(),
                'columns': list(self.reports_tree["columns"]),
                'data': []
            }
            
            for item in self.reports_tree.get_children():
                values = self.reports_tree.item(item)["values"]
                report_data['data'].append(list(values))
            
            # حفظ التقرير
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="حفظ التقرير",
                initialvalue=f"report_{self.report_type_var.get()}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("نجح", f"تم حفظ التقرير: {filename}")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في حفظ التقرير: {str(e)}")
    
    def show_chart(self):
        """عرض الرسم البياني"""
        if not self.reports_tree.get_children():
            messagebox.showwarning("تحذير", "لا توجد بيانات لعرضها")
            return
        
        try:
            import matplotlib.pyplot as plt
            from matplotlib import font_manager
            import numpy as np
            
            # تكوين الخط العربي
            plt.rcParams['font.family'] = ['Arial Unicode MS', 'Tahoma', 'DejaVu Sans']
            
            # جمع البيانات للرسم البياني
            data = []
            labels = []
            
            for item in self.reports_tree.get_children():
                values = self.reports_tree.item(item)["values"]
                if len(values) >= 2:
                    labels.append(str(values[0])[:20])  # تقصير الأسماء الطويلة
                    try:
                        # محاولة تحويل القيمة الثانية إلى رقم
                        numeric_value = float(str(values[1]).replace(',', ''))
                        data.append(numeric_value)
                    except:
                        data.append(0)
            
            if not data:
                messagebox.showwarning("تحذير", "لا توجد بيانات رقمية للرسم البياني")
                return
            
            # إنشاء الرسم البياني
            fig, ax = plt.subplots(figsize=(12, 8))
            
            if self.report_type_var.get() in ["المبيعات", "المشتريات", "الأرباح"]:
                # رسم بياني خطي للبيانات الزمنية
                ax.plot(labels, data, marker='o', linewidth=2, markersize=6)
                ax.set_title(f"تقرير {self.report_type_var.get()}", fontsize=16, fontweight='bold')
                plt.xticks(rotation=45)
            else:
                # رسم بياني عمودي للبيانات الأخرى
                bars = ax.bar(labels, data, color='skyblue', alpha=0.7)
                ax.set_title(f"تقرير {self.report_type_var.get()}", fontsize=16, fontweight='bold')
                plt.xticks(rotation=45)
                
                # إضافة القيم على الأعمدة
                for bar, value in zip(bars, data):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{value:.1f}', ha='center', va='bottom')
            
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()
            
        except ImportError:
            messagebox.showerror("خطأ", "مكتبة matplotlib غير مثبتة\nيرجى تثبيتها باستخدام: pip install matplotlib")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في إنشاء الرسم البياني: {str(e)}")