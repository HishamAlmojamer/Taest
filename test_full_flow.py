#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار التدفق الكامل للنظام
"""

import sys
import os
import threading
import time

# إضافة المجلد الحالي إلى مسار Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_login_to_main_flow():
    """اختبار التدفق من تسجيل الدخول إلى النافذة الرئيسية"""
    print("🧪 اختبار التدفق الكامل...")
    
    try:
        # اختبار 1: تسجيل الدخول
        print("1️⃣ اختبار تسجيل الدخول...")
        from database import Database
        db = Database()
        
        user = db.authenticate_user("admin", "admin123")
        if not user:
            print("❌ فشل في تسجيل الدخول")
            return False
        
        print("✅ تسجيل الدخول نجح")
        print(f"   المستخدم: {user['full_name']}")
        print(f"   الدور: {user['role']}")
        
        # اختبار 2: إنشاء النافذة الرئيسية
        print("\n2️⃣ اختبار النافذة الرئيسية...")
        from main_window import MainWindow
        
        # محاكاة إنشاء النافذة الرئيسية
        try:
            main_app = MainWindow(user)
            print("✅ تم إنشاء النافذة الرئيسية بنجاح")
            
            # اختبار الوصول للميزات
            print("\n3️⃣ اختبار الوصول للميزات...")
            
            # اختبار نظام الصلاحيات
            if hasattr(main_app, 'permission_manager'):
                print("✅ نظام الصلاحيات متاح")
            else:
                print("⚠️ نظام الصلاحيات غير متاح")
            
            # اختبار قاعدة البيانات
            if hasattr(main_app, 'db'):
                print("✅ قاعدة البيانات متاحة")
            else:
                print("⚠️ قاعدة البيانات غير متاحة")
            
            # إغلاق النافذة بعد ثانية واحدة
            def close_window():
                time.sleep(1)
                main_app.root.quit()
                main_app.root.destroy()
            
            # تشغيل النافذة لفترة قصيرة
            threading.Thread(target=close_window, daemon=True).start()
            main_app.root.mainloop()
            
            print("✅ النافذة الرئيسية عملت بنجاح")
            return True
            
        except Exception as e:
            print(f"❌ خطأ في النافذة الرئيسية: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_login_window_creation():
    """اختبار إنشاء نافذة تسجيل الدخول"""
    print("\n🧪 اختبار نافذة تسجيل الدخول...")
    
    try:
        from login_window import LoginWindow
        
        # إنشاء النافذة
        login_app = LoginWindow()
        print("✅ تم إنشاء نافذة تسجيل الدخول")
        
        # اختبار الدالة authenticate مباشرة
        print("🔐 اختبار دالة التحقق...")
        
        # محاكاة تسجيل الدخول
        login_app.username_var.set("admin")
        login_app.password_var.set("admin123")
        
        # التحقق من البيانات
        user = login_app.db.authenticate_user("admin", "admin123")
        
        if user:
            print("✅ التحقق من البيانات نجح")
            
            # محاكاة فتح النافذة الرئيسية
            print("🚀 محاكاة فتح النافذة الرئيسية...")
            
            # إغلاق نافذة تسجيل الدخول
            login_app.root.destroy()
            
            # فتح النافذة الرئيسية
            from main_window import MainWindow
            main_app = MainWindow(user)
            
            # إغلاق تلقائي بعد ثانية
            def auto_close():
                time.sleep(1)
                main_app.root.quit()
                main_app.root.destroy()
            
            threading.Thread(target=auto_close, daemon=True).start()
            main_app.root.mainloop()
            
            print("✅ الانتقال من تسجيل الدخول للنافذة الرئيسية نجح!")
            return True
        else:
            print("❌ فشل في التحقق من البيانات")
            login_app.root.destroy()
            return False
            
    except Exception as e:
        print(f"❌ خطأ في اختبار نافذة تسجيل الدخول: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """الدالة الرئيسية للاختبار"""
    print("="*60)
    print("🧪 اختبار التدفق الكامل للنظام")
    print("="*60)
    
    # اختبار 1: التدفق الكامل
    test1_result = test_login_to_main_flow()
    
    # اختبار 2: نافذة تسجيل الدخول
    test2_result = test_login_window_creation()
    
    print("\n" + "="*60)
    print("📊 نتائج الاختبارات:")
    print(f"   التدفق الكامل: {'✅ نجح' if test1_result else '❌ فشل'}")
    print(f"   نافذة تسجيل الدخول: {'✅ نجح' if test2_result else '❌ فشل'}")
    
    if test1_result and test2_result:
        print("\n🎉 جميع الاختبارات نجحت!")
        print("✅ النظام جاهز للاستخدام")
        print("\n📋 لتشغيل النظام:")
        print("   python start.py")
        print("   أو")
        print("   start.bat")
    else:
        print("\n⚠️ بعض الاختبارات فشلت")
        print("❌ النظام يحتاج لمراجعة")
    
    print("="*60)

if __name__ == "__main__":
    main()