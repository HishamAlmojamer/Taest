# إعدادات البرنامج المتقدمة

import os
from datetime import datetime

# معلومات التطبيق
APP_NAME = "نظام إدارة المخازن المتطور"
APP_VERSION = "3.0"
APP_AUTHOR = "المهندس هشام المجمر"
APP_DEVELOPER_PHONE = "773988932"
APP_DESCRIPTION = "نظام شامل ومتطور لإدارة المخازن والمبيعات مع الذكاء الاصطناعي"
APP_COPYRIGHT = f"© 2024 {APP_AUTHOR} - جميع الحقوق محفوظة"

# إعدادات قاعدة البيانات
DATABASE_NAME = "warehouse_management.db"
DATABASE_BACKUP_INTERVAL = 24  # ساعة
DATABASE_CLEANUP_DAYS = 365    # الاحتفاظ بالبيانات لسنة واحدة

# إعدادات النوافذ
MAIN_WINDOW_TITLE = f"🏪 {APP_NAME}"
MAIN_WINDOW_SIZE = "1400x800"
MAIN_WINDOW_MIN_SIZE = (1200, 700)

LOGIN_WINDOW_TITLE = f"{APP_NAME} - تسجيل الدخول"
LOGIN_WINDOW_SIZE = "450x400"

# المستخدم الافتراضي
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_ADMIN_FULLNAME = "مدير النظام"

# إعدادات الأمان
MAX_LOGIN_ATTEMPTS = 5
ACCOUNT_LOCKOUT_DURATION = 30  # دقيقة
SESSION_TIMEOUT = 120          # دقيقة
PASSWORD_MIN_LENGTH = 8
REQUIRE_STRONG_PASSWORDS = True

# إعدادات العرض
FONTS = {
    'default': ("Arial", 10),
    'header': ("Arial", 12, "bold"),
    'title': ("Arial", 16, "bold"),
    'button': ("Arial", 11, "bold"),
    'small': ("Arial", 9)
}

# ألوان النظام
COLORS = {
    'primary': "#2196F3",
    'secondary': "#FFC107",
    'success': "#4CAF50",
    'warning': "#FF9800",
    'error': "#F44336",
    'info': "#2196F3",
    'light': "#F5F5F5",
    'dark': "#212121",
    'low_stock': "#ffcccc",
    'warning_stock': "#fff3cd",
    'good_stock': "#d4edda"
}

# إعدادات المخزون
LOW_STOCK_THRESHOLD = 0.2      # 20% من الحد الأدنى
WARNING_STOCK_THRESHOLD = 0.5  # 50% من الحد الأدنى
AUTO_REORDER_ENABLED = True
REORDER_SAFETY_FACTOR = 1.5    # عامل الأمان لإعادة الطلب

# إعدادات التقارير
REPORTS_PER_PAGE = 50
DEFAULT_REPORT_FORMAT = "PDF"
AUTO_SAVE_REPORTS = True
REPORTS_DIRECTORY = "reports"

# إعدادات الطباعة
DEFAULT_PRINTER = None
PRINT_MARGINS = (20, 20, 20, 20)  # أعلى، يمين، أسفل، يسار
INVOICE_TEMPLATE = "default"

# إعدادات النسخ الاحتياطية
BACKUP_DIRECTORY = "backups"
AUTO_BACKUP_ENABLED = True
BACKUP_COMPRESSION = True
MAX_BACKUP_FILES = 30

# إعدادات الأداء
CACHE_SIZE = 1000
DATABASE_POOL_SIZE = 5
LAZY_LOADING = True
PAGINATION_SIZE = 100

# إعدادات التنبيهات
ENABLE_NOTIFICATIONS = True
NOTIFICATION_SOUND = True
EMAIL_NOTIFICATIONS = False
SMS_NOTIFICATIONS = False

# إعدادات التصدير
SUPPORTED_EXPORT_FORMATS = ["CSV", "Excel", "PDF", "JSON"]
DEFAULT_EXPORT_FORMAT = "Excel"
EXPORT_DIRECTORY = "exports"

# إعدادات الواجهة
THEME = "default"  # default, dark, light
LANGUAGE = "ar"    # ar, en
RTL_SUPPORT = True
ANIMATIONS_ENABLED = True

# إعدادات الذكاء الاصطناعي
AI_PREDICTIONS_ENABLED = True
PREDICTION_ACCURACY_THRESHOLD = 0.8
SEASONAL_ANALYSIS_ENABLED = True
ANOMALY_DETECTION_ENABLED = True

