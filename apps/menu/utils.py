# apps/menu/utils.py

import importlib
from apps.menu.models import MenuItem
from collections import defaultdict
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.urls import get_resolver, URLResolver, resolve

# ایمپورت MenuItem را در اینجا انجام می‌دهیم.
from .models import MenuItem


@transaction.atomic
def sync_menu_from_urls_grouped_by_app():
    """
    این تابع تمام URLهای دارای name را استخراج کرده و بر اساس ماژول ویو آن‌ها
    منوی والد و فرزند می‌سازد. والد بر اساس اپ است و فرزندان بر اساس هر URL.
    """
    resolver = get_resolver()

    # ساختار: {"apps.patient": [("dashboard", "apps.patient.views.dashboard"), ...]}
    app_to_urls = {}

    def collect_named_urls(urlpatterns, namespace=None, parent_ns=None):
        for entry in urlpatterns:
            if isinstance(entry, URLResolver):
                ns = f"{parent_ns}:{entry.namespace}" if parent_ns and entry.namespace else (
                        entry.namespace or parent_ns)
                collect_named_urls(entry.url_patterns, namespace=entry.namespace, parent_ns=ns)
            else:
                if not entry.name:
                    continue  # فقط URLهایی که name دارند را می‌خواهیم
                full_name = f"{parent_ns}:{entry.name}" if parent_ns else entry.name
                callback = entry.callback
                view_module = callback.__module__
                app_label = view_module.split(".views")[0] if ".views" in view_module else view_module.split(".")[0]

                app_to_urls.setdefault(app_label, []).append((full_name, callback))

    collect_named_urls(resolver.url_patterns)

    for app_label, url_items in app_to_urls.items():
        app_name_display = app_label.replace("apps.", "").replace("_", " ").title()

        parent_item, _ = MenuItem.objects.get_or_create(
            title=app_name_display,
            defaults={
                "is_active": True,
                "show_in_menu": True,
                "item_type": MenuItem.ItemType.HEADER,
                "order": 0,
                "auto_generated": True,
            },
        )

        for url_name, view_func in url_items:
            # آیا آیتم قبلاً ساخته شده؟
            if MenuItem.objects.filter(link_type=MenuItem.LinkType.REVERSE, link_target=url_name).exists():
                continue

            action_title = url_name.split(":")[-1].replace("_", " ").title()

            MenuItem.objects.create(
                title=action_title,
                parent=parent_item,
                item_type=MenuItem.ItemType.LINK,
                link_type=MenuItem.LinkType.REVERSE,
                link_target=url_name,
                is_active=True,
                show_in_menu=True,
                auto_generated=True,
            )


def get_menu_version():
    """
    نسخه فعلی منو را از کش دریافت می‌کند.
    اگر کلید "menu_version" در کش وجود نداشته باشد، مقدار پیش‌فرض 1 برگردانده می‌شود.
    """
    return cache.get("menu_version", 1)


def bump_menu_version():
    """
    نسخه منو را یک واحد افزایش می‌دهد.
    این تابع باید هر زمان که ساختار منو (مثلاً یک MenuItem) در دیتابیس تغییر می‌کند، فراخوانی شود.
    با افزایش نسخه، کلیدهای کش منو (که شامل این نسخه هستند) نامعتبر شده و منوها مجبور به بازسازی می‌شوند.
    این کار باعث می‌شود تغییرات منو فوراً در UI منعکس شوند.
    """
    current_version = get_menu_version()
    new_version = current_version + 1
    cache.set("menu_version", new_version)


# اتصال به سیگنال‌های ذخیره/حذف MenuItem.
@receiver(post_save, sender=MenuItem)
@receiver(post_delete, sender=MenuItem)
def menu_item_changed_handler(sender, **kwargs):
    """
    Signal handler برای فراخوانی `bump_menu_version()` پس از هر تغییر در مدل `MenuItem`.
    این باعث می‌شود کش منوها پس از ویرایش/حذف آیتم‌ها، به‌روز شود.
    """
    bump_menu_version()


def build_menu_tree(all_items, user, request=None):
    """
    تابع کمکی برای تولید ساختار درختی منو به صورت بازگشتی.
    این تابع بهینه‌سازی شده تا از defaultdict برای جستجوی سریعتر فرزندان استفاده کند.
    """

    items_by_parent_id = defaultdict(list)
    root_items = []  # آیتم‌های ریشه (بدون والد)

    for item in all_items:
        if item.parent_id is None:
            root_items.append(item)
        else:
            items_by_parent_id[item.parent_id].append(item)

    root_items.sort(key=lambda x: x.order)  # مرتب‌سازی آیتم‌های ریشه

    def _get_children(parent_id):
        """
        دریافت لیست فرزندان یک آیتم والد خاص و مرتب‌سازی آن‌ها.
        """
        children_list = items_by_parent_id.get(parent_id, [])
        children_list.sort(key=lambda x: x.order)
        return children_list

    def _build_recursive(current_level_items_to_process, parent_item_for_debug=None):
        """
        تابع بازگشتی برای ساخت درخت منو.
        `current_level_items_to_process`: لیستی از آیتم‌های MenuItem برای پردازش در این سطح.
        `parent_item_for_debug`: آیتم والد برای اهداف دیباگینگ (None برای ریشه).
        """
        tree_nodes = []

        for item in current_level_items_to_process:
            if item.has_access(user):
                node = {
                    "title": item.title,
                    "url": item.resolve_url(),
                    "icon": item.icon,
                    "badge": item.badge,
                    "css_class": item.css_class,
                    "type": item.item_type,
                    "is_active": item.is_active,
                    "show_in_menu": item.show_in_menu,
                    "id": item.id,
                    "children": []
                }

                # منطق هایلایت هوشمند آیتم منوی فعال.
                node['active'] = False
                if request and item.item_type == MenuItem.ItemType.LINK:
                    current_path = request.path

                    current_url_name = None
                    try:
                        resolved_url = resolve(current_path)
                        current_url_name = resolved_url.url_name
                        if resolved_url.app_name:
                            current_url_name = f"{resolved_url.app_name}:{current_url_name}"
                    except Exception:
                        pass

                    if current_url_name and item.link_type == MenuItem.LinkType.REVERSE and item.link_target == current_url_name:
                        node['active'] = True
                    elif current_url_name and item.highlight_url_names and current_url_name in item.highlight_url_names:
                        node['active'] = True
                    elif item.link_type == MenuItem.LinkType.STATIC and item.link_target and current_path.startswith(
                            item.link_target):
                        node['active'] = True
                    elif item.link_type == MenuItem.LinkType.EXTERNAL and item.link_target and current_path == item.link_target:
                        node['active'] = True

                # ساخت فرزندان آیتم به صورت بازگشتی.
                accessible_children_nodes = _build_recursive(_get_children(item.id), item)
                node["children"] = accessible_children_nodes

                # اگر یکی از فرزندان فعال بود، والد را نیز فعال (active) می‌کنیم.
                if any(child.get('active') for child in accessible_children_nodes):
                    node['active'] = True

                # یک هدر یا جداکننده تنها در صورتی به درخت اضافه می‌شود که حداقل یک فرزند قابل دسترسی داشته باشد.
                if (item.item_type in [MenuItem.ItemType.HEADER,
                                       MenuItem.ItemType.DIVIDER] and accessible_children_nodes) or \
                        (item.item_type not in [MenuItem.ItemType.HEADER, MenuItem.ItemType.DIVIDER]):
                    tree_nodes.append(node)

        return tree_nodes

    final_menu_tree = _build_recursive(root_items, None)
    return final_menu_tree
