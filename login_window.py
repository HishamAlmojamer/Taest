import tkinter as tk
from tkinter import ttk, messagebox
from database import Database
from permissions_system import PermissionManager
import hashlib
from datetime import datetime
import os
import config

class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{config.APP_NAME} - تسجيل الدخول")
        self.root.geometry("450x550")
        self.root.resizable(False, False)
        
        # تعيين أيقونة النافذة (إذا كانت متوفرة)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # توسيط النافذة
        self.center_window()
        
        # قاعدة البيانات
        self.db = Database()
        
        # المتغيرات
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.remember_me_var = tk.BooleanVar()
        
        # تحميل بيانات المستخدم المحفوظة
        self.load_saved_credentials()
        
        # إنشاء الواجهة
        self.create_widgets()
        
        # ربط مفتاح Enter بتسجيل الدخول
        self.root.bind('<Return>', lambda event: self.login())
        
        # التركيز على حقل اسم المستخدم أو كلمة المرور
        if self.username_var.get():
            self.password_entry.focus()
        else:
            self.username_entry.focus()
        
        # تسجيل محاولة الدخول
        self.login_attempts = 0
        self.max_attempts = 3
    
    def center_window(self):
        # الحصول على أبعاد الشاشة
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # حساب موقع النافذة
        x = (screen_width - 450) // 2
        y = (screen_height - 400) // 2
        
        self.root.geometry(f"450x400+{x}+{y}")
    
    def load_saved_credentials(self):
        """تحميل بيانات المستخدم المحفوظة"""
        try:
            if os.path.exists("user_settings.txt"):
                with open("user_settings.txt", "r", encoding="utf-8") as f:
                    saved_username = f.read().strip()
                    if saved_username:
                        self.username_var.set(saved_username)
                        self.remember_me_var.set(True)
        except:
            pass
    
    def save_credentials(self):
        """حفظ بيانات المستخدم"""
        try:
            if self.remember_me_var.get():
                with open("user_settings.txt", "w", encoding="utf-8") as f:
                    f.write(self.username_var.get())
            else:
                if os.path.exists("user_settings.txt"):
                    os.remove("user_settings.txt")
        except:
            pass
    
    def create_widgets(self):
        # الإطار الرئيسي
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # شعار أو أيقونة النظام
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # العنوان
        title_label = ttk.Label(header_frame, text="🏪 نظام إدارة المخازن", 
                               font=("Arial", 20, "bold"), foreground="#2196F3")
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame, text="نظام شامل لإدارة المخازن والمبيعات", 
                                  font=("Arial", 10), foreground="gray")
        subtitle_label.pack(pady=(5, 0))
        
        # إطار تسجيل الدخول
        login_frame = ttk.LabelFrame(main_frame, text="تسجيل الدخول", padding="20")
        login_frame.pack(fill=tk.X, pady=(0, 15))
        
        # اسم المستخدم
        ttk.Label(login_frame, text="👤 اسم المستخدم:", font=("Arial", 10)).pack(anchor=tk.W, pady=(0, 5))
        self.username_entry = ttk.Entry(login_frame, textvariable=self.username_var, 
                                       font=("Arial", 12), width=25)
        self.username_entry.pack(fill=tk.X, pady=(0, 15))
        
        # كلمة المرور
        ttk.Label(login_frame, text="🔒 كلمة المرور:", font=("Arial", 10)).pack(anchor=tk.W, pady=(0, 5))
        password_frame = ttk.Frame(login_frame)
        password_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.password_entry = ttk.Entry(password_frame, textvariable=self.password_var, 
                                       show="*", font=("Arial", 12))
        self.password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # زر إظهار/إخفاء كلمة المرور
        self.show_password_var = tk.BooleanVar()
        show_btn = ttk.Checkbutton(password_frame, text="إظهار", variable=self.show_password_var,
                                  command=self.toggle_password_visibility)
        show_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # تذكرني
        remember_frame = ttk.Frame(login_frame)
        remember_frame.pack(fill=tk.X, pady=(0, 15))
        
        remember_check = ttk.Checkbutton(remember_frame, text="تذكر اسم المستخدم", 
                                        variable=self.remember_me_var)
        remember_check.pack(side=tk.LEFT)
        
        # أزرار
        button_frame = ttk.Frame(login_frame)
        button_frame.pack(fill=tk.X)
        
        login_btn = ttk.Button(button_frame, text="🚀 دخول", command=self.login)
        login_btn.pack(side=tk.RIGHT, padx=(10, 0), ipadx=10)
        
        clear_btn = ttk.Button(button_frame, text="🗑️ مسح", command=self.clear_fields)
        clear_btn.pack(side=tk.RIGHT, ipadx=10)
        
        # معلومات المستخدم الافتراضي
        info_frame = ttk.LabelFrame(main_frame, text="ℹ️ معلومات المستخدم الافتراضي", padding="15")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_text = "اسم المستخدم: admin\nكلمة المرور: admin123"
        ttk.Label(info_frame, text=info_text, font=("Arial", 10), 
                 foreground="#666666", justify=tk.LEFT).pack(anchor=tk.W)
        
        # شريط الحالة
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(self.status_frame, text="جاهز للدخول", 
                                     font=("Arial", 9), foreground="green")
        self.status_label.pack(side=tk.LEFT)
        
        # عرض الوقت الحالي
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        time_label = ttk.Label(self.status_frame, text=current_time, 
                              font=("Arial", 9), foreground="gray")
        time_label.pack(side=tk.RIGHT)
        
        # معلومات المطور
        developer_frame = ttk.LabelFrame(main_frame, text="👨‍💻 معلومات المطور", padding="15")
        developer_frame.pack(fill=tk.X, pady=(10, 0))
        
        developer_info = f"""تصميم وتطوير: {config.APP_AUTHOR}
رقم الهاتف: {config.APP_DEVELOPER_PHONE}
الإصدار: {config.APP_VERSION}

{config.APP_COPYRIGHT}"""
        
        ttk.Label(developer_frame, text=developer_info, 
                 font=("Arial", 9), foreground="#444444", 
                 justify=tk.CENTER).pack(anchor=tk.CENTER)
    
    def toggle_password_visibility(self):
        """إظهار/إخفاء كلمة المرور"""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")
    
    def login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        # التحقق من الحقول الفارغة
        if not username or not password:
            self.update_status("يرجى إدخال اسم المستخدم وكلمة المرور", "error")
            return
        
        # التحقق من عدد المحاولات
        if self.login_attempts >= self.max_attempts:
            self.update_status("تم تجاوز الحد الأقصى لمحاولات الدخول", "error")
            messagebox.showerror("خطأ", "تم تجاوز الحد الأقصى لمحاولات الدخول. يرجى إعادة تشغيل البرنامج.")
            return
        
        self.update_status("جاري التحقق من البيانات...", "info")
        self.root.update()
        
        # التحقق من صحة البيانات
        user = self.db.authenticate_user(username, password)
        
        if user:
            self.update_status("تم تسجيل الدخول بنجاح", "success")
            
            # حفظ بيانات المستخدم إذا كان مطلوباً
            self.save_credentials()
            
            # تسجيل وقت الدخول
            self.log_login_attempt(username, True)
            
            # إغلاق نافذة تسجيل الدخول
            self.root.destroy()
            
            # فتح النافذة الرئيسية
            from main_window import MainWindow
            main_app = MainWindow(user)
            main_app.run()
        else:
            self.login_attempts += 1
            remaining = self.max_attempts - self.login_attempts
            
            self.update_status(f"بيانات خاطئة. المحاولات المتبقية: {remaining}", "error")
            self.log_login_attempt(username, False)
            
            self.password_var.set("")
            self.password_entry.focus()
            
            if remaining == 0:
                messagebox.showerror("خطأ", "تم تجاوز الحد الأقصى لمحاولات الدخول")
    
    def update_status(self, message, status_type="info"):
        """تحديث شريط الحالة"""
        colors = {
            "info": "#2196F3",
            "success": "#4CAF50", 
            "error": "#F44336",
            "warning": "#FF9800"
        }
        
        self.status_label.config(text=message, foreground=colors.get(status_type, "black"))
        self.root.update()
    
    def log_login_attempt(self, username, success):
        """تسجيل محاولة الدخول"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "نجح" if success else "فشل"
            
            with open("login_log.txt", "a", encoding="utf-8") as f:
                f.write(f"{timestamp} - {username} - {status}\n")
        except:
            pass
    
    def clear_fields(self):
        self.username_var.set("")
        self.password_var.set("")
        self.username_entry.focus()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = LoginWindow()
    app.run()