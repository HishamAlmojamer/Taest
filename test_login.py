#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار تسجيل الدخول
"""

from database import Database
import hashlib

def test_login():
    """اختبار تسجيل الدخول"""
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # جلب بيانات المستخدم
    cursor.execute('SELECT id, username, password, full_name, is_active FROM users WHERE username = ?', ('admin',))
    user = cursor.fetchone()
    
    if not user:
        print("❌ المستخدم غير موجود")
        return False
    
    print(f"✅ المستخدم موجود: {user[1]} - {user[3]}")
    
    # اختبار كلمة المرور
    stored_password = user[2]
    test_password = "admin123"
    
    if len(stored_password) > 64:  # كلمة مرور مشفرة
        salt = stored_password[:64]
        stored_hash = stored_password[64:]
        
        # حساب الهاش
        computed_hash = hashlib.pbkdf2_hmac('sha256', test_password.encode(), 
                                          salt.encode(), 100000)
        
        if computed_hash.hex() == stored_hash:
            print("✅ كلمة المرور صحيحة")
            return True
        else:
            print("❌ كلمة المرور خاطئة")
            return False
    else:
        # كلمة مرور غير مشفرة (قديمة)
        if stored_password == test_password:
            print("✅ كلمة المرور صحيحة (غير مشفرة)")
            return True
        else:
            print("❌ كلمة المرور خاطئة")
            return False
    
    conn.close()

if __name__ == "__main__":
    print("🔐 اختبار تسجيل الدخول...")
    result = test_login()
    print(f"النتيجة: {'نجح' if result else 'فشل'}")