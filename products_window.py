import tkinter as tk
from tkinter import ttk, messagebox
from category_window import CategoryWindow

class ProductsWindow:
    def __init__(self, parent, db, user):
        self.parent = parent
        self.db = db
        self.user = user
        
        # إنشاء النافذة
        self.window = tk.Toplevel(parent)
        self.window.title("🏷️ إدارة المنتجات")
        self.window.geometry("1200x700")
        self.window.grab_set()  # جعل النافذة modal
        
        # المتغيرات
        self.setup_variables()
        
        # إنشاء الواجهة
        self.create_widgets()
        
        # تحميل البيانات
        self.load_categories()
        self.load_products()
    
    def setup_variables(self):
        self.name_var = tk.StringVar()
        self.barcode_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.unit_var = tk.StringVar()
        self.purchase_price_var = tk.StringVar()
        self.selling_price_var = tk.StringVar()
        self.min_stock_var = tk.StringVar()
        self.description_var = tk.StringVar()
        self.search_var = tk.StringVar()
        
        # متغير لتتبع المنتج المحدد للتعديل
        self.selected_product_id = None
    
    def create_widgets(self):
        # الإطار الرئيسي
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # إطار الإدخال
        self.create_input_frame(main_frame)
        
        # إطار البحث والعرض
        self.create_display_frame(main_frame)
    
    def create_input_frame(self, parent):
        input_frame = ttk.LabelFrame(parent, text="بيانات المنتج", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # الصف الأول
        row1 = ttk.Frame(input_frame)
        row1.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(row1, text="اسم المنتج:").pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.name_var, width=20).pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(row1, text="الباركود:").pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.barcode_var, width=15).pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(row1, text="الفئة:").pack(side=tk.LEFT)
        self.category_combo = ttk.Combobox(row1, textvariable=self.category_var, width=15, state="readonly")
        self.category_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # الصف الثاني
        row2 = ttk.Frame(input_frame)
        row2.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(row2, text="الوحدة:").pack(side=tk.LEFT)
        unit_combo = ttk.Combobox(row2, textvariable=self.unit_var, width=10, 
                                 values=["قطعة", "كيلو", "لتر", "متر", "علبة", "كرتون"])
        unit_combo.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(row2, text="سعر الشراء:").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.purchase_price_var, width=10).pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(row2, text="سعر البيع:").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.selling_price_var, width=10).pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(row2, text="الحد الأدنى:").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.min_stock_var, width=10).pack(side=tk.LEFT, padx=(5, 0))
        
        # الصف الثالث
        row3 = ttk.Frame(input_frame)
        row3.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(row3, text="الوصف:").pack(side=tk.LEFT)
        ttk.Entry(row3, textvariable=self.description_var, width=50).pack(side=tk.LEFT, padx=(5, 0))
        
        # أزرار العمليات
        buttons_frame = ttk.Frame(input_frame)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(buttons_frame, text="➕ إضافة", command=self.add_product).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="✏️ تعديل", command=self.update_product).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="🗑️ حذف", command=self.delete_product).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="🔄 مسح", command=self.clear_fields).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="📊 تقرير المنتج", command=self.show_product_report).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="📁 إدارة الفئات", command=self.manage_categories).pack(side=tk.RIGHT)
    
    def create_display_frame(self, parent):
        display_frame = ttk.LabelFrame(parent, text="قائمة المنتجات", padding="10")
        display_frame.pack(fill=tk.BOTH, expand=True)
        
        # إطار البحث
        search_frame = ttk.Frame(display_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="البحث:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(5, 10))
        search_entry.bind('<KeyRelease>', self.search_products)
        
        ttk.Button(search_frame, text="🔍 بحث متقدم", command=self.advanced_search).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(search_frame, text="🔄 تحديث", command=self.load_products).pack(side=tk.LEFT)
        
        # جدول المنتجات
        columns = ("ID", "الاسم", "الباركود", "الفئة", "الوحدة", "سعر الشراء", "سعر البيع", "المخزون", "الحد الأدنى")
        self.tree = ttk.Treeview(display_frame, columns=columns, show="headings", height=15)
        
        # تكوين الأعمدة
        column_widths = [50, 150, 100, 100, 80, 100, 100, 80, 80]
        for i, (col, width) in enumerate(zip(columns, column_widths)):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=tk.CENTER)
        
        # شريط التمرير
        scrollbar = ttk.Scrollbar(display_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # تخطيط الجدول وشريط التمرير
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ربط النقر المزدوج بالتعديل
        self.tree.bind('<Double-1>', self.on_item_select)
    
    def load_categories(self):
        categories = self.db.get_categories()
        category_values = [f"{cat[0]} - {cat[1]}" for cat in categories]
        self.category_combo['values'] = category_values
    
    def load_products(self):
        # مسح البيانات الحالية
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # تحميل المنتجات
        products = self.db.get_products()
        for product in products:
            # تلوين المنتجات قليلة المخزون
            tags = ()
            if product[7] <= product[8]:  # المخزون الحالي <= الحد الأدنى
                tags = ('low_stock',)
            
            self.tree.insert('', tk.END, values=product, tags=tags)
        
        # تكوين الألوان
        self.tree.tag_configure('low_stock', background='#ffcccc')
    
    def search_products(self, event=None):
        search_term = self.search_var.get().lower()
        
        # مسح البيانات الحالية
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # تحميل وتصفية المنتجات
        products = self.db.get_products()
        for product in products:
            if (search_term in str(product[1]).lower() or  # الاسم
                search_term in str(product[2]).lower() or  # الباركود
                search_term in str(product[3]).lower()):   # الفئة
                
                tags = ()
                if product[7] <= product[8]:
                    tags = ('low_stock',)
                
                self.tree.insert('', tk.END, values=product, tags=tags)
        
        self.tree.tag_configure('low_stock', background='#ffcccc')
    
    def add_product(self):
        if not self.validate_input():
            return
        
        # استخراج معرف الفئة
        category_text = self.category_var.get()
        if not category_text:
            messagebox.showerror("خطأ", "يرجى اختيار الفئة")
            return
        
        category_id = int(category_text.split(' - ')[0])
        
        # إضافة المنتج
        success = self.db.add_product(
            self.name_var.get(),
            self.barcode_var.get(),
            category_id,
            self.unit_var.get(),
            float(self.purchase_price_var.get()),
            float(self.selling_price_var.get()),
            int(self.min_stock_var.get()),
            self.description_var.get()
        )
        
        if success:
            messagebox.showinfo("نجح", "تم إضافة المنتج بنجاح")
            self.clear_fields()
            self.load_products()
        else:
            messagebox.showerror("خطأ", "فشل في إضافة المنتج (ربما الباركود مكرر)")
    
    def update_product(self):
        if not self.selected_product_id:
            messagebox.showerror("خطأ", "يرجى اختيار منتج للتعديل")
            return
        
        if not self.validate_input():
            return
        
        # سيتم تنفيذ التحديث لاحقاً
        messagebox.showinfo("قريباً", "وظيفة التعديل ستكون متاحة قريباً")
    
    def delete_product(self):
        if not self.selected_product_id:
            messagebox.showerror("خطأ", "يرجى اختيار منتج للحذف")
            return
        
        if messagebox.askyesno("تأكيد", "هل تريد حذف هذا المنتج؟"):
            # سيتم تنفيذ الحذف لاحقاً
            messagebox.showinfo("قريباً", "وظيفة الحذف ستكون متاحة قريباً")
    
    def on_item_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            
            self.selected_product_id = values[0]
            self.name_var.set(values[1])
            self.barcode_var.set(values[2])
            self.category_var.set(f"{values[0]} - {values[3]}")  # سيحتاج تعديل
            self.unit_var.set(values[4])
            self.purchase_price_var.set(values[5])
            self.selling_price_var.set(values[6])
            self.min_stock_var.set(values[8])
    
    def validate_input(self):
        if not self.name_var.get().strip():
            messagebox.showerror("خطأ", "يرجى إدخال اسم المنتج")
            return False
        
        if not self.unit_var.get().strip():
            messagebox.showerror("خطأ", "يرجى اختيار الوحدة")
            return False
        
        try:
            float(self.purchase_price_var.get())
            float(self.selling_price_var.get())
            int(self.min_stock_var.get())
        except ValueError:
            messagebox.showerror("خطأ", "يرجى إدخال قيم صحيحة للأسعار والكمية")
            return False
        
        return True
    
    def clear_fields(self):
        self.selected_product_id = None
        self.name_var.set("")
        self.barcode_var.set("")
        self.category_var.set("")
        self.unit_var.set("")
        self.purchase_price_var.set("")
        self.selling_price_var.set("")
        self.min_stock_var.set("")
        self.description_var.set("")
    
    def manage_categories(self):
        CategoryWindow(self.window, self.db, self.load_categories)
    
    def advanced_search(self):
        """البحث المتقدم"""
        search_window = tk.Toplevel(self.window)
        search_window.title("🔍 البحث المتقدم")
        search_window.geometry("400x300")
        search_window.grab_set()
        search_window.transient(self.window)
        
        frame = ttk.Frame(search_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # متغيرات البحث
        name_var = tk.StringVar()
        category_var = tk.StringVar()
        min_stock_var = tk.StringVar()
        max_stock_var = tk.StringVar()
        min_price_var = tk.StringVar()
        max_price_var = tk.StringVar()
        
        # حقول البحث
        ttk.Label(frame, text="اسم المنتج:").pack(anchor=tk.W)
        ttk.Entry(frame, textvariable=name_var).pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="الفئة:").pack(anchor=tk.W)
        category_combo = ttk.Combobox(frame, textvariable=category_var, state="readonly")
        categories = ["جميع الفئات"] + [cat[1] for cat in self.db.get_categories()]
        category_combo['values'] = categories
        category_combo.set("جميع الفئات")
        category_combo.pack(fill=tk.X, pady=(0, 10))
        
        # نطاق المخزون
        stock_frame = ttk.LabelFrame(frame, text="نطاق المخزون", padding="10")
        stock_frame.pack(fill=tk.X, pady=(0, 10))
        
        stock_row = ttk.Frame(stock_frame)
        stock_row.pack(fill=tk.X)
        ttk.Label(stock_row, text="من:").pack(side=tk.LEFT)
        ttk.Entry(stock_row, textvariable=min_stock_var, width=10).pack(side=tk.LEFT, padx=(5, 10))
        ttk.Label(stock_row, text="إلى:").pack(side=tk.LEFT)
        ttk.Entry(stock_row, textvariable=max_stock_var, width=10).pack(side=tk.LEFT, padx=(5, 0))
        
        # نطاق السعر
        price_frame = ttk.LabelFrame(frame, text="نطاق سعر البيع", padding="10")
        price_frame.pack(fill=tk.X, pady=(0, 10))
        
        price_row = ttk.Frame(price_frame)
        price_row.pack(fill=tk.X)
        ttk.Label(price_row, text="من:").pack(side=tk.LEFT)
        ttk.Entry(price_row, textvariable=min_price_var, width=10).pack(side=tk.LEFT, padx=(5, 10))
        ttk.Label(price_row, text="إلى:").pack(side=tk.LEFT)
        ttk.Entry(price_row, textvariable=max_price_var, width=10).pack(side=tk.LEFT, padx=(5, 0))
        
        # أزرار
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        def perform_search():
            self.perform_advanced_search(name_var.get(), category_var.get(), 
                                       min_stock_var.get(), max_stock_var.get(),
                                       min_price_var.get(), max_price_var.get())
            search_window.destroy()
        
        ttk.Button(buttons_frame, text="🔍 بحث", command=perform_search).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(buttons_frame, text="❌ إلغاء", command=search_window.destroy).pack(side=tk.RIGHT)
    
    def perform_advanced_search(self, name, category, min_stock, max_stock, min_price, max_price):
        """تنفيذ البحث المتقدم"""
        # مسح البيانات الحالية
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # بناء استعلام البحث
        query = '''
            SELECT p.id, p.name, p.barcode, c.name, p.unit, p.purchase_price, 
                   p.selling_price, p.current_stock, p.min_stock
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE 1=1
        '''
        params = []
        
        if name:
            query += " AND p.name LIKE ?"
            params.append(f"%{name}%")
        
        if category and category != "جميع الفئات":
            query += " AND c.name = ?"
            params.append(category)
        
        if min_stock:
            query += " AND p.current_stock >= ?"
            params.append(int(min_stock))
        
        if max_stock:
            query += " AND p.current_stock <= ?"
            params.append(int(max_stock))
        
        if min_price:
            query += " AND p.selling_price >= ?"
            params.append(float(min_price))
        
        if max_price:
            query += " AND p.selling_price <= ?"
            params.append(float(max_price))
        
        query += " ORDER BY p.name"
        
        # تنفيذ البحث
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        products = cursor.fetchall()
        conn.close()
        
        # عرض النتائج
        for product in products:
            tags = ()
            if product[7] <= product[8]:  # المخزون الحالي <= الحد الأدنى
                tags = ('low_stock',)
            
            self.tree.insert('', tk.END, values=product, tags=tags)
        
        self.tree.tag_configure('low_stock', background='#ffcccc')
    
    def show_product_report(self):
        """عرض تقرير المنتج المحدد"""
        if not self.selected_product_id:
            messagebox.showwarning("تحذير", "يرجى اختيار منتج لعرض التقرير")
            return
        
        # إنشاء نافذة التقرير
        report_window = tk.Toplevel(self.window)
        report_window.title("📊 تقرير المنتج")
        report_window.geometry("600x500")
        report_window.grab_set()
        report_window.transient(self.window)
        
        frame = ttk.Frame(report_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # جلب بيانات المنتج
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # بيانات المنتج الأساسية
        cursor.execute('''
            SELECT p.name, p.barcode, c.name, p.unit, p.purchase_price, 
                   p.selling_price, p.current_stock, p.min_stock, p.description
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = ?
        ''', (self.selected_product_id,))
        
        product_data = cursor.fetchone()
        
        if not product_data:
            messagebox.showerror("خطأ", "لم يتم العثور على المنتج")
            report_window.destroy()
            return
        
        # إحصائيات المبيعات
        cursor.execute('''
            SELECT COUNT(*), SUM(si.quantity), SUM(si.total_price)
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE si.product_id = ?
        ''', (self.selected_product_id,))
        
        sales_stats = cursor.fetchone()
        
        # إحصائيات المشتريات
        cursor.execute('''
            SELECT COUNT(*), SUM(pi.quantity), SUM(pi.total_price)
            FROM purchase_items pi
            JOIN purchases p ON pi.purchase_id = p.id
            WHERE pi.product_id = ?
        ''', (self.selected_product_id,))
        
        purchase_stats = cursor.fetchone()
        
        conn.close()
        
        # عرض البيانات
        ttk.Label(frame, text=f"تقرير المنتج: {product_data[0]}", 
                 font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # معلومات أساسية
        info_frame = ttk.LabelFrame(frame, text="المعلومات الأساسية", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_text = f"""
الباركود: {product_data[1] or 'غير محدد'}
الفئة: {product_data[2] or 'غير محدد'}
الوحدة: {product_data[3]}
سعر الشراء: {product_data[4]:.2f}
سعر البيع: {product_data[5]:.2f}
المخزون الحالي: {product_data[6]}
الحد الأدنى: {product_data[7]}
الوصف: {product_data[8] or 'غير محدد'}
        """
        
        ttk.Label(info_frame, text=info_text.strip(), justify=tk.LEFT).pack(anchor=tk.W)
        
        # إحصائيات المبيعات
        sales_frame = ttk.LabelFrame(frame, text="إحصائيات المبيعات", padding="10")
        sales_frame.pack(fill=tk.X, pady=(0, 10))
        
        sales_text = f"""
عدد فواتير البيع: {sales_stats[0] or 0}
إجمالي الكمية المباعة: {sales_stats[1] or 0}
إجمالي قيمة المبيعات: {sales_stats[2] or 0:.2f}
        """
        
        ttk.Label(sales_frame, text=sales_text.strip(), justify=tk.LEFT).pack(anchor=tk.W)
        
        # إحصائيات المشتريات
        purchase_frame = ttk.LabelFrame(frame, text="إحصائيات المشتريات", padding="10")
        purchase_frame.pack(fill=tk.X, pady=(0, 10))
        
        purchase_text = f"""
عدد فواتير الشراء: {purchase_stats[0] or 0}
إجمالي الكمية المشتراة: {purchase_stats[1] or 0}
إجمالي قيمة المشتريات: {purchase_stats[2] or 0:.2f}
        """
        
        ttk.Label(purchase_frame, text=purchase_text.strip(), justify=tk.LEFT).pack(anchor=tk.W)
        
        # حساب الربح المحتمل
        potential_profit = (product_data[6] * product_data[5]) - (product_data[6] * product_data[4])
        
        profit_frame = ttk.LabelFrame(frame, text="تحليل الربحية", padding="10")
        profit_frame.pack(fill=tk.X, pady=(0, 10))
        
        profit_text = f"""
قيمة المخزون (بسعر الشراء): {product_data[6] * product_data[4]:.2f}
قيمة المخزون (بسعر البيع): {product_data[6] * product_data[5]:.2f}
الربح المحتمل: {potential_profit:.2f}
هامش الربح: {((product_data[5] - product_data[4]) / product_data[4] * 100):.1f}%
        """
        
        ttk.Label(profit_frame, text=profit_text.strip(), justify=tk.LEFT).pack(anchor=tk.W)
        
        # زر الإغلاق
        ttk.Button(frame, text="❌ إغلاق", command=report_window.destroy).pack(pady=(10, 0))