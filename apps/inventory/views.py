# 📦 Django Core
from django.views.generic import ListView, DetailView, CreateView, FormView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

# 🧾 مدل‌ها
from .models import (
    Item,
    StockIn,
    StockInItem,
    StockOut,
    StockOutItem,
    Loan,
    MaintenanceLog,
    ScheduledMaintenance
)

# 🧰 فرم‌ها
from .forms import (
    ItemForm,
    StockInForm, StockInItemFormSet,
    StockOutForm, StockOutItemFormSet,
    LoanForm,
    MaintenanceLogForm,
    ScheduledMaintenanceForm
)

# ⚙️ ابزارهای کمکی
import logging

# ⚠️ لاگر اصلی برای ثبت خطاها و عملیات حساس
logger = logging.getLogger(__name__)


# --------------------------------------------------
# لیست کالاها
# --------------------------------------------------
class ItemListView(LoginRequiredMixin, ListView):
    model = Item
    template_name = 'inventory/items/list.html'
    context_object_name = 'items'
    ordering = ['name']

    def get_queryset(self):
        try:
            qs = super().get_queryset()
            q = self.request.GET.get('q')
            if q:
                qs = qs.filter(name__icontains=q)
            return qs
        except Exception as e:
            logger.exception("خطا در دریافت لیست کالاها: %s", str(e))
            messages.error(self.request, "خطایی در دریافت لیست کالاها رخ داد.")
            return Item.objects.none()


