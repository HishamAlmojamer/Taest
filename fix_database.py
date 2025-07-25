#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إصلاح مشاكل قاعدة البيانات
"""

import sqlite3
import os

def fix_database():
    """إصلاح مشاكل قاعدة البيانات"""
    db_path = "warehouse_management.db"
    
    if not os.path.exists(db_path):
        print("❌ قاعدة البيانات غير موجودة")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # فحص وجود عمود role_id في جدول users
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print("أعمدة جدول users:", column_names)
        
        if 'role_id' not in column_names:
            print("✅ إضافة عمود role_id...")
            cursor.execute('ALTER TABLE users ADD COLUMN role_id INTEGER REFERENCES roles(id) DEFAULT 2')
            conn.commit()
            print("✅ تم إضافة عمود role_id")
        else:
            print("✅ عمود role_id موجود بالفعل")
        
        # تحديث role_id للمستخدم admin
        cursor.execute('UPDATE users SET role_id = 1 WHERE username = "admin"')
        conn.commit()
        print("✅ تم تحديث دور المدير")
        
        # فحص البيانات
        cursor.execute('SELECT username, role_id FROM users')
        users = cursor.fetchall()
        print("المستخدمين:", users)
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 إصلاح قاعدة البيانات...")
    fix_database()