#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إصلاح أعمدة قاعدة البيانات المفقودة
"""

import sqlite3
import os

def fix_database_columns():
    """إضافة الأعمدة المفقودة لقاعدة البيانات"""
    db_path = "warehouse_management.db"
    
    if not os.path.exists(db_path):
        print("❌ قاعدة البيانات غير موجودة")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔧 إصلاح أعمدة قاعدة البيانات...")
        
        # فحص أعمدة جدول users
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"الأعمدة الحالية في جدول users: {column_names}")
        
        # إضافة الأعمدة المفقودة
        columns_to_add = [
            ("email", "TEXT"),
            ("phone", "TEXT"),
            ("last_login", "TEXT"),
            ("created_at", "TEXT DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TEXT")
        ]
        
        for column_name, column_type in columns_to_add:
            if column_name not in column_names:
                try:
                    cursor.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_type}')
                    print(f"✅ تم إضافة عمود {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"⚠️ تحذير: فشل في إضافة عمود {column_name}: {e}")
            else:
                print(f"✅ عمود {column_name} موجود بالفعل")
        
        # تحديث البيانات الافتراضية
        cursor.execute('''
            UPDATE users 
            SET created_at = COALESCE(created_at, datetime('now')),
                email = COALESCE(email, ''),
                phone = COALESCE(phone, '')
            WHERE created_at IS NULL OR created_at = ''
        ''')
        
        conn.commit()
        
        # فحص النتيجة النهائية
        cursor.execute("PRAGMA table_info(users)")
        final_columns = cursor.fetchall()
        final_column_names = [col[1] for col in final_columns]
        
        print(f"الأعمدة النهائية في جدول users: {final_column_names}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 إصلاح أعمدة قاعدة البيانات")
    print("=" * 60)
    
    success = fix_database_columns()
    
    if success:
        print("\n✅ تم إصلاح قاعدة البيانات بنجاح!")
    else:
        print("\n❌ فشل في إصلاح قاعدة البيانات")
    
    print("=" * 60)