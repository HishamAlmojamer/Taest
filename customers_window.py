import tkinter as tk
from tkinter import ttk, messagebox

class CustomersWindow:
    def __init__(self, parent, db, user):
        self.parent = parent
        self.db = db
        self.user = user
        
        # إنشاء النافذة
        self.window = tk.Toplevel(parent)
        self.window.title("إدارة العملاء")
        self.window.geometry("800x600")
        self.window.grab_set()
        
        # المتغيرات
        self.setup_variables()
        
        # إنشاء الواجهة
        self.create_widgets()
        
        # تحميل البيانات
        self.load_customers()
    
    def setup_variables(self):
        self.name_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.address_var = tk.StringVar()
        self.search_var = tk.StringVar()
        
        # متغير لتتبع العميل المحدد للتعديل
        self.selected_customer_id = None
    
    def create_widgets(self):
        # الإطار الرئيسي
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # إطار الإدخال
        self.create_input_frame(main_frame)
        
        # إطار البحث والعرض
        self.create_display_frame(main_frame)
    
    def create_input_frame(self, parent):
        input_frame = ttk.LabelFrame(parent, text="بيانات العميل", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # الصف الأول
        row1 = ttk.Frame(input_frame)
        row1.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(row1, text="اسم العميل:").pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.name_var, width=30).pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(row1, text="رقم الهاتف:").pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.phone_var, width=20).pack(side=tk.LEFT, padx=(5, 0))
        
        # الصف الثاني
        row2 = ttk.Frame(input_frame)
        row2.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(row2, text="البريد الإلكتروني:").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.email_var, width=30).pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(row2, text="العنوان:").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.address_var, width=30).pack(side=tk.LEFT, padx=(5, 0))
        
        # أزرار العمليات
        buttons_frame = ttk.Frame(input_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(buttons_frame, text="إضافة", command=self.add_customer).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="تعديل", command=self.update_customer).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="حذف", command=self.delete_customer).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="مسح", command=self.clear_fields).pack(side=tk.LEFT)
    
    def create_display_frame(self, parent):
        display_frame = ttk.LabelFrame(parent, text="قائمة العملاء", padding="10")
        display_frame.pack(fill=tk.BOTH, expand=True)
        
        # إطار البحث
        search_frame = ttk.Frame(display_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="البحث:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(5, 10))
        search_entry.bind('<KeyRelease>', self.search_customers)
        
        ttk.Button(search_frame, text="تحديث", command=self.load_customers).pack(side=tk.LEFT)
        
        # جدول العملاء
        columns = ("ID", "اسم العميل", "رقم الهاتف", "البريد الإلكتروني")
        self.tree = ttk.Treeview(display_frame, columns=columns, show="headings", height=15)
        
        # تكوين الأعمدة
        column_widths = [50, 250, 150, 250]
        for i, (col, width) in enumerate(zip(columns, column_widths)):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=tk.CENTER if i == 0 else tk.W)
        
        # شريط التمرير
        scrollbar = ttk.Scrollbar(display_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # تخطيط الجدول وشريط التمرير
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ربط النقر المزدوج بالتعديل
        self.tree.bind('<Double-1>', self.on_item_select)
    
    def load_customers(self):
        # مسح البيانات الحالية
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # تحميل العملاء
        customers = self.db.get_customers()
        for customer in customers:
            self.tree.insert('', tk.END, values=customer)
    
    def search_customers(self, event=None):
        search_term = self.search_var.get().lower()
        
        # مسح البيانات الحالية
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # تحميل وتصفية العملاء
        customers = self.db.get_customers()
        for customer in customers:
            if (search_term in str(customer[1]).lower() or  # الاسم
                search_term in str(customer[2]).lower() or  # الهاتف
                search_term in str(customer[3]).lower()):   # البريد الإلكتروني
                
                self.tree.insert('', tk.END, values=customer)
    
    def add_customer(self):
        if not self.validate_input():
            return
        
        success = self.db.add_customer(
            self.name_var.get().strip(),
            self.phone_var.get().strip(),
            self.email_var.get().strip(),
            self.address_var.get().strip()
        )
        
        if success:
            messagebox.showinfo("نجح", "تم إضافة العميل بنجاح")
            self.clear_fields()
            self.load_customers()
        else:
            messagebox.showerror("خطأ", "فشل في إضافة العميل")
    
    def update_customer(self):
        if not self.selected_customer_id:
            messagebox.showerror("خطأ", "يرجى اختيار عميل للتعديل")
            return
        
        if not self.validate_input():
            return
        
        # سيتم تنفيذ التحديث لاحقاً
        messagebox.showinfo("قريباً", "وظيفة التعديل ستكون متاحة قريباً")
    
    def delete_customer(self):
        if not self.selected_customer_id:
            messagebox.showerror("خطأ", "يرجى اختيار عميل للحذف")
            return
        
        if messagebox.askyesno("تأكيد", "هل تريد حذف هذا العميل؟"):
            # سيتم تنفيذ الحذف لاحقاً
            messagebox.showinfo("قريباً", "وظيفة الحذف ستكون متاحة قريباً")
    
    def on_item_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            
            self.selected_customer_id = values[0]
            self.name_var.set(values[1])
            self.phone_var.set(values[2])
            self.email_var.set(values[3])
            
            # الحصول على العنوان من قاعدة البيانات
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT address FROM customers WHERE id = ?", (values[0],))
            result = cursor.fetchone()
            if result:
                self.address_var.set(result[0] or "")
            conn.close()
    
    def validate_input(self):
        if not self.name_var.get().strip():
            messagebox.showerror("خطأ", "يرجى إدخال اسم العميل")
            return False
        
        return True
    
    def clear_fields(self):
        self.selected_customer_id = None
        self.name_var.set("")
        self.phone_var.set("")
        self.email_var.set("")
        self.address_var.set("")