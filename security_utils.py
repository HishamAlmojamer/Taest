#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أدوات الأمان والحماية
"""

import hashlib
import secrets
import os
import json
from datetime import datetime, timedelta
import sqlite3

class SecurityManager:
    """مدير الأمان"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.failed_attempts = {}
        self.max_attempts = 5
        self.lockout_duration = 30  # دقيقة
    
    def hash_password(self, password, salt=None):
        """تشفير كلمة المرور"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        # استخدام PBKDF2 للتشفير
        key = hashlib.pbkdf2_hmac('sha256', 
                                 password.encode('utf-8'), 
                                 salt.encode('utf-8'), 
                                 100000)  # 100,000 تكرار
        
        return salt + key.hex()
    
    def verify_password(self, password, hashed_password):
        """التحقق من كلمة المرور"""
        try:
            salt = hashed_password[:64]  # أول 64 حرف هو الـ salt
            key = hashed_password[64:]
            
            new_key = hashlib.pbkdf2_hmac('sha256',
                                         password.encode('utf-8'),
                                         salt.encode('utf-8'),
                                         100000)
            
            return new_key.hex() == key
        except:
            return False
    
    def is_account_locked(self, username):
        """التحقق من قفل الحساب"""
        if username not in self.failed_attempts:
            return False
        
        attempts_data = self.failed_attempts[username]
        
        # التحقق من انتهاء فترة القفل
        if datetime.now() > attempts_data['locked_until']:
            del self.failed_attempts[username]
            return False
        
        return attempts_data['count'] >= self.max_attempts
    
    def record_failed_attempt(self, username):
        """تسجيل محاولة فاشلة"""
        now = datetime.now()
        
        if username not in self.failed_attempts:
            self.failed_attempts[username] = {
                'count': 1,
                'first_attempt': now,
                'locked_until': now
            }
        else:
            self.failed_attempts[username]['count'] += 1
            
            # قفل الحساب إذا تجاوز الحد الأقصى
            if self.failed_attempts[username]['count'] >= self.max_attempts:
                self.failed_attempts[username]['locked_until'] = now + timedelta(minutes=self.lockout_duration)
    
    def reset_failed_attempts(self, username):
        """إعادة تعيين المحاولات الفاشلة"""
        if username in self.failed_attempts:
            del self.failed_attempts[username]
    
    def generate_session_token(self):
        """إنشاء رمز جلسة"""
        return secrets.token_urlsafe(32)
    
    def log_security_event(self, event_type, username, details=""):
        """تسجيل أحداث الأمان"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'username': username,
                'details': details,
                'ip_address': 'localhost'  # يمكن تحسينه لاحقاً
            }
            
            # حفظ في ملف السجل
            with open('security_log.json', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
                
        except Exception as e:
            print(f"خطأ في تسجيل حدث الأمان: {e}")
    
    def check_password_strength(self, password):
        """فحص قوة كلمة المرور"""
        issues = []
        
        if len(password) < 8:
            issues.append("كلمة المرور يجب أن تكون 8 أحرف على الأقل")
        
        if not any(c.isupper() for c in password):
            issues.append("يجب أن تحتوي على حرف كبير واحد على الأقل")
        
        if not any(c.islower() for c in password):
            issues.append("يجب أن تحتوي على حرف صغير واحد على الأقل")
        
        if not any(c.isdigit() for c in password):
            issues.append("يجب أن تحتوي على رقم واحد على الأقل")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("يجب أن تحتوي على رمز خاص واحد على الأقل")
        
        return len(issues) == 0, issues
    
    def encrypt_sensitive_data(self, data):
        """تشفير البيانات الحساسة"""
        try:
            from cryptography.fernet import Fernet
            
            # إنشاء مفتاح التشفير (يجب حفظه بأمان)
            key = Fernet.generate_key()
            cipher_suite = Fernet(key)
            
            encrypted_data = cipher_suite.encrypt(data.encode('utf-8'))
            
            return {
                'key': key.decode('utf-8'),
                'data': encrypted_data.decode('utf-8')
            }
            
        except ImportError:
            # إذا لم تكن مكتبة التشفير متوفرة، استخدم base64
            import base64
            encoded = base64.b64encode(data.encode('utf-8'))
            return {
                'key': 'base64',
                'data': encoded.decode('utf-8')
            }
    
    def decrypt_sensitive_data(self, encrypted_data, key):
        """فك تشفير البيانات الحساسة"""
        try:
            if key == 'base64':
                import base64
                return base64.b64decode(encrypted_data['data']).decode('utf-8')
            
            from cryptography.fernet import Fernet
            cipher_suite = Fernet(key.encode('utf-8'))
            decrypted_data = cipher_suite.decrypt(encrypted_data['data'].encode('utf-8'))
            
            return decrypted_data.decode('utf-8')
            
        except:
            return None

class AuditLogger:
    """مسجل المراجعة"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.create_audit_table()
    
    def create_audit_table(self):
        """إنشاء جدول المراجعة"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    table_name TEXT,
                    record_id INTEGER,
                    old_values TEXT,
                    new_values TEXT,
                    ip_address TEXT,
                    user_agent TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"خطأ في إنشاء جدول المراجعة: {e}")
    
    def log_action(self, user_id, action, table_name=None, record_id=None, 
                   old_values=None, new_values=None):
        """تسجيل إجراء"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO audit_log 
                (timestamp, user_id, action, table_name, record_id, old_values, new_values, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                user_id,
                action,
                table_name,
                record_id,
                json.dumps(old_values, ensure_ascii=False) if old_values else None,
                json.dumps(new_values, ensure_ascii=False) if new_values else None,
                'localhost'
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"خطأ في تسجيل الإجراء: {e}")
    
    def get_audit_trail(self, user_id=None, action=None, table_name=None, 
                       from_date=None, to_date=None, limit=100):
        """الحصول على سجل المراجعة"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM audit_log WHERE 1=1"
            params = []
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if action:
                query += " AND action = ?"
                params.append(action)
            
            if table_name:
                query += " AND table_name = ?"
                params.append(table_name)
            
            if from_date:
                query += " AND timestamp >= ?"
                params.append(from_date)
            
            if to_date:
                query += " AND timestamp <= ?"
                params.append(to_date)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"خطأ في جلب سجل المراجعة: {e}")
            return []

