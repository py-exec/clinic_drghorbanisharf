import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# مسیر اصلی پروژه
BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_ROOT = os.getenv("BACKUP_ROOT", str(BASE_DIR / "backups"))
BACKUP_LOG_FILE = os.getenv("BACKUP_LOG_FILE", str(Path(BACKUP_ROOT) / "backup.log"))
ENV_PATH = "env/.env"
load_dotenv(ENV_PATH)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / "templates",  # 📍 مسیر قالب‌های مشترک
        ],
        'APP_DIRS': True,  # تا تمپلیت‌های داخل اپ‌ها هم خونده بشه
        'OPTIONS': {
            'context_processors': [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",

                # اگر چیزهای دیگه‌ای داری مثل custom context processor:
                # "apps.menu.context_processors.dynamic_menu",
            ],
        },
    },
]

STATIC_URL = "/static/"

STATICFILES_DIRS = [ "static",  # 📍 استاتیک‌های مشترک
]

STATIC_ROOT = BASE_DIR / "staticfiles"  # محل خروجی collectstatic

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# ✅ DEBUG = False در حالت پروداکشن
DEBUG = os.getenv("DEBUG", "False") == "True"

# تنظیم ALLOWED_HOSTS برای اجرا روی سرور
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost").split(",")

# تنظیم CORS برای اجازه دادن به درخواست‌ها از فرانت‌اند
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost").split(",")
# اپلیکیشن‌ها
INSTALLED_APPS = [
    # 📦 اپ‌های پیش‌فرض Django و ابزارهای مدیریت
    'jazzmin',  # 🎨 قالب زیبای پنل مدیریت جنگو برای بهبود تجربه کاربری ادمین.
    'django.contrib.admin',  # پنل مدیریت پیش‌فرض Django برای مدیریت داده‌ها.
    'django.contrib.auth',  # سیستم احراز هویت کاربران، شامل مدل‌های User و Group.
    'django.contrib.contenttypes',  # پشتیبانی از ContentType framework برای ارتباطات جنریک.
    'django.contrib.sessions',  # مدیریت نشست‌های کاربران (Session) برای پیگیری لاگین و وضعیت کاربر.
    'django.contrib.messages',  # ارسال پیام‌های موقت (مانند flash messages) به کاربران.
    'django.contrib.staticfiles',  # مدیریت فایل‌های استاتیک (CSS, JS, تصاویر) پروژه.
    'django.contrib.humanize',  # قالب‌بندی اعداد و تاریخ (مثلاً: ۱,۰۰۰,۰۰۰ تومان، ۲ روز پیش).

    # ⚙️ ابزارهای کمکی و کتابخانه‌های شخص ثالث برای قابلیت‌های پیشرفته
    'whitenoise.runserver_nostatic',  # برای مدیریت بهینه فایل‌های استاتیک در محیط پروداکشن.
    'django_celery_beat',  # مدیریت و زمان‌بندی تسک‌های پس‌زمینه (Background Tasks) با Celery.
    'django_celery_results',  # ذخیره نتایج و وضعیت تسک‌های Celery در دیتابیس.
    'rest_framework',  # Django REST Framework برای ساخت APIهای RESTful.
    'corsheaders',  # برای فعال‌سازی Cross-Origin Resource Sharing (CORS) و اجازه به فرانت‌اند‌های جداگانه برای ارتباط.
    'channels',  # فریم‌ورک جنگو برای پشتیبانی از WebSocket و پروتکل‌های ناهمزمان (Real-time features).
    'simple_history',  # برای ردیابی و ذخیره تاریخچه تغییرات در مدل‌های دیتابیس (Audit Log).
    'django_cleanup.apps.CleanupConfig',  # برای حذف خودکار فایل‌های مرتبط با مدل پس از حذف مدل (مثلاً تصاویر).

    # 🏥 اپ‌های اختصاصی پروژه ما (ترتیب لود شدن در اینجا بسیار مهم است!)
    # اپ‌های پایه‌ای که سایر اپ‌ها به آن‌ها وابسته هستند، باید زودتر لود شوند.

    'apps.menu',  # **مدیریت منو برای کاربران ** (ACL).
    'apps.accounts',  # **مدیریت کاربران و احراز هویت سفارشی** (شامل مدل User و ACL).
    'apps.patient',  # **مدیریت کامل اطلاعات بیماران** (سوابق پزشکی، پرونده، اطلاعات تماس).
    'apps.doctors',  # **مدیریت اطلاعات پزشکان، تخصص‌ها، برنامه‌های کاری (شیفت‌ها) و بلاک‌های زمانی** (مرخصی‌ها، جلسات).

    # 📌 مهمترین ترتیب: 'appointments' باید قبل از 'reception' و 'accounting' باشد
    # زیرا این اپ‌ها به مدل Appointment وابسته هستند.
    'apps.appointments',
    # **مدیریت مرکزی تمامی جنبه‌های نوبت‌دهی** (رزرو، وضعیت‌ها، تداخل‌ها، کدهای رهگیری).

    'apps.reception',  # **مدیریت پذیرش بیماران، شعب، منابع کلینیک و انواع خدمات پزشکی و تعرفه‌ها**.
    'apps.accounting',  # **مدیریت جامع حسابداری، فاکتورها، تراکنش‌ها، دفتر کل و ارتباطات مالی**.
    # --- پایان بخش ترتیب حیاتی ---

    'apps.staffs',  # مدیریت اطلاعات و وظایف کارمندان و پرسنل غیرپزشکی.
    # 'apps.shifts', # (کامنت شده) اگر برای مدیریت شیفت‌های عمومی یا شیفت‌های پرسنل غیرپزشکی استفاده شود.
    'apps.ecg',  # مدیریت اطلاعات و رکوردهای مربوط به نوار قلب (ECG).
    'apps.echo_tee',  # مدیریت اطلاعات مربوط به اکوکاردیوگرافی از طریق مری (TEE).
    'apps.echo_tte',  # مدیریت اطلاعات مربوط به اکوکاردیوگرافی از طریق قفسه سینه (TTE).
    'apps.echo_fellowship',  # مدیریت اطلاعات مربوط به بخش fellowship اکوکاردیوگرافی.
    'apps.holter',  # مدیریت نصب و ثبت اطلاعات دستگاه‌های هولتر (فشار خون/ریتم قلب).
    'apps.procedures',  # ثبت اطلاعات مربوط به جراحی‌ها یا مداخلات پزشکی.
    'apps.inventory',  # مدیریت انبارداری، موجودی کالا و تجهیزات پزشکی.
    'apps.prescriptions',  # مدیریت نسخه‌های دارویی و داروهای تجویزی.
    'apps.clinic_messenger',  # سیستم پیام‌رسانی داخلی کلینیک و مدیریت ارسال SMS/Email.
    'apps.holter_bp',  # (اگر اپ جداگانه برای هولتر فشار خون است)
    'apps.holter_hr',  # (اگر اپ جداگانه برای هولتر ضربان قلب است)
    'apps.exercise_stress_test',  # (اگر اپ جداگانه برای تست ورزش است)
    'apps.preparation',  # (اگر اپ جداگانه برای آماده‌سازی بیمار است)
    'apps.tilt',  # (اگر اپ جداگانه برای تست Tilt Table است)
'apps.backup', # ابزار پشتیبان‌گیری از پایگاه داده
]

