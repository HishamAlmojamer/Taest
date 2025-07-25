#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام إدارة المخازن
برنامج شامل لإدارة المخازن والمبيعات والمشتريات
"""

import sys
import os

# إضافة المجلد الحالي إلى مسار Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from login_window import LoginWindow

def main():
    """الدالة الرئيسية لتشغيل البرنامج"""
    try:
        # تشغيل نافذة تسجيل الدخول
        app = LoginWindow()
        app.run()
    except Exception as e:
        print(f"خطأ في تشغيل البرنامج: {e}")
        input("اضغط Enter للخروج...")

if __name__ == "__main__":
    main()