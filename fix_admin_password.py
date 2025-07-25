#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إصلاح كلمة مرور المدير
"""

from database import Database
import hashlib
import secrets

def fix_admin_password():
    """إصلاح كلمة مرور المدير"""
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # كلمة المرور الجديدة
    password = "admin123"
    
    # إنشاء salt جديد
    salt = secrets.token_hex(32)
    
    # تشفير كلمة المرور
    hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode(), 
                                        salt.encode(), 100000)
    
    # دمج salt مع hash
    stored_password = salt + hashed_password.hex()
    
    print(f"Salt length: {len(salt)}")
    print(f"Hash length: {len(hashed_password.hex())}")
    print(f"Total length: {len(stored_password)}")
    
    # تحديث كلمة المرور في قاعدة البيانات
    cursor.execute('UPDATE users SET password = ? WHERE username = ?', 
                  (stored_password, 'admin'))
    
    conn.commit()
    conn.close()
    
    print("✅ تم تحديث كلمة مرور المدير بنجاح")
    
    # اختبار كلمة المرور الجديدة
    test_login()

def test_login():
    """اختبار تسجيل الدخول"""
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT password FROM users WHERE username = ?', ('admin',))
    stored_password = cursor.fetchone()[0]
    
    test_password = "admin123"
    
    # استخراج salt و hash
    salt = stored_password[:64]
    stored_hash = stored_password[64:]
    
    # حساب hash للكلمة المدخلة
    computed_hash = hashlib.pbkdf2_hmac('sha256', test_password.encode(), 
                                      salt.encode(), 100000)
    
    if computed_hash.hex() == stored_hash:
        print("✅ اختبار تسجيل الدخول نجح")
        return True
    else:
        print("❌ اختبار تسجيل الدخول فشل")
        return False
    
    conn.close()

if __name__ == "__main__":
    print("🔧 إصلاح كلمة مرور المدير...")
    fix_admin_password()