# مسارات الملفات
PATHS = {
    'data': os.path.join(os.getcwd(), "data"),
    'logs': os.path.join(os.getcwd(), "logs"),
    'temp': os.path.join(os.getcwd(), "temp"),
    'exports': os.path.join(os.getcwd(), "exports"),
    'reports': os.path.join(os.getcwd(), "reports"),
    'backups': os.path.join(os.getcwd(), "backups"),
    'templates': os.path.join(os.getcwd(), "templates")
}

# إنشاء المجلدات إذا لم تكن موجودة
for path in PATHS.values():
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

# إعدادات السجلات
LOGGING = {
    'enabled': True,
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'file': os.path.join(PATHS['logs'], f"app_{datetime.now().strftime('%Y%m%d')}.log"),
    'max_size': 10 * 1024 * 1024,  # 10 MB
    'backup_count': 5
}

# إعدادات البريد الإلكتروني (للتنبيهات)
EMAIL_SETTINGS = {
    'enabled': False,
    'smtp_server': '',
    'smtp_port': 587,
    'username': '',
    'password': '',
    'use_tls': True,
    'from_email': '',
    'admin_email': ''
}

# إعدادات قاعدة البيانات المتقدمة
DATABASE_SETTINGS = {
    'connection_timeout': 30,
    'busy_timeout': 30000,
    'journal_mode': 'WAL',
    'synchronous': 'NORMAL',
    'cache_size': -64000,  # 64MB
    'temp_store': 'MEMORY'
}

# إعدادات الأمان المتقدمة
SECURITY_SETTINGS = {
    'encryption_enabled': True,
    'audit_logging': True,
    'session_encryption': True,
    'ip_whitelist': [],
    'failed_login_monitoring': True,
    'password_history': 5,
    'password_expiry_days': 90
}

# إعدادات التكامل
INTEGRATION_SETTINGS = {
    'barcode_scanner': False,
    'receipt_printer': False,
    'cash_drawer': False,
    'scale_integration': False,
    'accounting_software': None
}

# إعدادات العملة
CURRENCY_SETTINGS = {
    'symbol': 'ريال',
    'code': 'SAR',
    'decimal_places': 2,
    'thousands_separator': ',',
    'decimal_separator': '.',
    'symbol_position': 'after'  # before, after
}

# إعدادات التاريخ والوقت
DATETIME_SETTINGS = {
    'format': '%Y-%m-%d %H:%M:%S',
    'date_format': '%Y-%m-%d',
    'time_format': '%H:%M:%S',
    'timezone': 'Asia/Riyadh',
    'first_day_of_week': 6  # السبت = 6
}

# إعدادات التحديث التلقائي
UPDATE_SETTINGS = {
    'check_for_updates': True,
    'auto_update': False,
    'update_channel': 'stable',  # stable, beta, alpha
    'update_server': ''
}

def get_setting(key, default=None):
    """الحصول على إعداد معين"""
    return globals().get(key, default)

def update_setting(key, value):
    """تحديث إعداد معين"""
    globals()[key] = value

def save_settings():
    """حفظ الإعدادات في ملف"""
    import json
    
    settings = {
        'app_info': {
            'name': APP_NAME,
            'version': APP_VERSION,
            'author': APP_AUTHOR
        },
        'database': DATABASE_SETTINGS,
        'security': SECURITY_SETTINGS,
        'ui': {
            'theme': THEME,
            'language': LANGUAGE,
            'fonts': FONTS,
            'colors': COLORS
        },
        'features': {
            'ai_enabled': AI_PREDICTIONS_ENABLED,
            'notifications': ENABLE_NOTIFICATIONS,
            'auto_backup': AUTO_BACKUP_ENABLED
        }
    }
    
    try:
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"خطأ في حفظ الإعدادات: {e}")
        return False

def load_settings():
    """تحميل الإعدادات من ملف"""
    import json
    
    try:
        if os.path.exists('settings.json'):
            with open('settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # تطبيق الإعدادات المحملة
            if 'ui' in settings:
                globals().update({
                    'THEME': settings['ui'].get('theme', THEME),
                    'LANGUAGE': settings['ui'].get('language', LANGUAGE),
                    'FONTS': settings['ui'].get('fonts', FONTS),
                    'COLORS': settings['ui'].get('colors', COLORS)
                })
            
            return True
    except Exception as e:
        print(f"خطأ في تحميل الإعدادات: {e}")
        return False

# تحميل الإعدادات عند استيراد الملف
load_settings()