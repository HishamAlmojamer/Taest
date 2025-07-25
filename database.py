import sqlite3
import hashlib
from datetime import datetime

class Database:
    def __init__(self, db_name="warehouse_management.db"):
        self.db_name = db_name
        self.db_path = db_name  # إضافة خاصية db_path
        self.create_tables()
        self.create_default_admin()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def create_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # جدول المستخدمين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # جدول الفئات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول المنتجات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                barcode TEXT UNIQUE,
                category_id INTEGER,
                unit TEXT NOT NULL,
                purchase_price REAL NOT NULL,
                selling_price REAL NOT NULL,
                min_stock INTEGER DEFAULT 0,
                current_stock INTEGER DEFAULT 0,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')
        
        # جدول الموردين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_person TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول العملاء
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول المشتريات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER,
                total_amount REAL NOT NULL,
                discount REAL DEFAULT 0,
                final_amount REAL NOT NULL,
                payment_status TEXT DEFAULT 'pending',
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # جدول تفاصيل المشتريات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id INTEGER,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                FOREIGN KEY (purchase_id) REFERENCES purchases (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        # جدول المبيعات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                total_amount REAL NOT NULL,
                discount REAL DEFAULT 0,
                final_amount REAL NOT NULL,
                payment_method TEXT DEFAULT 'cash',
                payment_status TEXT DEFAULT 'paid',
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # جدول تفاصيل المبيعات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        # جدول حركات المخزون
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                movement_type TEXT NOT NULL, -- 'in', 'out', 'adjustment'
                quantity INTEGER NOT NULL,
                reference_type TEXT, -- 'purchase', 'sale', 'adjustment'
                reference_id INTEGER,
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_default_admin(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # التحقق من وجود مستخدم admin
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            # إنشاء كلمة مرور مشفرة
            password_hash = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute('''
                INSERT INTO users (username, password, full_name, role)
                VALUES (?, ?, ?, ?)
            ''', ("admin", password_hash, "مدير النظام", "admin"))
            conn.commit()
        
        conn.close()
    
    def authenticate_user(self, username, password):
        """التحقق من صحة بيانات المستخدم"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # جلب بيانات المستخدم
            cursor.execute('''
                SELECT id, username, password, full_name, role, role_id, is_active 
                FROM users WHERE username = ?
            ''', (username,))
            
            user_data = cursor.fetchone()
            
            if not user_data:
                return None
            
            user_id, db_username, stored_password, full_name, role, role_id, is_active = user_data
            
            # التحقق من أن المستخدم نشط
            if not is_active:
                return None
            
            # التحقق من كلمة المرور
            if self._verify_password(password, stored_password):
                # تحديث وقت آخر دخول (إذا كان العمود موجود)
                try:
                    cursor.execute('''
                        UPDATE users SET last_login = ? WHERE id = ?
                    ''', (datetime.now().isoformat(), user_id))
                    conn.commit()
                except sqlite3.OperationalError:
                    # العمود غير موجود، تجاهل التحديث
                    pass
                
                return {
                    'id': user_id,
                    'username': db_username,
                    'full_name': full_name,
                    'role': role,
                    'role_id': role_id
                }
            
            return None
            
        except Exception as e:
            print(f"خطأ في التحقق من المستخدم: {e}")
            return None
        finally:
            conn.close()
    
    def _verify_password(self, password, stored_password):
        """التحقق من كلمة المرور"""
        try:
            if len(stored_password) == 128:  # كلمة مرور مشفرة بـ PBKDF2
                salt = stored_password[:64]
                stored_hash = stored_password[64:]
                
                # حساب hash للكلمة المدخلة
                computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), 
                                                  salt.encode(), 100000)
                
                return computed_hash.hex() == stored_hash
            else:
                # كلمة مرور قديمة (SHA256 أو نص عادي)
                if stored_password == password:  # نص عادي
                    return True
                elif stored_password == hashlib.sha256(password.encode()).hexdigest():  # SHA256
                    return True
                else:
                    return False
        except Exception as e:
            print(f"خطأ في التحقق من كلمة المرور: {e}")
            return False
    
    def add_category(self, name, description=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO categories (name, description)
                VALUES (?, ?)
            ''', (name, description))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_categories(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description FROM categories ORDER BY name")
        categories = cursor.fetchall()
        conn.close()
        return categories
    
    def add_product(self, name, barcode, category_id, unit, purchase_price, selling_price, min_stock, description=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO products (name, barcode, category_id, unit, purchase_price, selling_price, min_stock, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, barcode, category_id, unit, purchase_price, selling_price, min_stock, description))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_products(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.id, p.name, p.barcode, c.name, p.unit, p.purchase_price, 
                   p.selling_price, p.current_stock, p.min_stock
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            ORDER BY p.name
        ''')
        products = cursor.fetchall()
        conn.close()
        return products
    
    def update_stock(self, product_id, quantity, movement_type, reference_type=None, reference_id=None, user_id=None, notes=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # تحديث المخزون الحالي
            if movement_type == 'in':
                cursor.execute('''
                    UPDATE products SET current_stock = current_stock + ?
                    WHERE id = ?
                ''', (quantity, product_id))
            elif movement_type == 'out':
                cursor.execute('''
                    UPDATE products SET current_stock = current_stock - ?
                    WHERE id = ?
                ''', (quantity, product_id))
            
            # إضافة حركة المخزون
            cursor.execute('''
                INSERT INTO stock_movements (product_id, movement_type, quantity, reference_type, reference_id, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (product_id, movement_type, quantity, reference_type, reference_id, notes, user_id))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def add_supplier(self, name, contact_person="", phone="", email="", address=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO suppliers (name, contact_person, phone, email, address)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, contact_person, phone, email, address))
        conn.commit()
        conn.close()
        return True
    
    def get_suppliers(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, contact_person, phone, email FROM suppliers ORDER BY name")
        suppliers = cursor.fetchall()
        conn.close()
        return suppliers
    
    def add_customer(self, name, phone="", email="", address=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO customers (name, phone, email, address)
            VALUES (?, ?, ?, ?)
        ''', (name, phone, email, address))
        conn.commit()
        conn.close()
        return True
    
    def get_customers(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, phone, email FROM customers ORDER BY name")
        customers = cursor.fetchall()
        conn.close()
        return customers