import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from print_utils import PrintManager

class SalesWindow:
    def __init__(self, parent, db, user):
        self.parent = parent
        self.db = db
        self.user = user
        
        # إنشاء النافذة
        self.window = tk.Toplevel(parent)
        self.window.title("💰 نقطة البيع")
        self.window.geometry("1300x750")
        self.window.grab_set()
        
        # مدير الطباعة
        self.print_manager = PrintManager(self.window)
        
        # المتغيرات
        self.setup_variables()
        
        # إنشاء الواجهة
        self.create_widgets()
        
        # تحميل البيانات
        self.load_products()
        self.load_customers()
    
    def setup_variables(self):
        self.product_search_var = tk.StringVar()
        self.customer_var = tk.StringVar()
        self.discount_var = tk.StringVar(value="0")
        self.payment_method_var = tk.StringVar(value="نقدي")
        self.notes_var = tk.StringVar()
        
        # متغيرات الإجماليات
        self.subtotal_var = tk.StringVar(value="0.00")
        self.discount_amount_var = tk.StringVar(value="0.00")
        self.total_var = tk.StringVar(value="0.00")
        
        # قائمة عناصر الفاتورة
        self.invoice_items = []
        
        # رقم الفاتورة الحالية
        self.current_invoice_id = None
    
    def create_widgets(self):
        # الإطار الرئيسي
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # الجزء العلوي - البحث والعميل
        self.create_top_frame(main_frame)
        
        # الجزء الأوسط - المنتجات والفاتورة
        self.create_middle_frame(main_frame)
        
        # الجزء السفلي - الإجماليات والدفع
        self.create_bottom_frame(main_frame)
    
    def create_top_frame(self, parent):
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # البحث عن المنتجات
        search_frame = ttk.LabelFrame(top_frame, text="البحث عن المنتج", padding="10")
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        ttk.Label(search_frame, text="اسم المنتج أو الباركود:").pack(anchor=tk.W)
        search_entry = ttk.Entry(search_frame, textvariable=self.product_search_var, font=("Arial", 12))
        search_entry.pack(fill=tk.X, pady=(5, 0))
        search_entry.bind('<KeyRelease>', self.search_products)
        search_entry.bind('<Return>', self.add_product_to_invoice)
        
        # العميل
        customer_frame = ttk.LabelFrame(top_frame, text="العميل", padding="10")
        customer_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Label(customer_frame, text="اختر العميل:").pack(anchor=tk.W)
        self.customer_combo = ttk.Combobox(customer_frame, textvariable=self.customer_var, 
                                          width=20, state="readonly")
        self.customer_combo.pack(pady=(5, 0))
    
    def create_middle_frame(self, parent):
        middle_frame = ttk.Frame(parent)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # قائمة المنتجات
        products_frame = ttk.LabelFrame(middle_frame, text="المنتجات المتاحة", padding="10")
        products_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # جدول المنتجات
        products_columns = ("ID", "الاسم", "الباركود", "السعر", "المخزون")
        self.products_tree = ttk.Treeview(products_frame, columns=products_columns, 
                                         show="headings", height=15)
        
        for col in products_columns:
            self.products_tree.heading(col, text=col)
            self.products_tree.column(col, width=100, anchor=tk.CENTER)
        
        products_scrollbar = ttk.Scrollbar(products_frame, orient=tk.VERTICAL, 
                                          command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=products_scrollbar.set)
        
        self.products_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        products_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ربط النقر المزدوج بإضافة المنتج
        self.products_tree.bind('<Double-1>', self.add_selected_product)
        
        # فاتورة البيع
        invoice_frame = ttk.LabelFrame(middle_frame, text="فاتورة البيع", padding="10")
        invoice_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # جدول الفاتورة
        invoice_columns = ("المنتج", "الكمية", "السعر", "الإجمالي")
        self.invoice_tree = ttk.Treeview(invoice_frame, columns=invoice_columns, 
                                        show="headings", height=15)
        
        for col in invoice_columns:
            self.invoice_tree.heading(col, text=col)
            self.invoice_tree.column(col, width=120, anchor=tk.CENTER)
        
        invoice_scrollbar = ttk.Scrollbar(invoice_frame, orient=tk.VERTICAL, 
                                         command=self.invoice_tree.yview)
        self.invoice_tree.configure(yscrollcommand=invoice_scrollbar.set)
        
        self.invoice_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        invoice_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # أزرار إدارة الفاتورة
        invoice_buttons = ttk.Frame(invoice_frame)
        invoice_buttons.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(invoice_buttons, text="حذف العنصر", 
                  command=self.remove_item).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(invoice_buttons, text="مسح الفاتورة", 
                  command=self.clear_invoice).pack(side=tk.LEFT)
    
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
        
        # الدفع والملاحظات
        payment_frame = ttk.LabelFrame(bottom_frame, text="الدفع والملاحظات", padding="10")
        payment_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # طريقة الدفع
        payment_method_frame = ttk.Frame(payment_frame)
        payment_method_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(payment_method_frame, text="طريقة الدفع:").pack(side=tk.LEFT)
        payment_combo = ttk.Combobox(payment_method_frame, textvariable=self.payment_method_var,
                                    values=["نقدي", "بطاقة ائتمان", "شيك", "تحويل بنكي"],
                                    state="readonly", width=15)
        payment_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # الملاحظات
        ttk.Label(payment_frame, text="ملاحظات:").pack(anchor=tk.W)
        ttk.Entry(payment_frame, textvariable=self.notes_var, width=50).pack(fill=tk.X, pady=(5, 10))
        
        # أزرار العمليات
        buttons_frame = ttk.Frame(payment_frame)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(buttons_frame, text="🛒 إتمام البيع", command=self.complete_sale).pack(side=tk.RIGHT, padx=(10, 0), ipadx=10)
        ttk.Button(buttons_frame, text="🖨️ طباعة", command=self.print_current_invoice).pack(side=tk.RIGHT, padx=(0, 5), ipadx=10)
        ttk.Button(buttons_frame, text="💾 حفظ مؤقت", command=self.save_draft).pack(side=tk.RIGHT, padx=(0, 5), ipadx=10)
    
    def load_products(self):
        products = self.db.get_products()
        
        # مسح البيانات الحالية
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        # إضافة المنتجات
        for product in products:
            if product[7] > 0:  # المنتجات المتوفرة فقط
                self.products_tree.insert('', tk.END, values=(
                    product[0], product[1], product[2], product[6], product[7]
                ))
    
    def load_customers(self):
        customers = self.db.get_customers()
        customer_values = ["عميل عادي"] + [f"{customer[0]} - {customer[1]}" for customer in customers]
        self.customer_combo['values'] = customer_values
        self.customer_combo.set("عميل عادي")
    
    def search_products(self, event=None):
        search_term = self.product_search_var.get().lower()
        
        # مسح البيانات الحالية
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        # تحميل وتصفية المنتجات
        products = self.db.get_products()
        for product in products:
            if product[7] > 0:  # المنتجات المتوفرة فقط
                if (search_term in str(product[1]).lower() or  # الاسم
                    search_term in str(product[2]).lower()):   # الباركود
                    
                    self.products_tree.insert('', tk.END, values=(
                        product[0], product[1], product[2], product[6], product[7]
                    ))
    
    def add_product_to_invoice(self, event=None):
        search_term = self.product_search_var.get().strip()
        if not search_term:
            return
        
        # البحث عن المنتج
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, selling_price, current_stock 
            FROM products 
            WHERE name LIKE ? OR barcode = ?
            LIMIT 1
        ''', (f'%{search_term}%', search_term))
        
        product = cursor.fetchone()
        conn.close()
        
        if product:
            self.add_item_to_invoice(product[0], product[1], product[2], product[3])
            self.product_search_var.set("")
        else:
            messagebox.showwarning("تحذير", "المنتج غير موجود")
    
    def add_selected_product(self, event):
        selection = self.products_tree.selection()
        if selection:
            item = self.products_tree.item(selection[0])
            values = item['values']
            self.add_item_to_invoice(values[0], values[1], values[3], values[4])
    
    def add_item_to_invoice(self, product_id, product_name, price, stock):
        if stock <= 0:
            messagebox.showwarning("تحذير", "المنتج غير متوفر في المخزون")
            return
        
        # التحقق من وجود المنتج في الفاتورة
        for i, item in enumerate(self.invoice_items):
            if item['product_id'] == product_id:
                if item['quantity'] < stock:
                    self.invoice_items[i]['quantity'] += 1
                    self.invoice_items[i]['total'] = self.invoice_items[i]['quantity'] * price
                    self.refresh_invoice_display()
                    self.calculate_totals()
                else:
                    messagebox.showwarning("تحذير", "الكمية المطلوبة أكبر من المتوفر في المخزون")
                return
        
        # إضافة منتج جديد
        self.invoice_items.append({
            'product_id': product_id,
            'product_name': product_name,
            'quantity': 1,
            'price': price,
            'total': price
        })
        
        self.refresh_invoice_display()
        self.calculate_totals()
    
    def refresh_invoice_display(self):
        # مسح البيانات الحالية
        for item in self.invoice_tree.get_children():
            self.invoice_tree.delete(item)
        
        # إضافة العناصر
        for item in self.invoice_items:
            self.invoice_tree.insert('', tk.END, values=(
                item['product_name'],
                item['quantity'],
                f"{item['price']:.2f}",
                f"{item['total']:.2f}"
            ))
    
    def calculate_totals(self, *args):
        subtotal = sum(item['total'] for item in self.invoice_items)
        
        try:
            discount_percent = float(self.discount_var.get() or 0)
        except ValueError:
            discount_percent = 0
        
        discount_amount = subtotal * (discount_percent / 100)
        total = subtotal - discount_amount
        
        self.subtotal_var.set(f"{subtotal:.2f}")
        self.discount_amount_var.set(f"{discount_amount:.2f}")
        self.total_var.set(f"{total:.2f}")
    
    def remove_item(self):
        selection = self.invoice_tree.selection()
        if selection:
            index = self.invoice_tree.index(selection[0])
            del self.invoice_items[index]
            self.refresh_invoice_display()
            self.calculate_totals()
    
    def clear_invoice(self):
        if messagebox.askyesno("تأكيد", "هل تريد مسح الفاتورة؟"):
            self.invoice_items.clear()
            self.refresh_invoice_display()
            self.calculate_totals()
    
    def complete_sale(self):
        if not self.invoice_items:
            messagebox.showwarning("تحذير", "لا توجد عناصر في الفاتورة")
            return
        
        try:
            # حفظ الفاتورة في قاعدة البيانات
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # استخراج معرف العميل
            customer_id = None
            customer_text = self.customer_var.get()
            if customer_text != "عميل عادي":
                customer_id = int(customer_text.split(' - ')[0])
            
            # حساب الإجماليات
            subtotal = sum(item['total'] for item in self.invoice_items)
            discount_percent = float(self.discount_var.get() or 0)
            discount_amount = subtotal * (discount_percent / 100)
            final_amount = subtotal - discount_amount
            
            # إدراج الفاتورة
            cursor.execute('''
                INSERT INTO sales (customer_id, total_amount, discount, final_amount, 
                                 payment_method, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (customer_id, subtotal, discount_amount, final_amount,
                  self.payment_method_var.get(), self.notes_var.get(), self.user['id']))
            
            sale_id = cursor.lastrowid
            
            # إدراج عناصر الفاتورة وتحديث المخزون
            for item in self.invoice_items:
                # إدراج العنصر
                cursor.execute('''
                    INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?)
                ''', (sale_id, item['product_id'], item['quantity'], 
                      item['price'], item['total']))
                
                # تحديث المخزون
                self.db.update_stock(item['product_id'], item['quantity'], 'out',
                                   'sale', sale_id, self.user['id'])
            
            conn.commit()
            conn.close()
            
            self.current_invoice_id = sale_id
            messagebox.showinfo("نجح", f"تم إتمام البيع بنجاح\nرقم الفاتورة: {sale_id}")
            
            # عرض خيارات ما بعد البيع
            self.show_post_sale_options(sale_id)
            
            # مسح الفاتورة
            self.clear_invoice()
            self.load_products()  # تحديث قائمة المنتجات
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في إتمام البيع: {str(e)}")
    
    def print_current_invoice(self):
        """طباعة الفاتورة الحالية"""
        if not self.invoice_items:
            messagebox.showwarning("تحذير", "لا توجد عناصر للطباعة")
            return
        
        # إعداد بيانات الفاتورة للطباعة
        invoice_data = {
            'id': self.current_invoice_id or "مسودة",
            'customer': self.customer_var.get() if self.customer_var.get() != "عميل عادي" else "عميل عادي",
            'items': [
                {
                    'name': item['product_name'],
                    'quantity': item['quantity'],
                    'price': item['price'],
                    'total': item['total']
                }
                for item in self.invoice_items
            ],
            'subtotal': float(self.subtotal_var.get()),
            'discount': float(self.discount_amount_var.get()),
            'total': float(self.total_var.get()),
            'payment_method': self.payment_method_var.get(),
            'notes': self.notes_var.get()
        }
        
        self.print_manager.print_invoice(invoice_data, "sale")
    
    def save_draft(self):
        """حفظ الفاتورة كمسودة"""
        if not self.invoice_items:
            messagebox.showwarning("تحذير", "لا توجد عناصر لحفظها")
            return
        
        try:
            # حفظ المسودة في ملف JSON
            import json
            draft_data = {
                'timestamp': datetime.now().isoformat(),
                'customer': self.customer_var.get(),
                'items': self.invoice_items,
                'discount': self.discount_var.get(),
                'payment_method': self.payment_method_var.get(),
                'notes': self.notes_var.get()
            }
            
            filename = f"draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("نجح", f"تم حفظ المسودة: {filename}")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في حفظ المسودة: {str(e)}")
    
    def show_post_sale_options(self, sale_id):
        """عرض خيارات ما بعد البيع"""
        dialog = tk.Toplevel(self.window)
        dialog.title("خيارات ما بعد البيع")
        dialog.geometry("300x200")
        dialog.grab_set()
        dialog.transient(self.window)
        
        # توسيط النافذة
        dialog.geometry("+%d+%d" % (
            self.window.winfo_rootx() + 100,
            self.window.winfo_rooty() + 100
        ))
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"تم إتمام البيع بنجاح\nرقم الفاتورة: {sale_id}", 
                 font=("Arial", 12), justify=tk.CENTER).pack(pady=(0, 20))
        
        # أزرار الخيارات
        ttk.Button(frame, text="🖨️ طباعة الفاتورة", 
                  command=lambda: self.print_completed_sale(sale_id, dialog)).pack(fill=tk.X, pady=5)
        
        ttk.Button(frame, text="📧 إرسال بالبريد الإلكتروني", 
                  command=lambda: self.email_invoice(sale_id)).pack(fill=tk.X, pady=5)
        
        ttk.Button(frame, text="🛒 بيع جديد", 
                  command=dialog.destroy).pack(fill=tk.X, pady=5)
        
        ttk.Button(frame, text="❌ إغلاق", 
                  command=dialog.destroy).pack(fill=tk.X, pady=(10, 0))
    
    def print_completed_sale(self, sale_id, dialog):
        """طباعة فاتورة مكتملة"""
        try:
            # جلب بيانات الفاتورة من قاعدة البيانات
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # جلب بيانات الفاتورة الأساسية
            cursor.execute('''
                SELECT s.id, s.total_amount, s.discount, s.final_amount, 
                       s.payment_method, s.notes, COALESCE(c.name, 'عميل عادي')
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.id = ?
            ''', (sale_id,))
            
            sale_data = cursor.fetchone()
            if not sale_data:
                messagebox.showerror("خطأ", "لم يتم العثور على الفاتورة")
                return
            
            # جلب عناصر الفاتورة
            cursor.execute('''
                SELECT p.name, si.quantity, si.unit_price, si.total_price
                FROM sale_items si
                JOIN products p ON si.product_id = p.id
                WHERE si.sale_id = ?
            ''', (sale_id,))
            
            items_data = cursor.fetchall()
            conn.close()
            
            # إعداد بيانات الطباعة
            invoice_data = {
                'id': sale_data[0],
                'customer': sale_data[6],
                'items': [
                    {
                        'name': item[0],
                        'quantity': item[1],
                        'price': item[2],
                        'total': item[3]
                    }
                    for item in items_data
                ],
                'subtotal': sale_data[1],
                'discount': sale_data[2],
                'total': sale_data[3],
                'payment_method': sale_data[4],
                'notes': sale_data[5] or ""
            }
            
            self.print_manager.print_invoice(invoice_data, "sale")
            dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في طباعة الفاتورة: {str(e)}")
    
    def email_invoice(self, sale_id):
        """إرسال الفاتورة بالبريد الإلكتروني"""
        messagebox.showinfo("قريباً", "وظيفة الإرسال بالبريد الإلكتروني ستكون متاحة قريباً")
    
    def validate_number(self, value):
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False