# WebSocket Channels with Redis
ASGI_APPLICATION = 'clinic_drghorbanisharif.asgi.application'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("localhost", 6379)],  # یا ("localhost", 6379) در لوکال
        },
    },
}

# میان‌افزارها
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # مدیریت استاتیک‌ها
    'corsheaders.middleware.CorsMiddleware',  # فعال‌سازی CORS
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.UsernameOrPhoneBackend",
]

LOGIN_URL = '/accounts/login/'  # مسیر صفحه لاگین

# فعال‌سازی CORS برای ارتباط با کلاینت‌های خارجی
CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'clinic_drghorbanisharif.urls'
WSGI_APPLICATION = 'clinic_drghorbanisharif.wsgi.application'

# # تنظیمات قالب‌ها
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / "db.sqlite3",  # مسیر فایل SQLite در پروژه
#     }
# }

# تنظیمات پایگاه داده (PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv("POSTGRES_DB", "clinic_db"),
        'USER': os.getenv("POSTGRES_USER", "py_exec"),
        'PASSWORD': os.getenv("POSTGRES_PASSWORD", "secure-password"),
        'HOST': os.getenv("POSTGRES_HOST", "localhost"),
        'PORT': os.getenv("POSTGRES_PORT", "5432"),
    }
}

# کشینگ و سشن‌ها
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://localhost:6379/1"),
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# اعتبارسنجی رمز عبور
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# تنظیمات زبان و منطقه زمانی
LANGUAGE_CODE = 'en'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

# تنظیمات ایمیل
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.example.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "your-email@example.com")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "your-email-password")

# کلید پیش‌فرض مدل‌ها
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# امنیت و تنظیمات اصلی
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "fallback-secret-key")

LOGIN_REDIRECT_URL = "/"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
        "backup_file": {"class": "logging.FileHandler", "filename": BACKUP_LOG_FILE, "level": "INFO"},
    },
    "loggers": {
        "backup": {"handlers": ["backup_file", "console"], "level": "INFO", "propagate": False},
    },
}

AUTH_USER_MODEL = "accounts.User"

# ===============================
# CELERY CONFIG
# ===============================
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Tehran"
CELERY_BEAT_SCHEDULE = {"daily_backup": {"task": "apps.backup.tasks.scheduled_backup", "schedule": 86400}}

# اطلاعات پیش‌فرض سوپر یوزر
DEFAULT_SUPERUSER_PHONE = os.getenv("DEFAULT_SUPERUSER_PHONE", "09100000000")
DEFAULT_SUPERUSER_PASSWORD = os.getenv("DEFAULT_SUPERUSER_PASSWORD", "admin1234")
DEFAULT_SUPERUSER_FIRST_NAME = os.getenv("DEFAULT_SUPERUSER_FIRST_NAME", "ادمین")
DEFAULT_SUPERUSER_LAST_NAME = os.getenv("DEFAULT_SUPERUSER_LAST_NAME", "سیستم")
DEFAULT_SUPERUSER_NATIONAL_CODE = os.getenv("DEFAULT_SUPERUSER_NATIONAL_CODE", "0000000000")

# IPPanel Settings
IPPANEL_API_KEY = os.getenv("IPPANEL_API_KEY", "")
IPPANEL_ORIGINATOR = os.getenv("IPPANEL_ORIGINATOR", "+98xxxxxxxxxx")
IPPANEL_URL = os.getenv("IPPANEL_URL", "https://rest.ippanel.com/v1/messages")  # فقط در صورت نیاز
IPPANEL_TIMEOUT = int(os.getenv("IPPANEL_TIMEOUT", "10"))
