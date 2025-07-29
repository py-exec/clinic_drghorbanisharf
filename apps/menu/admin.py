from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import MenuItem
from .utils import sync_menu_from_urls_grouped_by_app


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("title", "item_type", "is_active", "show_in_menu", "parent")
    list_filter = ("is_active", "show_in_menu", "item_type")
    search_fields = ("title", "link_target")

    # ✅ دکمه بالا، بدون نیاز به انتخاب آیتم
    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}

        # اضافه کردن دکمه به context
        extra_context["custom_button"] = format_html(
            '<a class="btn btn-success" style="margin: 10px 0;" href="sync-menu/">🔄 ساخت خودکار منو</a>'
        )
        return super().changelist_view(request, extra_context=extra_context)

    # ✅ URL سفارشی برای اجرای تابع
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("sync-menu/", self.admin_site.admin_view(self.sync_menu_from_urls), name="sync-menu"),
        ]
        return custom_urls + urls

    # ✅ اجرای تابع sync
    def sync_menu_from_urls(self, request):
        count_before = MenuItem.objects.count()
        sync_menu_from_urls_grouped_by_app()
        count_after = MenuItem.objects.count()
        added = count_after - count_before

        self.message_user(request, f"✅ {added} آیتم منو جدید اضافه شد.", level=messages.SUCCESS)
        return redirect("admin:apps.menu_menuitem_changelist")
