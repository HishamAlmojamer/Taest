import tkinter as tk
from tkinter import ttk, messagebox

class CategoryWindow:
    def __init__(self, parent, db, callback=None):
        self.parent = parent
        self.db = db
        self.callback = callback  # دالة لتحديث قائمة الفئات في النافذة الأصلية
        
        # إنشاء النافذة
        self.window = tk.Toplevel(parent)
        self.window.title("إدارة الفئات")
        self.window.geometry("500x400")
        self.window.grab_set()
        self.window.transient(parent)
        
        # المتغيرات
        self.setup_variables()
        
        # إنشاء الواجهة
        self.create_widgets()
        
        # تحميل البيانات
        self.load_categories()
    
    def setup_variables(self):
        self.name_var = tk.StringVar()
        self.description_var = tk.StringVar()
        self.selected_category_id = None
    
    def create_widgets(self):
        # الإطار الرئيسي
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # إطار الإدخال
        input_frame = ttk.LabelFrame(main_frame, text="بيانات الفئة", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # اسم الفئة
        ttk.Label(input_frame, text="اسم الفئة:").pack(anchor=tk.W)
        ttk.Entry(input_frame, textvariable=self.name_var, width=40).pack(fill=tk.X, pady=(5, 10))
        
        # الوصف
        ttk.Label(input_frame, text="الوصف:").pack(anchor=tk.W)
        ttk.Entry(input_frame, textvariable=self.description_var, width=40).pack(fill=tk.X, pady=(5, 10))
        
        # أزرار العمليات
        buttons_frame = ttk.Frame(input_frame)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(buttons_frame, text="إضافة", command=self.add_category).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="تعديل", command=self.update_category).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="حذف", command=self.delete_category).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="مسح", command=self.clear_fields).pack(side=tk.LEFT)
        
        # إطار العرض
        display_frame = ttk.LabelFrame(main_frame, text="قائمة الفئات", padding="10")
        display_frame.pack(fill=tk.BOTH, expand=True)
        
        # جدول الفئات
        columns = ("ID", "اسم الفئة", "الوصف")
        self.tree = ttk.Treeview(display_frame, columns=columns, show="headings", height=12)
        
        # تكوين الأعمدة
        self.tree.heading("ID", text="ID")
        self.tree.heading("اسم الفئة", text="اسم الفئة")
        self.tree.heading("الوصف", text="الوصف")
        
        self.tree.column("ID", width=50, anchor=tk.CENTER)
        self.tree.column("اسم الفئة", width=150, anchor=tk.W)
        self.tree.column("الوصف", width=250, anchor=tk.W)
        
        # شريط التمرير
        scrollbar = ttk.Scrollbar(display_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # تخطيط الجدول وشريط التمرير
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ربط النقر المزدوج بالتعديل
        self.tree.bind('<Double-1>', self.on_item_select)
        
        # زر الإغلاق
        close_frame = ttk.Frame(main_frame)
        close_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(close_frame, text="إغلاق", command=self.close_window).pack(side=tk.RIGHT)
    
    def load_categories(self):
        # مسح البيانات الحالية
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # تحميل الفئات
        categories = self.db.get_categories()
        for category in categories:
            self.tree.insert('', tk.END, values=category)
    
    def add_category(self):
        if not self.validate_input():
            return
        
        success = self.db.add_category(
            self.name_var.get().strip(),
            self.description_var.get().strip()
        )
        
        if success:
            messagebox.showinfo("نجح", "تم إضافة الفئة بنجاح")
            self.clear_fields()
            self.load_categories()
            if self.callback:
                self.callback()  # تحديث قائمة الفئات في النافذة الأصلية
        else:
            messagebox.showerror("خطأ", "فشل في إضافة الفئة (ربما الاسم مكرر)")
    
    def update_category(self):
        if not self.selected_category_id:
            messagebox.showerror("خطأ", "يرجى اختيار فئة للتعديل")
            return
        
        if not self.validate_input():
            return
        
        # سيتم تنفيذ التحديث لاحقاً
        messagebox.showinfo("قريباً", "وظيفة التعديل ستكون متاحة قريباً")
    
    def delete_category(self):
        if not self.selected_category_id:
            messagebox.showerror("خطأ", "يرجى اختيار فئة للحذف")
            return
        
        if messagebox.askyesno("تأكيد", "هل تريد حذف هذه الفئة؟"):
            # سيتم تنفيذ الحذف لاحقاً
            messagebox.showinfo("قريباً", "وظيفة الحذف ستكون متاحة قريباً")
    
    def on_item_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            
            self.selected_category_id = values[0]
            self.name_var.set(values[1])
            self.description_var.set(values[2] if values[2] else "")
    
    def validate_input(self):
        if not self.name_var.get().strip():
            messagebox.showerror("خطأ", "يرجى إدخال اسم الفئة")
            return False
        
        return True
    
    def clear_fields(self):
        self.selected_category_id = None
        self.name_var.set("")
        self.description_var.set("")
    
    def close_window(self):
        self.window.destroy()