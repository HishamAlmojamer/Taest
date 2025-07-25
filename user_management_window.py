#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة إدارة المستخدمين والصلاحيات
تصميم: المهندس هشام المجمر - 773988932
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from permissions_system import PermissionManager, UserRole, Permission
from validation_utils import DataValidator
import hashlib
import secrets

class UserManagementWindow:
    def __init__(self, parent, db, user):
        self.parent = parent
        self.db = db
        self.user = user
        self.permission_manager = PermissionManager(db.db_path)
        
        # التحقق من الصلاحية
        if not self.permission_manager.has_permission(user['id'], Permission.USER_MANAGEMENT):
            messagebox.showerror("غير مسموح", "ليس لديك صلاحية لإدارة المستخدمين")
            return
        
        # إنشاء النافذة
        self.window = tk.Toplevel(parent)
        self.window.title("👥 إدارة المستخدمين والصلاحيات")
        self.window.geometry("1200x800")
        self.window.grab_set()
        
        # المتغيرات
        self.setup_variables()
        
        # إنشاء الواجهة
        self.create_widgets()
        
        # تحميل البيانات
        self.load_users()
        self.load_roles()
    
    def setup_variables(self):
        """إعداد المتغيرات"""
        self.selected_user_id = None
        
        # متغيرات المستخدم
        self.username_var = tk.StringVar()
        self.full_name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.role_var = tk.StringVar()
        self.is_active_var = tk.BooleanVar(value=True)
        
        # متغيرات البحث
        self.search_var = tk.StringVar()
        self.filter_role_var = tk.StringVar()
        self.filter_status_var = tk.StringVar()
    
    def create_widgets(self):
        """إنشاء عناصر الواجهة"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # إنشاء دفتر الملاحظات
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # تبويب إدارة المستخدمين
        self.create_users_tab()
        
        # تبويب الأدوار والصلاحيات
        self.create_roles_tab()
        
        # تبويب سجل النشاط
        self.create_activity_tab()
    
    def create_users_tab(self):
        """تبويب إدارة المستخدمين"""
        users_frame = ttk.Frame(self.notebook)
        self.notebook.add(users_frame, text="👥 المستخدمين")
        
        # إطار البحث والفلترة
        search_frame = ttk.LabelFrame(users_frame, text="البحث والفلترة", padding="10")
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # البحث
        ttk.Label(search_frame, text="البحث:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.grid(row=0, column=1, padx=(0, 20))
        search_entry.bind('<KeyRelease>', self.search_users)
        
        # فلتر الدور
        ttk.Label(search_frame, text="الدور:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        role_combo = ttk.Combobox(search_frame, textvariable=self.filter_role_var, 
                                 width=20, state="readonly")
        role_combo.grid(row=0, column=3, padx=(0, 20))
        role_combo.bind('<<ComboboxSelected>>', self.filter_users)
        
        # فلتر الحالة
        ttk.Label(search_frame, text="الحالة:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        status_combo = ttk.Combobox(search_frame, textvariable=self.filter_status_var,
                                   values=["الكل", "نشط", "غير نشط"], width=15, state="readonly")
        status_combo.set("الكل")
        status_combo.grid(row=0, column=5, padx=(0, 20))
        status_combo.bind('<<ComboboxSelected>>', self.filter_users)
        
        # زر تحديث
        ttk.Button(search_frame, text="🔄 تحديث", 
                  command=self.load_users).grid(row=0, column=6)
        
        # إطار رئيسي للمحتوى
        content_frame = ttk.Frame(users_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # الجانب الأيسر - قائمة المستخدمين
        left_frame = ttk.LabelFrame(content_frame, text="قائمة المستخدمين", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # جدول المستخدمين
        columns = ("المعرف", "اسم المستخدم", "الاسم الكامل", "الدور", "البريد الإلكتروني", "الحالة", "آخر دخول")
        self.users_tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=120, anchor=tk.CENTER)
        
        # شريط التمرير للجدول
        users_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=users_scrollbar.set)
        
        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        users_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ربط الأحداث
        self.users_tree.bind('<<TreeviewSelect>>', self.on_user_select)
        self.users_tree.bind('<Double-1>', self.edit_user)
        
        # الجانب الأيمن - تفاصيل المستخدم
        right_frame = ttk.LabelFrame(content_frame, text="تفاصيل المستخدم", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # حقول المستخدم
        row = 0
        
        ttk.Label(right_frame, text="اسم المستخدم:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(right_frame, textvariable=self.username_var, width=25).grid(row=row, column=1, pady=5)
        row += 1
        
        ttk.Label(right_frame, text="الاسم الكامل:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(right_frame, textvariable=self.full_name_var, width=25).grid(row=row, column=1, pady=5)
        row += 1
        
        ttk.Label(right_frame, text="البريد الإلكتروني:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(right_frame, textvariable=self.email_var, width=25).grid(row=row, column=1, pady=5)
        row += 1
        
        ttk.Label(right_frame, text="رقم الهاتف:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(right_frame, textvariable=self.phone_var, width=25).grid(row=row, column=1, pady=5)
        row += 1
        
        ttk.Label(right_frame, text="الدور:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.role_combo = ttk.Combobox(right_frame, textvariable=self.role_var, 
                                      width=22, state="readonly")
        self.role_combo.grid(row=row, column=1, pady=5)
        row += 1
        
        ttk.Checkbutton(right_frame, text="نشط", variable=self.is_active_var).grid(row=row, column=0, columnspan=2, pady=10)
        row += 1
        
        # أزرار العمليات
        buttons_frame = ttk.Frame(right_frame)
        buttons_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        ttk.Button(buttons_frame, text="➕ إضافة", command=self.add_user).pack(side=tk.TOP, fill=tk.X, pady=2)
        ttk.Button(buttons_frame, text="✏️ تعديل", command=self.update_user).pack(side=tk.TOP, fill=tk.X, pady=2)
        ttk.Button(buttons_frame, text="🗑️ حذف", command=self.delete_user).pack(side=tk.TOP, fill=tk.X, pady=2)
        ttk.Button(buttons_frame, text="🔑 تغيير كلمة المرور", command=self.change_password).pack(side=tk.TOP, fill=tk.X, pady=2)
        ttk.Button(buttons_frame, text="🔒 قفل/إلغاء قفل", command=self.toggle_user_status).pack(side=tk.TOP, fill=tk.X, pady=2)
        ttk.Button(buttons_frame, text="🔄 مسح الحقول", command=self.clear_user_fields).pack(side=tk.TOP, fill=tk.X, pady=2)
        
        row += 1
        
        # إطار الصلاحيات الخاصة
        permissions_frame = ttk.LabelFrame(right_frame, text="الصلاحيات الخاصة", padding="5")
        permissions_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Button(permissions_frame, text="⚙️ إدارة الصلاحيات", 
                  command=self.manage_user_permissions).pack(fill=tk.X)
    
    def create_roles_tab(self):
        """تبويب الأدوار والصلاحيات"""
        roles_frame = ttk.Frame(self.notebook)
        self.notebook.add(roles_frame, text="🎭 الأدوار والصلاحيات")
        
        # إطار الأدوار
        roles_list_frame = ttk.LabelFrame(roles_frame, text="الأدوار", padding="10")
        roles_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # قائمة الأدوار
        self.roles_listbox = tk.Listbox(roles_list_frame, height=15)
        self.roles_listbox.pack(fill=tk.BOTH, expand=True)
        self.roles_listbox.bind('<<ListboxSelect>>', self.on_role_select)
        
        # إطار الصلاحيات
        permissions_frame = ttk.LabelFrame(roles_frame, text="صلاحيات الدور المحدد", padding="10")
        permissions_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # شجرة الصلاحيات
        self.permissions_tree = ttk.Treeview(permissions_frame, columns=("الصلاحية", "الحالة"), 
                                           show="tree headings", height=20)
        
        self.permissions_tree.heading("#0", text="الفئة")
        self.permissions_tree.heading("الصلاحية", text="الصلاحية")
        self.permissions_tree.heading("الحالة", text="الحالة")
        
        self.permissions_tree.column("#0", width=150)
        self.permissions_tree.column("الصلاحية", width=200)
        self.permissions_tree.column("الحالة", width=80)
        
        permissions_scrollbar = ttk.Scrollbar(permissions_frame, orient=tk.VERTICAL, 
                                            command=self.permissions_tree.yview)
        self.permissions_tree.configure(yscrollcommand=permissions_scrollbar.set)
        
        self.permissions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        permissions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_activity_tab(self):
        """تبويب سجل النشاط"""
        activity_frame = ttk.Frame(self.notebook)
        self.notebook.add(activity_frame, text="📋 سجل النشاط")
        
        # إطار الفلترة
        filter_frame = ttk.LabelFrame(activity_frame, text="فلترة السجل", padding="10")
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # فلاتر التاريخ
        ttk.Label(filter_frame, text="من تاريخ:").grid(row=0, column=0, padx=5)
        self.from_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(filter_frame, textvariable=self.from_date_var, width=12).grid(row=0, column=1, padx=5)
        
        ttk.Label(filter_frame, text="إلى تاريخ:").grid(row=0, column=2, padx=5)
        self.to_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(filter_frame, textvariable=self.to_date_var, width=12).grid(row=0, column=3, padx=5)
        
        # فلتر المستخدم
        ttk.Label(filter_frame, text="المستخدم:").grid(row=0, column=4, padx=5)
        self.activity_user_var = tk.StringVar()
        user_combo = ttk.Combobox(filter_frame, textvariable=self.activity_user_var, 
                                 width=20, state="readonly")
        user_combo.grid(row=0, column=5, padx=5)
        
        # زر التحديث
        ttk.Button(filter_frame, text="🔍 عرض السجل", 
                  command=self.load_activity_log).grid(row=0, column=6, padx=10)
        
        # جدول السجل
        log_frame = ttk.Frame(activity_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ("التاريخ", "المستخدم", "النشاط", "التفاصيل", "عنوان IP")
        self.activity_tree = ttk.Treeview(log_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.activity_tree.heading(col, text=col)
            self.activity_tree.column(col, width=150, anchor=tk.CENTER)
        
        activity_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, 
                                         command=self.activity_tree.yview)
        self.activity_tree.configure(yscrollcommand=activity_scrollbar.set)
        
        self.activity_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        activity_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def load_users(self):
        """تحميل قائمة المستخدمين"""
        # مسح البيانات الحالية
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.username, u.full_name, r.display_name, u.email, 
                   u.is_active, u.last_login
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            ORDER BY u.username
        ''')
        
        users = cursor.fetchall()
        conn.close()
        
        for user in users:
            status = "نشط" if user[5] else "غير نشط"
            last_login = user[6] if user[6] else "لم يسجل دخول"
            
            self.users_tree.insert('', tk.END, values=(
                user[0], user[1], user[2], user[3] or "غير محدد", 
                user[4] or "", status, last_login
            ))
    
    def load_roles(self):
        """تحميل قائمة الأدوار"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT name, display_name FROM roles WHERE is_active = 1')
        roles = cursor.fetchall()
        conn.close()
        
        # تحديث قائمة الأدوار في الكومبو بوكس
        role_values = [f"{role[1]} ({role[0]})" for role in roles]
        self.role_combo['values'] = role_values
        
        # تحديث فلتر الأدوار
        filter_values = ["الكل"] + [role[1] for role in roles]
        search_frame = self.window.nametowidget(self.window.winfo_children()[0].winfo_children()[0].winfo_children()[0])
        role_combo = search_frame.grid_slaves(row=0, column=3)[0]
        role_combo['values'] = filter_values
        role_combo.set("الكل")
        
        # تحديث قائمة الأدوار في التبويب
        self.roles_listbox.delete(0, tk.END)
        for role in roles:
            self.roles_listbox.insert(tk.END, f"{role[1]} ({role[0]})")
    
    def on_user_select(self, event):
        """عند اختيار مستخدم"""
        selection = self.users_tree.selection()
        if not selection:
            return
        
        item = self.users_tree.item(selection[0])
        values = item['values']
        
        self.selected_user_id = values[0]
        
        # تحميل بيانات المستخدم
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, full_name, email, phone, r.name, is_active
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            WHERE u.id = ?
        ''', (self.selected_user_id,))
        
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            self.username_var.set(user_data[0])
            self.full_name_var.set(user_data[1] or "")
            self.email_var.set(user_data[2] or "")
            self.phone_var.set(user_data[3] or "")
            
            # تحديد الدور
            if user_data[4]:
                for value in self.role_combo['values']:
                    if f"({user_data[4]})" in value:
                        self.role_var.set(value)
                        break
            
            self.is_active_var.set(bool(user_data[5]))
    
    def on_role_select(self, event):
        """عند اختيار دور"""
        selection = self.roles_listbox.curselection()
        if not selection:
            return
        
        role_text = self.roles_listbox.get(selection[0])
        role_name = role_text.split('(')[1].rstrip(')')
        
        self.load_role_permissions(role_name)
    
    def load_role_permissions(self, role_name):
        """تحميل صلاحيات الدور"""
        # مسح البيانات الحالية
        for item in self.permissions_tree.get_children():
            self.permissions_tree.delete(item)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # جلب جميع الصلاحيات مع حالتها للدور
        cursor.execute('''
            SELECT p.name, p.display_name, p.category,
                   CASE WHEN rp.permission_id IS NOT NULL THEN 1 ELSE 0 END as granted
            FROM permissions p
            LEFT JOIN role_permissions rp ON p.id = rp.permission_id 
                AND rp.role_id = (SELECT id FROM roles WHERE name = ?)
            WHERE p.is_active = 1
            ORDER BY p.category, p.display_name
        ''', (role_name,))
        
        permissions = cursor.fetchall()
        conn.close()
        
        # تجميع الصلاحيات حسب الفئة
        categories = {}
        for perm in permissions:
            category = perm[2]
            if category not in categories:
                categories[category] = []
            categories[category].append(perm)
        
        # إضافة الصلاحيات للشجرة
        for category, perms in categories.items():
            category_item = self.permissions_tree.insert('', tk.END, text=category, values=("", ""))
            
            for perm in perms:
                status = "✅ ممنوحة" if perm[3] else "❌ غير ممنوحة"
                self.permissions_tree.insert(category_item, tk.END, text="", 
                                           values=(perm[1], status))
    
    def add_user(self):
        """إضافة مستخدم جديد"""
        if not self.validate_user_data():
            return
        
        # نافذة كلمة المرور
        password = self.get_password_dialog("إدخال كلمة المرور للمستخدم الجديد")
        if not password:
            return
        
        # تشفير كلمة المرور
        salt = secrets.token_hex(32)
        hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode(), 
                                            salt.encode(), 100000)
        stored_password = salt + hashed_password.hex()
        
        # الحصول على معرف الدور
        role_name = self.role_var.get().split('(')[1].rstrip(')')
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id FROM roles WHERE name = ?', (role_name,))
            role_id = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT INTO users (username, password, full_name, email, phone, 
                                 role_id, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.username_var.get(),
                stored_password,
                self.full_name_var.get(),
                self.email_var.get() or None,
                self.phone_var.get() or None,
                role_id,
                self.is_active_var.get(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            messagebox.showinfo("نجح", "تم إضافة المستخدم بنجاح")
            self.load_users()
            self.clear_user_fields()
            
        except sqlite3.IntegrityError:
            messagebox.showerror("خطأ", "اسم المستخدم موجود بالفعل")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في إضافة المستخدم: {str(e)}")
        finally:
            conn.close()
    
    def update_user(self):
        """تحديث بيانات المستخدم"""
        if not self.selected_user_id:
            messagebox.showwarning("تحذير", "يرجى اختيار مستخدم للتعديل")
            return
        
        if not self.validate_user_data():
            return
        
        # الحصول على معرف الدور
        role_name = self.role_var.get().split('(')[1].rstrip(')')
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id FROM roles WHERE name = ?', (role_name,))
            role_id = cursor.fetchone()[0]
            
            cursor.execute('''
                UPDATE users SET full_name = ?, email = ?, phone = ?, 
                               role_id = ?, is_active = ?
                WHERE id = ?
            ''', (
                self.full_name_var.get(),
                self.email_var.get() or None,
                self.phone_var.get() or None,
                role_id,
                self.is_active_var.get(),
                self.selected_user_id
            ))
            
            conn.commit()
            messagebox.showinfo("نجح", "تم تحديث بيانات المستخدم بنجاح")
            self.load_users()
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في تحديث المستخدم: {str(e)}")
        finally:
            conn.close()
    
    def delete_user(self):
        """حذف المستخدم"""
        if not self.selected_user_id:
            messagebox.showwarning("تحذير", "يرجى اختيار مستخدم للحذف")
            return
        
        if self.selected_user_id == self.user['id']:
            messagebox.showerror("خطأ", "لا يمكن حذف المستخدم الحالي")
            return
        
        response = messagebox.askyesno("تأكيد الحذف", 
                                     "هل أنت متأكد من حذف هذا المستخدم؟\nهذا الإجراء لا يمكن التراجع عنه")
        if not response:
            return
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # حذف الصلاحيات الخاصة أولاً
            cursor.execute('DELETE FROM user_permissions WHERE user_id = ?', (self.selected_user_id,))
            
            # حذف جلسات المستخدم
            cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (self.selected_user_id,))
            
            # حذف المستخدم
            cursor.execute('DELETE FROM users WHERE id = ?', (self.selected_user_id,))
            
            conn.commit()
            messagebox.showinfo("نجح", "تم حذف المستخدم بنجاح")
            self.load_users()
            self.clear_user_fields()
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في حذف المستخدم: {str(e)}")
        finally:
            conn.close()
    
    def change_password(self):
        """تغيير كلمة مرور المستخدم"""
        if not self.selected_user_id:
            messagebox.showwarning("تحذير", "يرجى اختيار مستخدم لتغيير كلمة المرور")
            return
        
        new_password = self.get_password_dialog("إدخال كلمة المرور الجديدة")
        if not new_password:
            return
        
        # تشفير كلمة المرور الجديدة
        salt = secrets.token_hex(32)
        hashed_password = hashlib.pbkdf2_hmac('sha256', new_password.encode(), 
                                            salt.encode(), 100000)
        stored_password = salt + hashed_password.hex()
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('UPDATE users SET password = ? WHERE id = ?', 
                          (stored_password, self.selected_user_id))
            conn.commit()
            messagebox.showinfo("نجح", "تم تغيير كلمة المرور بنجاح")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في تغيير كلمة المرور: {str(e)}")
        finally:
            conn.close()
    
    def toggle_user_status(self):
        """قفل/إلغاء قفل المستخدم"""
        if not self.selected_user_id:
            messagebox.showwarning("تحذير", "يرجى اختيار مستخدم")
            return
        
        if self.selected_user_id == self.user['id']:
            messagebox.showerror("خطأ", "لا يمكن قفل المستخدم الحالي")
            return
        
        new_status = not self.is_active_var.get()
        action = "تفعيل" if new_status else "قفل"
        
        response = messagebox.askyesno("تأكيد", f"هل تريد {action} هذا المستخدم؟")
        if not response:
            return
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('UPDATE users SET is_active = ? WHERE id = ?', 
                          (new_status, self.selected_user_id))
            conn.commit()
            
            self.is_active_var.set(new_status)
            messagebox.showinfo("نجح", f"تم {action} المستخدم بنجاح")
            self.load_users()
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في {action} المستخدم: {str(e)}")
        finally:
            conn.close()
    
    def manage_user_permissions(self):
        """إدارة الصلاحيات الخاصة للمستخدم"""
        if not self.selected_user_id:
            messagebox.showwarning("تحذير", "يرجى اختيار مستخدم")
            return
        
        UserPermissionsDialog(self.window, self.db, self.selected_user_id, 
                             self.user['id'], self.permission_manager)
    
    def validate_user_data(self):
        """التحقق من صحة بيانات المستخدم"""
        if not DataValidator.validate_required_field(self.username_var.get(), "اسم المستخدم"):
            return False
        
        if not DataValidator.validate_required_field(self.full_name_var.get(), "الاسم الكامل"):
            return False
        
        if not DataValidator.validate_required_field(self.role_var.get(), "الدور"):
            return False
        
        if self.email_var.get() and not DataValidator.validate_email(self.email_var.get()):
            messagebox.showerror("خطأ", "البريد الإلكتروني غير صحيح")
            return False
        
        if self.phone_var.get() and not DataValidator.validate_phone(self.phone_var.get()):
            messagebox.showerror("خطأ", "رقم الهاتف غير صحيح")
            return False
        
        return True
    
    def get_password_dialog(self, title):
        """نافذة إدخال كلمة المرور"""
        dialog = tk.Toplevel(self.window)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.grab_set()
        dialog.transient(self.window)
        
        # توسيط النافذة
        dialog.geometry("+%d+%d" % (
            self.window.winfo_rootx() + 100,
            self.window.winfo_rooty() + 100
        ))
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        password_var = tk.StringVar()
        confirm_var = tk.StringVar()
        result = [None]
        
        ttk.Label(frame, text="كلمة المرور:").pack(anchor=tk.W, pady=(0, 5))
        password_entry = ttk.Entry(frame, textvariable=password_var, show="*", width=30)
        password_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="تأكيد كلمة المرور:").pack(anchor=tk.W, pady=(0, 5))
        confirm_entry = ttk.Entry(frame, textvariable=confirm_var, show="*", width=30)
        confirm_entry.pack(fill=tk.X, pady=(0, 20))
        
        def confirm_password():
            password = password_var.get()
            confirm = confirm_var.get()
            
            if not password:
                messagebox.showerror("خطأ", "يرجى إدخال كلمة المرور")
                return
            
            if password != confirm:
                messagebox.showerror("خطأ", "كلمة المرور وتأكيدها غير متطابقين")
                return
            
            if len(password) < 6:
                messagebox.showerror("خطأ", "كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                return
            
            result[0] = password
            dialog.destroy()
        
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(buttons_frame, text="تأكيد", command=confirm_password).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(buttons_frame, text="إلغاء", command=dialog.destroy).pack(side=tk.RIGHT)
        
        password_entry.focus()
        dialog.wait_window()
        
        return result[0]
    
    def clear_user_fields(self):
        """مسح حقول المستخدم"""
        self.selected_user_id = None
        self.username_var.set("")
        self.full_name_var.set("")
        self.email_var.set("")
        self.phone_var.set("")
        self.role_var.set("")
        self.is_active_var.set(True)
    
    def search_users(self, event=None):
        """البحث في المستخدمين"""
        self.filter_users()
    
    def filter_users(self, event=None):
        """فلترة المستخدمين"""
        search_term = self.search_var.get().lower()
        role_filter = self.filter_role_var.get()
        status_filter = self.filter_status_var.get()
        
        # مسح البيانات الحالية
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT u.id, u.username, u.full_name, r.display_name, u.email, 
                   u.is_active, u.last_login
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            WHERE 1=1
        '''
        params = []
        
        if search_term:
            query += " AND (LOWER(u.username) LIKE ? OR LOWER(u.full_name) LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        if role_filter and role_filter != "الكل":
            query += " AND r.display_name = ?"
            params.append(role_filter)
        
        if status_filter and status_filter != "الكل":
            is_active = 1 if status_filter == "نشط" else 0
            query += " AND u.is_active = ?"
            params.append(is_active)
        
        query += " ORDER BY u.username"
        
        cursor.execute(query, params)
        users = cursor.fetchall()
        conn.close()
        
        for user in users:
            status = "نشط" if user[5] else "غير نشط"
            last_login = user[6] if user[6] else "لم يسجل دخول"
            
            self.users_tree.insert('', tk.END, values=(
                user[0], user[1], user[2], user[3] or "غير محدد", 
                user[4] or "", status, last_login
            ))
    
    def load_activity_log(self):
        """تحميل سجل النشاط"""
        # مسح البيانات الحالية
        for item in self.activity_tree.get_children():
            self.activity_tree.delete(item)
        
        from_date = self.from_date_var.get()
        to_date = self.to_date_var.get()
        user_filter = self.activity_user_var.get()
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT al.timestamp, u.username, al.action, al.old_values, al.ip_address
            FROM audit_log al
            LEFT JOIN users u ON al.user_id = u.id
            WHERE DATE(al.timestamp) BETWEEN ? AND ?
        '''
        params = [from_date, to_date]
        
        if user_filter:
            query += " AND u.username = ?"
            params.append(user_filter)
        
        query += " ORDER BY al.timestamp DESC LIMIT 1000"
        
        try:
            cursor.execute(query, params)
            logs = cursor.fetchall()
            
            for log in logs:
                self.activity_tree.insert('', tk.END, values=(
                    log[0], log[1] or "نظام", log[2], 
                    log[3] or "", log[4] or "localhost"
                ))
                
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في تحميل سجل النشاط: {str(e)}")
        finally:
            conn.close()
    
    def edit_user(self, event):
        """تعديل المستخدم بالنقر المزدوج"""
        self.update_user()

class UserPermissionsDialog:
    """نافذة إدارة الصلاحيات الخاصة للمستخدم"""
    
    def __init__(self, parent, db, user_id, current_user_id, permission_manager):
        self.parent = parent
        self.db = db
        self.user_id = user_id
        self.current_user_id = current_user_id
        self.permission_manager = permission_manager
        
        # إنشاء النافذة
        self.window = tk.Toplevel(parent)
        self.window.title("⚙️ إدارة الصلاحيات الخاصة")
        self.window.geometry("600x500")
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_permissions()
    
    def create_widgets(self):
        """إنشاء عناصر الواجهة"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # معلومات المستخدم
        info_frame = ttk.LabelFrame(main_frame, text="معلومات المستخدم", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # جلب معلومات المستخدم
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT username, full_name FROM users WHERE id = ?', (self.user_id,))
        user_info = cursor.fetchone()
        conn.close()
        
        if user_info:
            ttk.Label(info_frame, text=f"المستخدم: {user_info[1]} ({user_info[0]})", 
                     font=("Arial", 12, "bold")).pack()
        
        # شجرة الصلاحيات
        permissions_frame = ttk.LabelFrame(main_frame, text="الصلاحيات الخاصة", padding="10")
        permissions_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        columns = ("الصلاحية", "الحالة", "المصدر", "تاريخ المنح")
        self.permissions_tree = ttk.Treeview(permissions_frame, columns=columns, 
                                           show="headings", height=15)
        
        for col in columns:
            self.permissions_tree.heading(col, text=col)
            self.permissions_tree.column(col, width=120, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(permissions_frame, orient=tk.VERTICAL, 
                                command=self.permissions_tree.yview)
        self.permissions_tree.configure(yscrollcommand=scrollbar.set)
        
        self.permissions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # أزرار العمليات
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(buttons_frame, text="➕ منح صلاحية", 
                  command=self.grant_permission).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="➖ سحب صلاحية", 
                  command=self.revoke_permission).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="❌ إغلاق", 
                  command=self.window.destroy).pack(side=tk.RIGHT)
    
    def load_permissions(self):
        """تحميل صلاحيات المستخدم"""
        # مسح البيانات الحالية
        for item in self.permissions_tree.get_children():
            self.permissions_tree.delete(item)
        
        permissions = self.permission_manager.get_user_permissions(self.user_id)
        
        for perm_name, perm_data in permissions.items():
            status = "✅ ممنوحة" if perm_data['granted'] else "❌ مسحوبة"
            source = "دور" if perm_data['source'] == 'role' else "خاص"
            
            self.permissions_tree.insert('', tk.END, values=(
                perm_data['display_name'],
                status,
                source,
                datetime.now().strftime("%Y-%m-%d")
            ))
    
    def grant_permission(self):
        """منح صلاحية خاصة"""
        # نافذة اختيار الصلاحية
        PermissionSelectionDialog(self.window, self.db, self.user_id, 
                                 self.current_user_id, self.permission_manager, 
                                 True, self.load_permissions)
    
    def revoke_permission(self):
        """سحب صلاحية"""
        PermissionSelectionDialog(self.window, self.db, self.user_id, 
                                 self.current_user_id, self.permission_manager, 
                                 False, self.load_permissions)

class PermissionSelectionDialog:
    """نافذة اختيار الصلاحية"""
    
    def __init__(self, parent, db, user_id, current_user_id, permission_manager, 
                 is_grant, callback):
        self.parent = parent
        self.db = db
        self.user_id = user_id
        self.current_user_id = current_user_id
        self.permission_manager = permission_manager
        self.is_grant = is_grant
        self.callback = callback
        
        # إنشاء النافذة
        self.window = tk.Toplevel(parent)
        title = "منح صلاحية" if is_grant else "سحب صلاحية"
        self.window.title(f"⚙️ {title}")
        self.window.geometry("400x300")
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_available_permissions()
    
    def create_widgets(self):
        """إنشاء عناصر الواجهة"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        action = "منح" if self.is_grant else "سحب"
        ttk.Label(main_frame, text=f"اختر الصلاحية المراد {action}ها:", 
                 font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # قائمة الصلاحيات
        self.permissions_listbox = tk.Listbox(main_frame, height=12)
        self.permissions_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # أزرار
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(buttons_frame, text=f"✅ {action}", 
                  command=self.apply_permission).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(buttons_frame, text="❌ إلغاء", 
                  command=self.window.destroy).pack(side=tk.RIGHT)
    
    def load_available_permissions(self):
        """تحميل الصلاحيات المتاحة"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, display_name, category 
            FROM permissions 
            WHERE is_active = 1 
            ORDER BY category, display_name
        ''')
        
        permissions = cursor.fetchall()
        conn.close()
        
        self.permissions_data = {}
        
        for perm in permissions:
            display_text = f"{perm[2]} - {perm[1]}"
            self.permissions_listbox.insert(tk.END, display_text)
            self.permissions_data[display_text] = perm[0]
    
    def apply_permission(self):
        """تطبيق الصلاحية"""
        selection = self.permissions_listbox.curselection()
        if not selection:
            messagebox.showwarning("تحذير", "يرجى اختيار صلاحية")
            return
        
        selected_text = self.permissions_listbox.get(selection[0])
        permission_name = self.permissions_data[selected_text]
        
        try:
            permission_enum = Permission(permission_name)
            
            if self.is_grant:
                success = self.permission_manager.grant_permission(
                    self.user_id, permission_enum, self.current_user_id)
                action = "منح"
            else:
                success = self.permission_manager.revoke_permission(
                    self.user_id, permission_enum, self.current_user_id)
                action = "سحب"
            
            if success:
                messagebox.showinfo("نجح", f"تم {action} الصلاحية بنجاح")
                self.callback()
                self.window.destroy()
            else:
                messagebox.showerror("خطأ", f"فشل في {action} الصلاحية")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {str(e)}")