# --------------------------------------------------
# فرم ثبت کالای جدید
# --------------------------------------------------
class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = 'inventory/items/create.html'

    def form_valid(self, form):
        try:
            form.instance.created_by = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, "کالا با موفقیت ثبت شد.")
            return response
        except Exception as e:
            logger.exception("خطا در ثبت کالا: %s", str(e))
            messages.error(self.request, "ثبت کالا با خطا مواجه شد.")
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.warning(self.request, "لطفاً اطلاعات وارد شده را بررسی کنید.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('inventory:item_detail', kwargs={'pk': self.object.pk})


# --------------------------------------------------
# نمایش جزئیات کالا
# --------------------------------------------------
class ItemDetailView(LoginRequiredMixin, DetailView):
    model = Item
    template_name = 'inventory/items/detail.html'
    context_object_name = 'item'

    def get_object(self, queryset=None):
        try:
            return get_object_or_404(Item, pk=self.kwargs.get('pk'))
        except Exception as e:
            logger.exception("کالا یافت نشد: %s", str(e))
            messages.error(self.request, "کالا یافت نشد یا مشکلی در بارگذاری پیش آمد.")
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = self.object
        try:
            context['stockins'] = item.stockinitem_set.select_related('stock_in')[:5]
            context['stockouts'] = item.stockoutitem_set.select_related('stock_out')[:5]
        except Exception as e:
            logger.warning("خطا در دریافت اطلاعات ورود/خروج کالا: %s", str(e))
            messages.warning(self.request, "عدم توانایی در بارگذاری ورود و خروج کالا.")
            context['stockins'] = []
            context['stockouts'] = []
        return context


# ===============================
# ثبت تعمیرات (MaintenanceLog)
# ===============================
class ItemMaintenanceView(LoginRequiredMixin, FormView):
    template_name = 'inventory/items/maintenance_form.html'
    form_class = MaintenanceLogForm

    def dispatch(self, request, *args, **kwargs):
        try:
            self.item = get_object_or_404(Item, pk=kwargs.get("pk"))
        except Exception as e:
            logger.warning(f"[تعمیر] کالا پیدا نشد - {e}")
            messages.error(request, "کالای انتخاب‌شده یافت نشد.")
            return redirect('inventory:item_list')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["item"] = self.item
        return context

    def form_valid(self, form):
        try:
            log = form.save(commit=False)
            log.item = self.item
            log.save()
            messages.success(self.request, "✅ ثبت تعمیر با موفقیت انجام شد.")
            return redirect('inventory:item_detail', pk=self.item.pk)
        except Exception as e:
            logger.error(f"[ثبت تعمیر] خطا: {e}")
            messages.error(self.request, "⛔ ثبت تعمیر با خطا مواجه شد.")
            return self.form_invalid(form)


# ===============================
# ثبت نگهداری دوره‌ای (ScheduledMaintenance)
# ===============================
class ItemPMView(LoginRequiredMixin, FormView):
    template_name = 'inventory/items/pm_form.html'
    form_class = ScheduledMaintenanceForm

    def dispatch(self, request, *args, **kwargs):
        try:
            self.item = get_object_or_404(Item, pk=kwargs.get("pk"))
        except Exception as e:
            logger.warning(f"[PM] کالا یافت نشد - {e}")
            messages.warning(request, "کالای انتخاب‌شده یافت نشد.")
            return redirect('inventory:item_list')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["item"] = self.item
        return context

    def form_valid(self, form):
        try:
            pm = form.save(commit=False)
            pm.item = self.item
            pm.save()
            messages.success(self.request, "✅ برنامه PM با موفقیت ثبت شد.")
            return redirect('inventory:item_detail', pk=self.item.pk)
        except Exception as e:
            logger.exception(f"[PM ثبت] خطا در ذخیره: {e}")
            messages.error(self.request, "⛔ خطا در ثبت برنامه نگهداری.")
            return self.form_invalid(form)


# ===============================
# لیست تعمیرات تجهیزات
# ===============================
class MaintenanceListView(LoginRequiredMixin, ListView):
    model = MaintenanceLog
    template_name = 'inventory/lists/maintenance_list.html'
    context_object_name = 'maintenances'
    ordering = ['-date_reported']

    def get_queryset(self):
        qs = super().get_queryset().select_related('item', 'company')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(item__name__icontains=q)
        return qs


# ===============================
# لیست برنامه‌های نگهداری دوره‌ای (PM)
# ===============================
class PMListView(LoginRequiredMixin, ListView):
    model = ScheduledMaintenance
    template_name = 'inventory/lists/pm_list.html'
    context_object_name = 'pms'
    ordering = ['-next_due_date']

    def get_queryset(self):
        qs = super().get_queryset().select_related('item')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(item__name__icontains=q)
        return qs


# ===============================
# لیست موجودی انبار
# ===============================
class InventoryListView(LoginRequiredMixin, ListView):
    model = StockInItem
    template_name = 'inventory/lists/inventory_list.html'
    context_object_name = 'inventory_items'
    ordering = ['-stock_in__date']

    def get_queryset(self):
        qs = super().get_queryset().select_related('item', 'stock_in')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(item__name__icontains=q)
        return qs


# --------------------------------------------------
# 📦 لیست اسناد ورود کالا به انبار
# --------------------------------------------------
class StockInListView(LoginRequiredMixin, ListView):
    model = StockIn
    template_name = 'inventory/lists/stockin_list.html'
    context_object_name = 'stockins'
    ordering = ['-date']

    def get_queryset(self):
        try:
            qs = super().get_queryset().prefetch_related('items__item', 'supplier')
            q = self.request.GET.get('q')
            if q:
                qs = qs.filter(items__item__name__icontains=q).distinct()
            return qs
        except Exception as e:
            logger.error(f"[StockInListView] خطا در فیلتر: {e}")
            messages.error(self.request, "⛔ خطا در دریافت لیست ورود کالاها")
            return StockIn.objects.none()


# --------------------------------------------------
# 📤 لیست اسناد خروج کالا از انبار
# --------------------------------------------------
class StockOutListView(LoginRequiredMixin, ListView):
    model = StockOut
    template_name = 'inventory/lists/stockout_list.html'
    context_object_name = 'stockouts'
    ordering = ['-date']

    def get_queryset(self):
        try:
            qs = super().get_queryset().prefetch_related('items__item')
            q = self.request.GET.get('q')
            if q:
                qs = qs.filter(items__item__name__icontains=q).distinct()
            return qs
        except Exception as e:
            logger.warning(f"[StockOutListView] خطا در فیلتر: {e}")
            messages.error(self.request, "⛔ خطا در دریافت لیست خروج کالاها")
            return StockOut.objects.none()


# --------------------------------------------------
# 🧳 لیست امانت تجهیزات
# --------------------------------------------------
class LoanListView(LoginRequiredMixin, ListView):
    model = Loan
    template_name = 'inventory/lists/loan_list.html'
    context_object_name = 'loans'
    ordering = ['-loan_date']

    def get_queryset(self):
        try:
            qs = super().get_queryset().select_related('item')
            q = self.request.GET.get('q')
            if q:
                qs = qs.filter(patient__icontains=q)
            return qs
        except Exception as e:
            logger.exception(f"[LoanListView] خطا در واکشی لیست امانت‌ها: {e}")
            messages.error(self.request, "⛔ دریافت لیست امانت‌ها با مشکل مواجه شد.")
            return Loan.objects.none()