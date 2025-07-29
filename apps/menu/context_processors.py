# apps/menu/context_processors.py

from apps.accounts.models import User
from django.conf import settings
from django.core.cache import cache

from .models import MenuItem  # MenuItem همچنان برای MenuItem.ItemType نیاز است.
# 📌 ایمپورت تابع build_menu_tree و get_menu_version از utils
from .utils import build_menu_tree, get_menu_version


def dynamic_menu(request):
    """
    Context processor برای ارائه منوی داینامیک به تمام تمپلیت‌ها.
    منو بر اساس دسترسی کاربر (نقش‌ها و مجوزها) فیلتر شده و کش می‌شود.
    این تابع، لیستی از آیتم‌های منو را در قالب درختی آماده می‌کند
    که برای رندر در ناوبری وب‌سایت استفاده می‌شود.
    """
    user = request.user

    menu_cache_timeout = getattr(settings, "MENU_CACHE_TIMEOUT", 3600)

    # دریافت نسخه فعلی منو برای استفاده در کلید کش.
    menu_version = get_menu_version()

    if not user.is_authenticated:
        cache_key = f"dynamic_menu_guest_v{menu_version}"
    else:
        cache_key = f"dynamic_menu_user_{user.id}_v{menu_version}"

    menu_tree = cache.get(cache_key)

    if menu_tree:
        return {"dynamic_menu": menu_tree}

    all_items = list(
        MenuItem.objects.select_related("parent")
        .prefetch_related("permissions", "required_roles")
        .filter(is_active=True, show_in_menu=True)
        .order_by('order')
    )

    # استفاده از تابع build_menu_tree از utils
    menu_tree = build_menu_tree(all_items, user, request)  # 👈 ارسال request

    cache.set(cache_key, menu_tree, menu_cache_timeout)

    return {"dynamic_menu": menu_tree}

# 📌 تابع _build_menu_tree از اینجا حذف شده و به apps/menu/utils.py منتقل شده است.
