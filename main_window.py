import tkinter as tk
from tkinter import ttk, messagebox
from database import Database
from products_window import ProductsWindow
from sales_window import SalesWindow
from purchases_window import PurchasesWindow
from reports_window import ReportsWindow
from suppliers_window import SuppliersWindow
from customers_window import CustomersWindow
from dashboard_window import DashboardWindow
from user_management_window import UserManagementWindow
from permissions_system import PermissionManager, Permission, require_permission
import config

class MainWindow:
    def __init__(self, user):
        self.user = user
        self.root = tk.Tk()
        self.root.title(f"{config.APP_NAME} v{config.APP_VERSION} - {user['full_name']}")
        self.root.geometry("1400x800")
        self.root.state('zoomed')  # تكبير النافذة
        
        # قاعدة البيانات
        self.db = Database()
        
        # إعداد نظام الصلاحيات
        self.permission_manager = PermissionManager(self.db.db_path)
        
        # إنشاء الواجهة
        self.create_widgets()
        
        # تحديث الإحصائيات
        self.update_statistics()
    
    def create_widgets(self):
        # شريط القوائم
        self.create_menu_bar()
        
        # الإطار الرئيسي
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # شريط المعلومات العلوي
        self.create_info_bar(main_frame)
        
        # الإطار الأوسط - الأزرار الرئيسية
        self.create_main_buttons(main_frame)
        
        # الإطار السفلي - الإحصائيات
        self.create_statistics_frame(main_frame)
    
    def create_menu_bar(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # قائمة الملف
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ملف", menu=file_menu)
        file_menu.add_command(label="تسجيل خروج", command=self.logout)
        file_menu.add_separator()
        file_menu.add_command(label="خروج", command=self.root.quit)
        
        # قائمة المخزون
        inventory_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="المخزون", menu=inventory_menu)
        inventory_menu.add_command(label="إدارة المنتجات", command=self.open_products)
        inventory_menu.add_command(label="تقرير المخزون", command=self.open_inventory_report)
        
        # قائمة المبيعات
        sales_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="المبيعات", menu=sales_menu)
        sales_menu.add_command(label="نقطة البيع", command=self.open_sales)
        sales_menu.add_command(label="تقارير المبيعات", command=self.open_sales_reports)
        
        # قائمة المشتريات
        purchases_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="المشتريات", menu=purchases_menu)
        purchases_menu.add_command(label="إدارة المشتريات", command=self.open_purchases)
        purchases_menu.add_command(label="تقارير المشتريات", command=self.open_purchases_reports)
        
        # قائمة الأطراف
        parties_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="الأطراف", menu=parties_menu)
        parties_menu.add_command(label="الموردين", command=self.open_suppliers)
        parties_menu.add_command(label="العملاء", command=self.open_customers)
        
        # قائمة التقارير
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="التقارير", menu=reports_menu)
        reports_menu.add_command(label="🎛️ لوحة التحكم الذكية", command=self.open_dashboard)
        reports_menu.add_separator()
        reports_menu.add_command(label="📊 التقارير المالية", command=self.open_reports)
        reports_menu.add_command(label="📋 تقارير المخزون", command=self.open_inventory_report)
        
        # قائمة الإدارة (للمديرين فقط)
        if self.permission_manager.has_permission(self.user['id'], Permission.USER_MANAGEMENT):
            admin_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="الإدارة", menu=admin_menu)
            admin_menu.add_command(label="👥 إدارة المستخدمين", command=self.open_user_management)
            admin_menu.add_command(label="🔒 إدارة الصلاحيات", command=self.open_permissions_management)
            admin_menu.add_separator()
            admin_menu.add_command(label="💾 نسخة احتياطية", command=self.create_backup)
            admin_menu.add_command(label="📋 سجل المراجعة", command=self.view_audit_log)
        
        # قائمة المساعدة
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="مساعدة", menu=help_menu)
        help_menu.add_command(label="📖 دليل المستخدم", command=self.show_user_guide)
        help_menu.add_command(label="ℹ️ حول البرنامج", command=self.show_about)
        help_menu.add_separator()
        help_menu.add_command(label="📞 الدعم الفني", command=self.show_support_info)
    
    def create_info_bar(self, parent):
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        # معلومات المستخدم
        user_label = ttk.Label(info_frame, text=f"المستخدم: {self.user['full_name']}", 
                              font=("Arial", 12, "bold"))
        user_label.pack(side=tk.LEFT)
        
        # التاريخ والوقت
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        time_label = ttk.Label(info_frame, text=f"التاريخ: {now}", 
                              font=("Arial", 12))
        time_label.pack(side=tk.RIGHT)
    
    def create_main_buttons(self, parent):
        buttons_frame = ttk.LabelFrame(parent, text="الوظائف الرئيسية", padding="20")
        buttons_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # إنشاء شبكة من الأزرار
        buttons = [
            ("🎛️ لوحة التحكم الذكية", self.open_dashboard, "#2196F3"),
            ("🏷️ إدارة المنتجات", self.open_products, "#4CAF50"),
            ("💰 نقطة البيع", self.open_sales, "#FF9800"),
            ("📦 المشتريات", self.open_purchases, "#9C27B0"),
            ("🏢 الموردين", self.open_suppliers, "#607D8B"),
            ("👥 العملاء", self.open_customers, "#795548"),
            ("📊 التقارير", self.open_reports, "#F44336")
        ]
        
        row = 0
        col = 0
        for text, command, color in buttons:
            # إنشاء إطار للزر مع لون مخصص
            btn_frame = tk.Frame(buttons_frame, bg=color, relief=tk.RAISED, bd=2)
            btn_frame.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
            
            btn = tk.Button(btn_frame, text=text, command=command,
                           font=("Arial", 11, "bold"), fg="white", bg=color,
                           relief=tk.FLAT, bd=0, padx=15, pady=20,
                           cursor="hand2", wraplength=150)
            btn.pack(fill=tk.BOTH, expand=True)
            
            # تأثير hover
            def create_hover_effect(button, original_color):
                def on_enter(e):
                    button.config(bg=self.darken_color(original_color))
                def on_leave(e):
                    button.config(bg=original_color)
                return on_enter, on_leave
            
            on_enter, on_leave = create_hover_effect(btn, color)
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
            
            col += 1
            if col > 2:  # 3 أزرار في كل صف
                col = 0
                row += 1
        
        # تكوين الشبكة
        for i in range(3):
            buttons_frame.columnconfigure(i, weight=1)
    
    def darken_color(self, color):
        """تغميق اللون للتأثير hover"""
        # إزالة # من بداية اللون
        color = color.lstrip('#')
        # تحويل إلى RGB
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        # تغميق بنسبة 20%
        darkened = tuple(max(0, int(c * 0.8)) for c in rgb)
        # تحويل مرة أخرى إلى hex
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
        for i in range(2):
            buttons_frame.rowconfigure(i, weight=1)
    
    def create_statistics_frame(self, parent):
        stats_frame = ttk.LabelFrame(parent, text="إحصائيات سريعة", padding="20")
        stats_frame.pack(fill=tk.X)
        
        # إنشاء متغيرات الإحصائيات
        self.total_products_var = tk.StringVar(value="0")
        self.low_stock_var = tk.StringVar(value="0")
        self.today_sales_var = tk.StringVar(value="0.00")
        self.total_customers_var = tk.StringVar(value="0")
        
        # عرض الإحصائيات
        stats = [
            ("إجمالي المنتجات", self.total_products_var),
            ("منتجات قليلة المخزون", self.low_stock_var),
            ("مبيعات اليوم", self.today_sales_var),
            ("إجمالي العملاء", self.total_customers_var)
        ]
        
        for i, (label, var) in enumerate(stats):
            stat_frame = ttk.Frame(stats_frame)
            stat_frame.grid(row=0, column=i, padx=20, sticky="ew")
            
            ttk.Label(stat_frame, text=label, font=("Arial", 10)).pack()
            ttk.Label(stat_frame, textvariable=var, 
                     font=("Arial", 14, "bold"), foreground="blue").pack()
        
        # تكوين الشبكة
        for i in range(4):
            stats_frame.columnconfigure(i, weight=1)
    
    def update_statistics(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # إجمالي المنتجات
            cursor.execute("SELECT COUNT(*) FROM products")
            total_products = cursor.fetchone()[0]
            self.total_products_var.set(str(total_products))
            
            # المنتجات قليلة المخزون
            cursor.execute("SELECT COUNT(*) FROM products WHERE current_stock <= min_stock")
            low_stock = cursor.fetchone()[0]
            self.low_stock_var.set(str(low_stock))
            
            # مبيعات اليوم
            cursor.execute('''
                SELECT COALESCE(SUM(final_amount), 0) FROM sales 
                WHERE DATE(created_at) = DATE('now')
            ''')
            today_sales = cursor.fetchone()[0]
            self.today_sales_var.set(f"{today_sales:.2f}")
            
            # إجمالي العملاء
            cursor.execute("SELECT COUNT(*) FROM customers")
            total_customers = cursor.fetchone()[0]
            self.total_customers_var.set(str(total_customers))
            
        except Exception as e:
            print(f"خطأ في تحديث الإحصائيات: {e}")
        finally:
            conn.close()
    
    def open_products(self):
        ProductsWindow(self.root, self.db, self.user)
    
    def open_sales(self):
        try:
            from enhanced_sales_window import EnhancedSalesWindow
            EnhancedSalesWindow(self.root, self.db, self.user)
        except ImportError:
            # العودة للنافذة القديمة في حالة عدم توفر المحسنة
            from sales_window import SalesWindow
            SalesWindow(self.root, self.db, self.user)
    
    def open_purchases(self):
        PurchasesWindow(self.root, self.db, self.user)
    
    def open_suppliers(self):
        SuppliersWindow(self.root, self.db, self.user)
    
    def open_customers(self):
        CustomersWindow(self.root, self.db, self.user)
    
    def open_reports(self):
        try:
            from enhanced_reports import EnhancedReportsWindow
            EnhancedReportsWindow(self.root, self.db, self.user)
        except ImportError:
            # العودة لنافذة التقارير القديمة في حالة عدم توفر المحسنة
            from reports_window import ReportsWindow
            ReportsWindow(self.root, self.db, self.user)
    
    def open_dashboard(self):
        """فتح لوحة التحكم الذكية"""
        try:
            from enhanced_dashboard import EnhancedDashboard
            EnhancedDashboard(self.root, self.db, self.user)
        except ImportError:
            # العودة للوحة التحكم القديمة في حالة عدم توفر المحسنة
            from dashboard_window import DashboardWindow
            DashboardWindow(self.root, self.db, self.user)
    
    def open_inventory_report(self):
        # سيتم تنفيذها لاحقاً
        messagebox.showinfo("قريباً", "تقرير المخزون سيكون متاحاً قريباً")
    
    def open_sales_reports(self):
        # سيتم تنفيذها لاحقاً
        messagebox.showinfo("قريباً", "تقارير المبيعات ستكون متاحة قريباً")
    
    def open_purchases_reports(self):
        # سيتم تنفيذها لاحقاً
        messagebox.showinfo("قريباً", "تقارير المشتريات ستكون متاحة قريباً")
    
    def logout(self):
        if messagebox.askyesno("تأكيد", "هل تريد تسجيل الخروج؟"):
            self.root.destroy()
            from login_window import LoginWindow
            login_app = LoginWindow()
            login_app.run()
    
    @require_permission(Permission.USER_MANAGEMENT)
    def open_user_management(self):
        """فتح نافذة إدارة المستخدمين"""
        UserManagementWindow(self.root, self.db, self.user)
    
    @require_permission(Permission.USER_MANAGEMENT)
    def open_permissions_management(self):
        """فتح نافذة إدارة الصلاحيات"""
        messagebox.showinfo("قريباً", "نافذة إدارة الصلاحيات ستكون متاحة قريباً")
    
    @require_permission(Permission.BACKUP_RESTORE)
    def create_backup(self):
        """إنشاء نسخة احتياطية"""
        try:
            from security_utils import BackupManager
            backup_manager = BackupManager(self.db.db_path)
            backup_path = backup_manager.create_backup()
            
            if backup_path:
                messagebox.showinfo("نجح", f"تم إنشاء النسخة الاحتياطية بنجاح:\n{backup_path}")
            else:
                messagebox.showerror("خطأ", "فشل في إنشاء النسخة الاحتياطية")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في إنشاء النسخة الاحتياطية: {str(e)}")
    
    @require_permission(Permission.AUDIT_LOG)
    def view_audit_log(self):
        """عرض سجل المراجعة"""
        messagebox.showinfo("قريباً", "سجل المراجعة متاح في نافذة إدارة المستخدمين")
    
    def show_user_guide(self):
        """عرض دليل المستخدم"""
        try:
            import webbrowser
            import os
            guide_path = os.path.join(os.getcwd(), "USER_GUIDE.md")
            if os.path.exists(guide_path):
                webbrowser.open(guide_path)
            else:
                messagebox.showinfo("دليل المستخدم", 
                                   "دليل المستخدم متوفر في ملف USER_GUIDE.md")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في فتح دليل المستخدم: {str(e)}")
    
    def show_about(self):
        """عرض معلومات البرنامج"""
        about_text = f"""
{config.APP_NAME}
الإصدار {config.APP_VERSION}

{config.APP_DESCRIPTION}

تصميم وتطوير: {config.APP_AUTHOR}
رقم الهاتف: {config.APP_DEVELOPER_PHONE}

{config.APP_COPYRIGHT}

الميزات:
• إدارة شاملة للمخازن والمنتجات
• نقطة بيع متطورة مع طباعة الفواتير
• تقارير مالية وإحصائية متقدمة
• لوحة تحكم ذكية مع التوقعات
• نظام صلاحيات متقدم
• نسخ احتياطية تلقائية
• أمان وحماية عالية المستوى
        """
        
        # إنشاء نافذة مخصصة للمعلومات
        about_window = tk.Toplevel(self.root)
        about_window.title("حول البرنامج")
        about_window.geometry("500x600")
        about_window.grab_set()
        about_window.transient(self.root)
        
        # توسيط النافذة
        about_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 100,
            self.root.winfo_rooty() + 50
        ))
        
        main_frame = ttk.Frame(about_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # أيقونة البرنامج
        icon_label = ttk.Label(main_frame, text="🏪", font=("Arial", 48))
        icon_label.pack(pady=(0, 20))
        
        # النص
        text_widget = tk.Text(main_frame, wrap=tk.WORD, height=20, width=50,
                             font=("Arial", 11), relief=tk.FLAT, bg="#f0f0f0")
        text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        text_widget.insert(tk.END, about_text.strip())
        text_widget.config(state=tk.DISABLED)
        
        # زر الإغلاق
        ttk.Button(main_frame, text="إغلاق", 
                  command=about_window.destroy).pack()
    
    def show_support_info(self):
        """عرض معلومات الدعم الفني"""
        support_text = f"""
الدعم الفني

المطور: {config.APP_AUTHOR}
رقم الهاتف: {config.APP_DEVELOPER_PHONE}

للحصول على الدعم الفني:
• اتصل على الرقم أعلاه
• أرسل رسالة واتساب
• أرفق لقطة شاشة للمشكلة إن أمكن

ساعات العمل:
السبت - الخميس: 9:00 ص - 6:00 م
الجمعة: مغلق

نوع الدعم المتاح:
• حل المشاكل التقنية
• تدريب على استخدام البرنامج
• طلب ميزات جديدة
• تحديثات البرنامج
        """
        
        messagebox.showinfo("الدعم الفني", support_text.strip())
    
    def run(self):
        self.root.mainloop()