class BackupManager:
    """مدير النسخ الاحتياطية"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.backup_dir = "backups"
        
        # إنشاء مجلد النسخ الاحتياطية
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_backup(self, backup_name=None):
        """إنشاء نسخة احتياطية"""
        try:
            if backup_name is None:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # نسخ قاعدة البيانات
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            # ضغط النسخة الاحتياطية
            import zipfile
            zip_path = backup_path + ".zip"
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(backup_path, backup_name)
            
            # حذف الملف غير المضغوط
            os.remove(backup_path)
            
            return zip_path
            
        except Exception as e:
            print(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
            return None
    
    def restore_backup(self, backup_path):
        """استعادة نسخة احتياطية"""
        try:
            import zipfile
            import shutil
            
            # فك ضغط النسخة الاحتياطية
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(self.backup_dir)
            
            # العثور على ملف قاعدة البيانات
            extracted_files = os.listdir(self.backup_dir)
            db_file = None
            
            for file in extracted_files:
                if file.endswith('.db'):
                    db_file = os.path.join(self.backup_dir, file)
                    break
            
            if db_file:
                # استبدال قاعدة البيانات الحالية
                shutil.copy2(db_file, self.db_path)
                os.remove(db_file)
                return True
            
            return False
            
        except Exception as e:
            print(f"خطأ في استعادة النسخة الاحتياطية: {e}")
            return False
    
    def schedule_automatic_backup(self, interval_hours=24):
        """جدولة النسخ الاحتياطية التلقائية"""
        import threading
        import time
        
        def backup_worker():
            while True:
                self.create_backup()
                time.sleep(interval_hours * 3600)  # تحويل الساعات إلى ثوان
        
        backup_thread = threading.Thread(target=backup_worker, daemon=True)
        backup_thread.start()
    
    def cleanup_old_backups(self, keep_days=30):
        """تنظيف النسخ الاحتياطية القديمة"""
        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            for filename in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, filename)
                
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        print(f"تم حذف النسخة الاحتياطية القديمة: {filename}")
            
        except Exception as e:
            print(f"خطأ في تنظيف النسخ الاحتياطية: {e}")

class DataIntegrityChecker:
    """فاحص سلامة البيانات"""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def check_database_integrity(self):
        """فحص سلامة قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # فحص سلامة قاعدة البيانات
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            conn.close()
            
            return result[0] == "ok"
            
        except Exception as e:
            print(f"خطأ في فحص سلامة قاعدة البيانات: {e}")
            return False
    
    def check_referential_integrity(self):
        """فحص سلامة المراجع"""
        issues = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # فحص المنتجات بدون فئات صحيحة
            cursor.execute('''
                SELECT p.id, p.name FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.category_id IS NOT NULL AND c.id IS NULL
            ''')
            
            orphaned_products = cursor.fetchall()
            if orphaned_products:
                issues.append(f"منتجات بفئات غير موجودة: {len(orphaned_products)}")
            
            # فحص عناصر المبيعات بدون منتجات صحيحة
            cursor.execute('''
                SELECT si.id FROM sale_items si
                LEFT JOIN products p ON si.product_id = p.id
                WHERE p.id IS NULL
            ''')
            
            orphaned_sale_items = cursor.fetchall()
            if orphaned_sale_items:
                issues.append(f"عناصر مبيعات بمنتجات غير موجودة: {len(orphaned_sale_items)}")
            
            conn.close()
            
            return len(issues) == 0, issues
            
        except Exception as e:
            return False, [f"خطأ في فحص سلامة المراجع: {e}"]
    
    def fix_data_issues(self):
        """إصلاح مشاكل البيانات"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # إصلاح المنتجات بدون فئات
            cursor.execute('''
                UPDATE products SET category_id = NULL
                WHERE category_id NOT IN (SELECT id FROM categories)
            ''')
            
            # حذف عناصر المبيعات المعطلة
            cursor.execute('''
                DELETE FROM sale_items
                WHERE product_id NOT IN (SELECT id FROM products)
            ''')
            
            # حذف عناصر المشتريات المعطلة
            cursor.execute('''
                DELETE FROM purchase_items
                WHERE product_id NOT IN (SELECT id FROM products)
            ''')
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"خطأ في إصلاح مشاكل البيانات: {e}")
            return False