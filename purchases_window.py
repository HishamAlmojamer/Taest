import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from print_utils import PrintManager

class PurchasesWindow:
    def __init__(self, parent, db, user):
        self.parent = parent
        self.db = db
        self.user = user
        
        # إنشاء النافذة
        self.window = tk.Toplevel(parent)
        self.window.title("📦 إدارة المشتريات")
        self.window.geometry("1200x700")
        self.window.grab_set()
        
        # مدير الطباعة
        self.print_manager = PrintManager(self.window)
        
        # المتغيرات
        self.setup_variables()
        
        # إنشاء الواجهة
        self.create_widgets()
        
        # تحميل البيانات
        self.load_suppliers()
        self.load_products()
    
    def setup_variables(self):
        self.supplier_var = tk.StringVar()
        self.product_search_var = tk.StringVar()
        self.discount_var = tk.StringVar(value="0")
        self.payment_status_var = tk.StringVar(value="مدفوع")
        self.notes_var = tk.StringVar()
        
        # متغيرات الإجماليات
        self.subtotal_var = tk.StringVar(value="0.00")
        self.discount_amount_var = tk.StringVar(value="0.00")
        self.total_var = tk.StringVar(value="0.00")
        
        # قائمة عناصر فاتورة الشراء
        self.purchase_items = []
    
    def create_widgets(self):
        # الإطار الرئيسي
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # الجزء العلوي - المورد والبحث
        self.create_top_frame(main_frame)
        
        # الجزء الأوسط - المنتجات وفاتورة الشراء
        self.create_middle_frame(main_frame)
        
        # الجزء السفلي - الإجماليات والدفع
        self.create_bottom_frame(main_frame)
    
    def create_top_frame(self, parent):
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # المورد
        supplier_frame = ttk.LabelFrame(top_frame, text="المورد", padding="10")
        supplier_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Label(supplier_frame, text="اختر المورد:").pack(anchor=tk.W)
        self.supplier_combo = ttk.Combobox(supplier_frame, textvariable=self.supplier_var,
                                          width=25, state="readonly")
        self.supplier_combo.pack(pady=(5, 0))
        
        # البحث عن المنتجات
        search_frame = ttk.LabelFrame(top_frame, text="البحث عن المنتج", padding="10")
        search_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        ttk.Label(search_frame, text="اسم المنتج أو الباركود:").pack(anchor=tk.W)
        search_entry = ttk.Entry(search_frame, textvariable=self.product_search_var, font=("Arial", 12))
        search_entry.pack(fill=tk.X, pady=(5, 0))
        search_entry.bind('<KeyRelease>', self.search_products)
    
    def create_middle_frame(self, parent):
        middle_frame = ttk.Frame(parent)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # قائمة المنتجات
        products_frame = ttk.LabelFrame(middle_frame, text="المنتجات", padding="10")
        products_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # جدول المنتجات
        products_columns = ("ID", "الاسم", "الباركود", "سعر الشراء", "المخزون الحالي")
        self.products_tree = ttk.Treeview(products_frame, columns=products_columns,
                                         show="headings", height=15)
        
        for col in products_columns:
            self.products_tree.heading(col, text=col)
            self.products_tree.column(col, width=120, anchor=tk.CENTER)
        
        products_scrollbar = ttk.Scrollbar(products_frame, orient=tk.VERTICAL,
                                          command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=products_scrollbar.set)
        
        self.products_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        products_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ربط النقر المزدوج بإضافة المنتج
        self.products_tree.bind('<Double-1>', self.add_selected_product)
        
        # فاتورة الشراء
        purchase_frame = ttk.LabelFrame(middle_frame, text="فاتورة الشراء", padding="10")
        purchase_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # جدول الفاتورة
        purchase_columns = ("المنتج", "الكمية", "سعر الوحدة", "الإجمالي")
        self.purchase_tree = ttk.Treeview(purchase_frame, columns=purchase_columns,
                                         show="headings", height=15)
        
        for col in purchase_columns:
            self.purchase_tree.heading(col, text=col)
            self.purchase_tree.column(col, width=120, anchor=tk.CENTER)
        
        purchase_scrollbar = ttk.Scrollbar(purchase_frame, orient=tk.VERTICAL,
                                          command=self.purchase_tree.yview)
        self.purchase_tree.configure(yscrollcommand=purchase_scrollbar.set)
        
        self.purchase_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        purchase_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # أزرار إدارة الفاتورة
        purchase_buttons = ttk.Frame(purchase_frame)
        purchase_buttons.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(purchase_buttons, text="تعديل الكمية",
                  command=self.edit_quantity).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(purchase_buttons, text="حذف العنصر",
                  command=self.remove_item).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(purchase_buttons, text="مسح الفاتورة",
                  command=self.clear_purchase).pack(side=tk.LEFT)
    
    def create_bottom_frame(self, parent):
        bottom_frame = ttk.Frame(parent)
        bottom_frame.pack(fill=tk.X)
        
        # الإجماليات
        totals_frame = ttk.LabelFrame(bottom_frame, text="الإجماليات", padding="10")
        totals_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Label(totals_frame, text="المجموع الفرعي:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(totals_frame, textvariable=self.subtotal_var,
                 font=("Arial", 12, "bold")).grid(row=0, column=1, sticky=tk.E, pady=2)
        
        ttk.Label(totals_frame, text="الخصم:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(totals_frame, textvariable=self.discount_var, width=10,
                 validate="key", validatecommand=(self.window.register(self.validate_number), '%P')).grid(row=1, column=1, pady=2)
        
        ttk.Label(totals_frame, text="قيمة الخصم:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(totals_frame, textvariable=self.discount_amount_var,
                 font=("Arial", 10)).grid(row=2, column=1, sticky=tk.E, pady=2)
        
        ttk.Label(totals_frame, text="الإجمالي:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Label(totals_frame, textvariable=self.total_var,
                 font=("Arial", 14, "bold"), foreground="blue").grid(row=3, column=1, sticky=tk.E, pady=2)
        
        # ربط تغيير الخصم بإعادة الحساب
        self.discount_var.trace('w', self.calculate_totals)
        
        # حالة الدفع والملاحظات
        payment_frame = ttk.LabelFrame(bottom_frame, text="حالة الدفع والملاحظات", padding="10")
        payment_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # حالة الدفع
        payment_status_frame = ttk.Frame(payment_frame)
        payment_status_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(payment_status_frame, text="حالة الدفع:").pack(side=tk.LEFT)
        payment_combo = ttk.Combobox(payment_status_frame, textvariable=self.payment_status_var,
                                    values=["مدفوع", "غير مدفوع", "مدفوع جزئياً"],
                                    state="readonly", width=15)
        payment_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # الملاحظات
        ttk.Label(payment_frame, text="ملاحظات:").pack(anchor=tk.W)
        ttk.Entry(payment_frame, textvariable=self.notes_var, width=50).pack(fill=tk.X, pady=(5, 10))
        
        # أزرار العمليات
        buttons_frame = ttk.Frame(payment_frame)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(buttons_frame, text="حفظ الفاتورة", command=self.save_purchase,
                  style="Accent.TButton").pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(buttons_frame, text="طباعة", command=self.print_purchase).pack(side=tk.RIGHT)
    
    def load_suppliers(self):
        suppliers = self.db.get_suppliers()
        supplier_values = [f"{supplier[0]} - {supplier[1]}" for supplier in suppliers]
        self.supplier_combo['values'] = supplier_values
    
    def load_products(self):
        products = self.db.get_products()
        
        # مسح البيانات الحالية
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        # إضافة المنتجات
        for product in products:
            self.products_tree.insert('', tk.END, values=(
                product[0], product[1], product[2], product[4], product[7]
            ))
    
    def search_products(self, event=None):
        search_term = self.product_search_var.get().lower()
        
        # مسح البيانات الحالية
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        # تحميل وتصفية المنتجات
        products = self.db.get_products()
        for product in products:
            if (search_term in str(product[1]).lower() or  # الاسم
                search_term in str(product[2]).lower()):   # الباركود
                
                self.products_tree.insert('', tk.END, values=(
                    product[0], product[1], product[2], product[4], product[7]
                ))
    
    def add_selected_product(self, event):
        selection = self.products_tree.selection()
        if selection:
            item = self.products_tree.item(selection[0])
            values = item['values']
            self.show_quantity_dialog(values[0], values[1], values[3])
    
    def show_quantity_dialog(self, product_id, product_name, unit_price):
        # نافذة إدخال الكمية والسعر
        dialog = tk.Toplevel(self.window)
        dialog.title("إضافة منتج")
        dialog.geometry("300x200")
        dialog.grab_set()
        dialog.transient(self.window)
        
        # توسيط النافذة
        dialog.geometry("+%d+%d" % (self.window.winfo_rootx() + 50, self.window.winfo_rooty() + 50))
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"المنتج: {product_name}").pack(pady=(0, 10))
        
        # الكمية
        ttk.Label(frame, text="الكمية:").pack(anchor=tk.W)
        quantity_var = tk.StringVar(value="1")
        quantity_entry = ttk.Entry(frame, textvariable=quantity_var)
        quantity_entry.pack(fill=tk.X, pady=(5, 10))
        quantity_entry.focus()
        
        # سعر الوحدة
        ttk.Label(frame, text="سعر الوحدة:").pack(anchor=tk.W)
        price_var = tk.StringVar(value=str(unit_price))
        price_entry = ttk.Entry(frame, textvariable=price_var)
        price_entry.pack(fill=tk.X, pady=(5, 10))
        
        # الأزرار
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        def add_item():
            try:
                quantity = int(quantity_var.get())
                price = float(price_var.get())
                
                if quantity <= 0 or price < 0:
                    messagebox.showerror("خطأ", "يرجى إدخال قيم صحيحة")
                    return
                
                self.add_item_to_purchase(product_id, product_name, quantity, price)
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("خطأ", "يرجى إدخال قيم صحيحة")
        
        ttk.Button(buttons_frame, text="إضافة", command=add_item).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(buttons_frame, text="إلغاء", command=dialog.destroy).pack(side=tk.RIGHT)
        
        # ربط مفتاح Enter بالإضافة
        dialog.bind('<Return>', lambda e: add_item())
    
    def add_item_to_purchase(self, product_id, product_name, quantity, price):
        # التحقق من وجود المنتج في الفاتورة
        for i, item in enumerate(self.purchase_items):
            if item['product_id'] == product_id:
                self.purchase_items[i]['quantity'] += quantity
                self.purchase_items[i]['total'] = self.purchase_items[i]['quantity'] * self.purchase_items[i]['price']
                self.refresh_purchase_display()
                self.calculate_totals()
                return
        
        # إضافة منتج جديد
        self.purchase_items.append({
            'product_id': product_id,
            'product_name': product_name,
            'quantity': quantity,
            'price': price,
            'total': quantity * price
        })
        
        self.refresh_purchase_display()
        self.calculate_totals()
    
    def refresh_purchase_display(self):
        # مسح البيانات الحالية
        for item in self.purchase_tree.get_children():
            self.purchase_tree.delete(item)
        
        # إضافة العناصر
        for item in self.purchase_items:
            self.purchase_tree.insert('', tk.END, values=(
                item['product_name'],
                item['quantity'],
                f"{item['price']:.2f}",
                f"{item['total']:.2f}"
            ))
    
    def calculate_totals(self, *args):
        subtotal = sum(item['total'] for item in self.purchase_items)
        
        try:
            discount_percent = float(self.discount_var.get() or 0)
        except ValueError:
            discount_percent = 0
        
        discount_amount = subtotal * (discount_percent / 100)
        total = subtotal - discount_amount
        
        self.subtotal_var.set(f"{subtotal:.2f}")
        self.discount_amount_var.set(f"{discount_amount:.2f}")
        self.total_var.set(f"{total:.2f}")
    
    def edit_quantity(self):
        selection = self.purchase_tree.selection()
        if not selection:
            messagebox.showwarning("تحذير", "يرجى اختيار عنصر للتعديل")
            return
        
        index = self.purchase_tree.index(selection[0])
        item = self.purchase_items[index]
        
        # نافذة تعديل الكمية
        dialog = tk.Toplevel(self.window)
        dialog.title("تعديل الكمية")
        dialog.geometry("250x150")
        dialog.grab_set()
        dialog.transient(self.window)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"المنتج: {item['product_name']}").pack(pady=(0, 10))
        
        ttk.Label(frame, text="الكمية الجديدة:").pack(anchor=tk.W)
        quantity_var = tk.StringVar(value=str(item['quantity']))
        quantity_entry = ttk.Entry(frame, textvariable=quantity_var)
        quantity_entry.pack(fill=tk.X, pady=(5, 10))
        quantity_entry.focus()
        quantity_entry.select_range(0, tk.END)
        
        def update_quantity():
            try:
                new_quantity = int(quantity_var.get())
                if new_quantity <= 0:
                    messagebox.showerror("خطأ", "يرجى إدخال كمية صحيحة")
                    return
                
                self.purchase_items[index]['quantity'] = new_quantity
                self.purchase_items[index]['total'] = new_quantity * item['price']
                self.refresh_purchase_display()
                self.calculate_totals()
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("خطأ", "يرجى إدخال كمية صحيحة")
        
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(buttons_frame, text="تحديث", command=update_quantity).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(buttons_frame, text="إلغاء", command=dialog.destroy).pack(side=tk.RIGHT)
        
        dialog.bind('<Return>', lambda e: update_quantity())
    
    def remove_item(self):
        selection = self.purchase_tree.selection()
        if selection:
            if messagebox.askyesno("تأكيد", "هل تريد حذف هذا العنصر؟"):
                index = self.purchase_tree.index(selection[0])
                del self.purchase_items[index]
                self.refresh_purchase_display()
                self.calculate_totals()
    
    def clear_purchase(self):
        if messagebox.askyesno("تأكيد", "هل تريد مسح فاتورة الشراء؟"):
            self.purchase_items.clear()
            self.refresh_purchase_display()
            self.calculate_totals()
    
    def save_purchase(self):
        if not self.purchase_items:
            messagebox.showwarning("تحذير", "لا توجد عناصر في فاتورة الشراء")
            return
        
        if not self.supplier_var.get():
            messagebox.showwarning("تحذير", "يرجى اختيار المورد")
            return
        
        try:
            # حفظ الفاتورة في قاعدة البيانات
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # استخراج معرف المورد
            supplier_text = self.supplier_var.get()
            supplier_id = int(supplier_text.split(' - ')[0])
            
            # حساب الإجماليات
            subtotal = sum(item['total'] for item in self.purchase_items)
            discount_percent = float(self.discount_var.get() or 0)
            discount_amount = subtotal * (discount_percent / 100)
            final_amount = subtotal - discount_amount
            
            # إدراج فاتورة الشراء
            cursor.execute('''
                INSERT INTO purchases (supplier_id, total_amount, discount, final_amount,
                                     payment_status, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (supplier_id, subtotal, discount_amount, final_amount,
                  self.payment_status_var.get(), self.notes_var.get(), self.user['id']))
            
            purchase_id = cursor.lastrowid
            
            # إدراج عناصر الفاتورة وتحديث المخزون
            for item in self.purchase_items:
                # إدراج العنصر
                cursor.execute('''
                    INSERT INTO purchase_items (purchase_id, product_id, quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?)
                ''', (purchase_id, item['product_id'], item['quantity'],
                      item['price'], item['total']))
                
                # تحديث المخزون
                self.db.update_stock(item['product_id'], item['quantity'], 'in',
                                   'purchase', purchase_id, self.user['id'])
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("نجح", f"تم حفظ فاتورة الشراء بنجاح\nرقم الفاتورة: {purchase_id}")
            
            # مسح الفاتورة
            self.clear_purchase()
            self.load_products()  # تحديث قائمة المنتجات
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في حفظ فاتورة الشراء: {str(e)}")
    
    def print_purchase(self):
        messagebox.showinfo("قريباً", "وظيفة الطباعة ستكون متاحة قريباً")
    
    def validate_number(self, value):
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False