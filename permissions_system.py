#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام الصلاحيات والأدوار
تصميم: المهندس هشام المجمر - 773988932
"""

import sqlite3
from datetime import datetime
from enum import Enum

class UserRole(Enum):
    """أدوار المستخدمين"""
    SUPER_ADMIN = "super_admin"      # مدير عام
    ADMIN = "admin"                  # مدير
    MANAGER = "manager"              # مدير فرع
    CASHIER = "cashier"              # كاشير
    INVENTORY_CLERK = "inventory"    # موظف مخزون
    SALES_REP = "sales"              # مندوب مبيعات
    VIEWER = "viewer"                # مستعرض فقط

class Permission(Enum):
    """الصلاحيات المتاحة"""
    # صلاحيات المنتجات
    PRODUCTS_VIEW = "products_view"
    PRODUCTS_ADD = "products_add"
    PRODUCTS_EDIT = "products_edit"
    PRODUCTS_DELETE = "products_delete"
    PRODUCTS_IMPORT = "products_import"
    PRODUCTS_EXPORT = "products_export"
    
    # صلاحيات المبيعات
    SALES_VIEW = "sales_view"
    SALES_CREATE = "sales_create"
    SALES_EDIT = "sales_edit"
    SALES_DELETE = "sales_delete"
    SALES_REFUND = "sales_refund"
    SALES_DISCOUNT = "sales_discount"
    
    # صلاحيات المشتريات
    PURCHASES_VIEW = "purchases_view"
    PURCHASES_CREATE = "purchases_create"
    PURCHASES_EDIT = "purchases_edit"
    PURCHASES_DELETE = "purchases_delete"
    PURCHASES_APPROVE = "purchases_approve"
    
    # صلاحيات العملاء والموردين
    CUSTOMERS_VIEW = "customers_view"
    CUSTOMERS_MANAGE = "customers_manage"
    SUPPLIERS_VIEW = "suppliers_view"
    SUPPLIERS_MANAGE = "suppliers_manage"
    
    # صلاحيات التقارير
    REPORTS_VIEW = "reports_view"
    REPORTS_FINANCIAL = "reports_financial"
    REPORTS_INVENTORY = "reports_inventory"
    REPORTS_SALES = "reports_sales"
    REPORTS_EXPORT = "reports_export"
    
    # صلاحيات النظام
    SYSTEM_SETTINGS = "system_settings"
    USER_MANAGEMENT = "user_management"
    BACKUP_RESTORE = "backup_restore"
    AUDIT_LOG = "audit_log"
    
    # صلاحيات المخزون
    INVENTORY_VIEW = "inventory_view"
    INVENTORY_ADJUST = "inventory_adjust"
    INVENTORY_TRANSFER = "inventory_transfer"
    
    # صلاحيات متقدمة
    DASHBOARD_ACCESS = "dashboard_access"
    AI_FEATURES = "ai_features"
    ADVANCED_REPORTS = "advanced_reports"
    PRICE_MANAGEMENT = "price_management"

class PermissionManager:
    """مدير الصلاحيات"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.create_permissions_tables()
        self.setup_default_roles()
    
    def create_permissions_tables(self):
        """إنشاء جداول الصلاحيات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول الأدوار
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول الصلاحيات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # جدول ربط الأدوار بالصلاحيات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS role_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                granted_by INTEGER,
                granted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (role_id) REFERENCES roles (id),
                FOREIGN KEY (permission_id) REFERENCES permissions (id),
                FOREIGN KEY (granted_by) REFERENCES users (id),
                UNIQUE(role_id, permission_id)
            )
        ''')
        
        # تحديث جدول المستخدمين لإضافة الدور (إذا لم يكن موجود)
        try:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN role_id INTEGER 
                REFERENCES roles(id) DEFAULT 2
            ''')
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
        
        # جدول صلاحيات المستخدمين الخاصة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                granted BOOLEAN DEFAULT 1,
                granted_by INTEGER,
                granted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (permission_id) REFERENCES permissions (id),
                FOREIGN KEY (granted_by) REFERENCES users (id),
                UNIQUE(user_id, permission_id)
            )
        ''')
        
        # جدول جلسات المستخدمين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def setup_default_roles(self):
        """إعداد الأدوار الافتراضية"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # إدراج الأدوار الافتراضية
        default_roles = [
            (UserRole.SUPER_ADMIN.value, "مدير عام", "صلاحيات كاملة للنظام"),
            (UserRole.ADMIN.value, "مدير", "صلاحيات إدارية شاملة"),
            (UserRole.MANAGER.value, "مدير فرع", "إدارة العمليات اليومية"),
            (UserRole.CASHIER.value, "كاشير", "نقطة البيع والمبيعات"),
            (UserRole.INVENTORY_CLERK.value, "موظف مخزون", "إدارة المخزون والمنتجات"),
            (UserRole.SALES_REP.value, "مندوب مبيعات", "المبيعات والعملاء"),
            (UserRole.VIEWER.value, "مستعرض", "عرض البيانات فقط")
        ]
        
        for role_name, display_name, description in default_roles:
            cursor.execute('''
                INSERT OR IGNORE INTO roles (name, display_name, description)
                VALUES (?, ?, ?)
            ''', (role_name, display_name, description))
        
        # إدراج الصلاحيات
        permissions_data = [
            # صلاحيات المنتجات
            (Permission.PRODUCTS_VIEW.value, "عرض المنتجات", "منتجات", "عرض قائمة المنتجات"),
            (Permission.PRODUCTS_ADD.value, "إضافة منتجات", "منتجات", "إضافة منتجات جديدة"),
            (Permission.PRODUCTS_EDIT.value, "تعديل المنتجات", "منتجات", "تعديل بيانات المنتجات"),
            (Permission.PRODUCTS_DELETE.value, "حذف المنتجات", "منتجات", "حذف المنتجات"),
            (Permission.PRODUCTS_IMPORT.value, "استيراد المنتجات", "منتجات", "استيراد المنتجات من ملف"),
            (Permission.PRODUCTS_EXPORT.value, "تصدير المنتجات", "منتجات", "تصدير بيانات المنتجات"),
            
            # صلاحيات المبيعات
            (Permission.SALES_VIEW.value, "عرض المبيعات", "مبيعات", "عرض فواتير المبيعات"),
            (Permission.SALES_CREATE.value, "إنشاء مبيعات", "مبيعات", "إنشاء فواتير مبيعات جديدة"),
            (Permission.SALES_EDIT.value, "تعديل المبيعات", "مبيعات", "تعديل فواتير المبيعات"),
            (Permission.SALES_DELETE.value, "حذف المبيعات", "مبيعات", "حذف فواتير المبيعات"),
            (Permission.SALES_REFUND.value, "مرتجعات المبيعات", "مبيعات", "معالجة مرتجعات المبيعات"),
            (Permission.SALES_DISCOUNT.value, "خصومات المبيعات", "مبيعات", "تطبيق خصومات على المبيعات"),
            
            # صلاحيات المشتريات
            (Permission.PURCHASES_VIEW.value, "عرض المشتريات", "مشتريات", "عرض فواتير المشتريات"),
            (Permission.PURCHASES_CREATE.value, "إنشاء مشتريات", "مشتريات", "إنشاء فواتير مشتريات جديدة"),
            (Permission.PURCHASES_EDIT.value, "تعديل المشتريات", "مشتريات", "تعديل فواتير المشتريات"),
            (Permission.PURCHASES_DELETE.value, "حذف المشتريات", "مشتريات", "حذف فواتير المشتريات"),
            (Permission.PURCHASES_APPROVE.value, "اعتماد المشتريات", "مشتريات", "اعتماد طلبات الشراء"),
            
            # صلاحيات العملاء والموردين
            (Permission.CUSTOMERS_VIEW.value, "عرض العملاء", "عملاء", "عرض قائمة العملاء"),
            (Permission.CUSTOMERS_MANAGE.value, "إدارة العملاء", "عملاء", "إضافة وتعديل العملاء"),
            (Permission.SUPPLIERS_VIEW.value, "عرض الموردين", "موردين", "عرض قائمة الموردين"),
            (Permission.SUPPLIERS_MANAGE.value, "إدارة الموردين", "موردين", "إضافة وتعديل الموردين"),
            
            # صلاحيات التقارير
            (Permission.REPORTS_VIEW.value, "عرض التقارير", "تقارير", "عرض التقارير الأساسية"),
            (Permission.REPORTS_FINANCIAL.value, "التقارير المالية", "تقارير", "عرض التقارير المالية"),
            (Permission.REPORTS_INVENTORY.value, "تقارير المخزون", "تقارير", "عرض تقارير المخزون"),
            (Permission.REPORTS_SALES.value, "تقارير المبيعات", "تقارير", "عرض تقارير المبيعات"),
            (Permission.REPORTS_EXPORT.value, "تصدير التقارير", "تقارير", "تصدير التقارير"),
            
            # صلاحيات النظام
            (Permission.SYSTEM_SETTINGS.value, "إعدادات النظام", "نظام", "تعديل إعدادات النظام"),
            (Permission.USER_MANAGEMENT.value, "إدارة المستخدمين", "نظام", "إدارة المستخدمين والصلاحيات"),
            (Permission.BACKUP_RESTORE.value, "النسخ الاحتياطية", "نظام", "إنشاء واستعادة النسخ الاحتياطية"),
            (Permission.AUDIT_LOG.value, "سجل المراجعة", "نظام", "عرض سجل العمليات"),
            
            # صلاحيات المخزون
            (Permission.INVENTORY_VIEW.value, "عرض المخزون", "مخزون", "عرض حالة المخزون"),
            (Permission.INVENTORY_ADJUST.value, "تعديل المخزون", "مخزون", "تعديل كميات المخزون"),
            (Permission.INVENTORY_TRANSFER.value, "نقل المخزون", "مخزون", "نقل المخزون بين المواقع"),
            
            # صلاحيات متقدمة
            (Permission.DASHBOARD_ACCESS.value, "لوحة التحكم", "متقدم", "الوصول للوحة التحكم الذكية"),
            (Permission.AI_FEATURES.value, "الميزات الذكية", "متقدم", "استخدام ميزات الذكاء الاصطناعي"),
            (Permission.ADVANCED_REPORTS.value, "التقارير المتقدمة", "متقدم", "التقارير والتحليلات المتقدمة"),
            (Permission.PRICE_MANAGEMENT.value, "إدارة الأسعار", "متقدم", "تعديل أسعار المنتجات")
        ]
        
        for perm_name, display_name, category, description in permissions_data:
            cursor.execute('''
                INSERT OR IGNORE INTO permissions (name, display_name, category, description)
                VALUES (?, ?, ?, ?)
            ''', (perm_name, display_name, category, description))
        
        conn.commit()
        conn.close()
        
        # إعداد صلاحيات الأدوار
        self.setup_role_permissions()
    
    def setup_role_permissions(self):
        """إعداد صلاحيات الأدوار"""
        role_permissions = {
            UserRole.SUPER_ADMIN.value: list(Permission),  # جميع الصلاحيات
            
            UserRole.ADMIN.value: [
                Permission.PRODUCTS_VIEW, Permission.PRODUCTS_ADD, Permission.PRODUCTS_EDIT, Permission.PRODUCTS_DELETE,
                Permission.PRODUCTS_IMPORT, Permission.PRODUCTS_EXPORT,
                Permission.SALES_VIEW, Permission.SALES_CREATE, Permission.SALES_EDIT, Permission.SALES_DELETE,
                Permission.SALES_REFUND, Permission.SALES_DISCOUNT,
                Permission.PURCHASES_VIEW, Permission.PURCHASES_CREATE, Permission.PURCHASES_EDIT, 
                Permission.PURCHASES_DELETE, Permission.PURCHASES_APPROVE,
                Permission.CUSTOMERS_VIEW, Permission.CUSTOMERS_MANAGE,
                Permission.SUPPLIERS_VIEW, Permission.SUPPLIERS_MANAGE,
                Permission.REPORTS_VIEW, Permission.REPORTS_FINANCIAL, Permission.REPORTS_INVENTORY,
                Permission.REPORTS_SALES, Permission.REPORTS_EXPORT,
                Permission.INVENTORY_VIEW, Permission.INVENTORY_ADJUST, Permission.INVENTORY_TRANSFER,
                Permission.DASHBOARD_ACCESS, Permission.AI_FEATURES, Permission.ADVANCED_REPORTS,
                Permission.PRICE_MANAGEMENT, Permission.BACKUP_RESTORE
            ],
            
            UserRole.MANAGER.value: [
                Permission.PRODUCTS_VIEW, Permission.PRODUCTS_ADD, Permission.PRODUCTS_EDIT,
                Permission.SALES_VIEW, Permission.SALES_CREATE, Permission.SALES_EDIT, Permission.SALES_REFUND,
                Permission.PURCHASES_VIEW, Permission.PURCHASES_CREATE, Permission.PURCHASES_EDIT,
                Permission.CUSTOMERS_VIEW, Permission.CUSTOMERS_MANAGE,
                Permission.SUPPLIERS_VIEW, Permission.SUPPLIERS_MANAGE,
                Permission.REPORTS_VIEW, Permission.REPORTS_INVENTORY, Permission.REPORTS_SALES,
                Permission.INVENTORY_VIEW, Permission.INVENTORY_ADJUST,
                Permission.DASHBOARD_ACCESS, Permission.ADVANCED_REPORTS
            ],
            
            UserRole.CASHIER.value: [
                Permission.PRODUCTS_VIEW,
                Permission.SALES_VIEW, Permission.SALES_CREATE, Permission.SALES_REFUND,
                Permission.CUSTOMERS_VIEW, Permission.CUSTOMERS_MANAGE,
                Permission.INVENTORY_VIEW
            ],
            
            UserRole.INVENTORY_CLERK.value: [
                Permission.PRODUCTS_VIEW, Permission.PRODUCTS_ADD, Permission.PRODUCTS_EDIT,
                Permission.PURCHASES_VIEW, Permission.PURCHASES_CREATE,
                Permission.SUPPLIERS_VIEW,
                Permission.INVENTORY_VIEW, Permission.INVENTORY_ADJUST, Permission.INVENTORY_TRANSFER,
                Permission.REPORTS_INVENTORY
            ],
            
            UserRole.SALES_REP.value: [
                Permission.PRODUCTS_VIEW,
                Permission.SALES_VIEW, Permission.SALES_CREATE,
                Permission.CUSTOMERS_VIEW, Permission.CUSTOMERS_MANAGE,
                Permission.REPORTS_SALES
            ],
            
            UserRole.VIEWER.value: [
                Permission.PRODUCTS_VIEW,
                Permission.SALES_VIEW,
                Permission.PURCHASES_VIEW,
                Permission.CUSTOMERS_VIEW,
                Permission.SUPPLIERS_VIEW,
                Permission.REPORTS_VIEW,
                Permission.INVENTORY_VIEW
            ]
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for role_name, permissions in role_permissions.items():
            # الحصول على معرف الدور
            cursor.execute('SELECT id FROM roles WHERE name = ?', (role_name,))
            role_result = cursor.fetchone()
            if not role_result:
                continue
            
            role_id = role_result[0]
            
            for permission in permissions:
                # الحصول على معرف الصلاحية
                cursor.execute('SELECT id FROM permissions WHERE name = ?', (permission.value,))
                perm_result = cursor.fetchone()
                if not perm_result:
                    continue
                
                perm_id = perm_result[0]
                
                # ربط الدور بالصلاحية
                cursor.execute('''
                    INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                    VALUES (?, ?)
                ''', (role_id, perm_id))
        
        conn.commit()
        conn.close()
    
    def check_permission(self, user_id, permission):
        """فحص صلاحية محددة للمستخدم"""
        return self.has_permission(user_id, permission)
    
    def has_permission(self, user_id, permission):
        """التحقق من صلاحية المستخدم"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # التحقق من صلاحيات الدور
            cursor.execute('''
                SELECT 1 FROM users u
                JOIN roles r ON u.role_id = r.id
                JOIN role_permissions rp ON r.id = rp.role_id
                JOIN permissions p ON rp.permission_id = p.id
                WHERE u.id = ? AND p.name = ? AND r.is_active = 1 AND p.is_active = 1
            ''', (user_id, permission.value))
            
            if cursor.fetchone():
                return True
            
            # التحقق من الصلاحيات الخاصة
            cursor.execute('''
                SELECT granted FROM user_permissions up
                JOIN permissions p ON up.permission_id = p.id
                WHERE up.user_id = ? AND p.name = ? 
                AND (up.expires_at IS NULL OR up.expires_at > datetime('now'))
            ''', (user_id, permission.value))
            
            result = cursor.fetchone()
            return result[0] if result else False
            
        finally:
            conn.close()
    
    def get_user_permissions(self, user_id):
        """الحصول على جميع صلاحيات المستخدم"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # صلاحيات الدور
            cursor.execute('''
                SELECT p.name, p.display_name, p.category
                FROM users u
                JOIN roles r ON u.role_id = r.id
                JOIN role_permissions rp ON r.id = rp.role_id
                JOIN permissions p ON rp.permission_id = p.id
                WHERE u.id = ? AND r.is_active = 1 AND p.is_active = 1
            ''', (user_id,))
            
            role_permissions = cursor.fetchall()
            
            # الصلاحيات الخاصة
            cursor.execute('''
                SELECT p.name, p.display_name, p.category, up.granted
                FROM user_permissions up
                JOIN permissions p ON up.permission_id = p.id
                WHERE up.user_id = ? 
                AND (up.expires_at IS NULL OR up.expires_at > datetime('now'))
            ''', (user_id,))
            
            user_permissions = cursor.fetchall()
            
            # دمج الصلاحيات
            all_permissions = {}
            
            # إضافة صلاحيات الدور
            for perm_name, display_name, category in role_permissions:
                all_permissions[perm_name] = {
                    'display_name': display_name,
                    'category': category,
                    'granted': True,
                    'source': 'role'
                }
            
            # إضافة/تعديل الصلاحيات الخاصة
            for perm_name, display_name, category, granted in user_permissions:
                all_permissions[perm_name] = {
                    'display_name': display_name,
                    'category': category,
                    'granted': bool(granted),
                    'source': 'user'
                }
            
            return all_permissions
            
        finally:
            conn.close()
    
    def grant_permission(self, user_id, permission, granted_by, expires_at=None):
        """منح صلاحية خاصة للمستخدم"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # الحصول على معرف الصلاحية
            cursor.execute('SELECT id FROM permissions WHERE name = ?', (permission.value,))
            perm_result = cursor.fetchone()
            if not perm_result:
                return False
            
            perm_id = perm_result[0]
            
            # منح الصلاحية
            cursor.execute('''
                INSERT OR REPLACE INTO user_permissions 
                (user_id, permission_id, granted, granted_by, expires_at)
                VALUES (?, ?, 1, ?, ?)
            ''', (user_id, perm_id, granted_by, expires_at))
            
            conn.commit()
            return True
            
        finally:
            conn.close()
    
    def revoke_permission(self, user_id, permission, granted_by):
        """سحب صلاحية من المستخدم"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # الحصول على معرف الصلاحية
            cursor.execute('SELECT id FROM permissions WHERE name = ?', (permission.value,))
            perm_result = cursor.fetchone()
            if not perm_result:
                return False
            
            perm_id = perm_result[0]
            
            # سحب الصلاحية
            cursor.execute('''
                INSERT OR REPLACE INTO user_permissions 
                (user_id, permission_id, granted, granted_by)
                VALUES (?, ?, 0, ?)
            ''', (user_id, perm_id, granted_by))
            
            conn.commit()
            return True
            
        finally:
            conn.close()
    
    def change_user_role(self, user_id, new_role, changed_by):
        """تغيير دور المستخدم"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # الحصول على معرف الدور الجديد
            cursor.execute('SELECT id FROM roles WHERE name = ?', (new_role.value,))
            role_result = cursor.fetchone()
            if not role_result:
                return False
            
            role_id = role_result[0]
            
            # تحديث دور المستخدم
            cursor.execute('''
                UPDATE users SET role_id = ? WHERE id = ?
            ''', (role_id, user_id))
            
            conn.commit()
            return True
            
        finally:
            conn.close()

def require_permission(permission):
    """ديكوريتر للتحقق من الصلاحيات"""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if hasattr(self, 'user') and hasattr(self, 'permission_manager'):
                if not self.permission_manager.has_permission(self.user['id'], permission):
                    from tkinter import messagebox
                    messagebox.showerror("غير مسموح", 
                                       f"ليس لديك صلاحية للوصول لهذه الميزة\nالصلاحية المطلوبة: {permission.value}")
                    return
            return func(self, *args, **kwargs)
        return wrapper
    return decorator