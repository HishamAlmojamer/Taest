#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار تسجيل الدخول المحدث
"""

from database import Database

def test_login():
    """اختبار تسجيل الدخول"""
    print("🔐 اختبار تسجيل الدخول المحدث...")
    
    db = Database()
    
    # اختبار بيانات صحيحة
    user = db.authenticate_user("admin", "admin123")
    
    if user:
        print("✅ تسجيل الدخول نجح!")
        print(f"   المعرف: {user['id']}")
        print(f"   اسم المستخدم: {user['username']}")
        print(f"   الاسم الكامل: {user['full_name']}")
        print(f"   الدور: {user['role']}")
        print(f"   معرف الدور: {user['role_id']}")
        return True
    else:
        print("❌ تسجيل الدخول فشل!")
        return False

def test_wrong_password():
    """اختبار كلمة مرور خاطئة"""
    print("\n🔐 اختبار كلمة مرور خاطئة...")
    
    db = Database()
    user = db.authenticate_user("admin", "wrong_password")
    
    if user:
        print("❌ خطأ: تم قبول كلمة مرور خاطئة!")
        return False
    else:
        print("✅ تم رفض كلمة المرور الخاطئة بشكل صحيح")
        return True

def test_wrong_username():
    """اختبار اسم مستخدم خاطئ"""
    print("\n🔐 اختبار اسم مستخدم خاطئ...")
    
    db = Database()
    user = db.authenticate_user("wrong_user", "admin123")
    
    if user:
        print("❌ خطأ: تم قبول اسم مستخدم خاطئ!")
        return False
    else:
        print("✅ تم رفض اسم المستخدم الخاطئ بشكل صحيح")
        return True

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 اختبار نظام تسجيل الدخول")
    print("=" * 50)
    
    test1 = test_login()
    test2 = test_wrong_password()
    test3 = test_wrong_username()
    
    print("\n" + "=" * 50)
    print("📊 نتائج الاختبار:")
    print(f"   تسجيل دخول صحيح: {'✅ نجح' if test1 else '❌ فشل'}")
    print(f"   رفض كلمة مرور خاطئة: {'✅ نجح' if test2 else '❌ فشل'}")
    print(f"   رفض اسم مستخدم خاطئ: {'✅ نجح' if test3 else '❌ فشل'}")
    
    if test1 and test2 and test3:
        print("\n🎉 جميع الاختبارات نجحت! النظام جاهز للاستخدام")
    else:
        print("\n⚠️ بعض الاختبارات فشلت. يحتاج النظام لمراجعة")
    
    print("=" * 50)