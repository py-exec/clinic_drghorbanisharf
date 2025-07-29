# apps/accounts/views.py

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .forms import UserCreateForm, UserUpdateForm
from .models import User, Role


# ----------------------------
# داشبورد اصلی سیستم
# ----------------------------
@login_required
def dashboard_view(request):
    """
    داشبورد اصلی سیستم که پس از ورود به کاربر نمایش داده می‌شود.
    در آینده می‌توان بر اساس نقش کاربر (request.user.role) کانتکست‌های
    متفاوتی را به این صفحه ارسال کرد.
    """
    # TODO: این بخش در آینده با داده‌های واقعی از مدل‌های دیگر پر می‌شود
    context = {
        'stats': {
            'patients_count': User.objects.filter(role__code='patient').count(),
            'doctors_count': User.objects.filter(role__code='doctor').count(),
        }
    }
    return render(request, "main_dashboard.html", context)


# ----------------------------
# ورود به سیستم
# ----------------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # بک‌اند سفارشی ما هم با نام کاربری و هم با شماره تلفن کار می‌کند
        user = authenticate(request, username=username, password=password)

        if user:
            if not user.is_active:
                messages.error(request, "حساب کاربری شما غیرفعال است.")
            elif not user.is_verified:
                messages.warning(request, "حساب کاربری شما هنوز توسط ادمین تایید نشده است.")
            else:
                login(request, user)
                user.update_last_seen(request)
                messages.success(request, f"خوش آمدید، {user.get_full_name()}")

                next_url = request.GET.get('next')
                return redirect(next_url or 'dashboard')
        else:
            messages.error(request, "نام کاربری یا رمز عبور اشتباه است.")

    return render(request, "accounts/login.html")


# ----------------------------
# خروج از سیستم
# ----------------------------
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "با موفقیت خارج شدید.")
    return redirect("accounts:login")


# ----------------------------
# ثبت‌نام اولیه کاربران
# ----------------------------
def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = UserCreateForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.is_verified = False
            user.save()

            try:
                # 👈 اصلاح: استفاده از مدل صحیح Role
                default_role = Role.objects.get(code="patient")
                user.role = default_role
                user.save()
            except Role.DoesNotExist:
                pass

            messages.success(request, "حساب شما با موفقیت ساخته شد. پس از تایید توسط مدیر، فعال خواهد شد.")
            return redirect("accounts:login")
    else:
        form = UserCreateForm()

    return render(request, "accounts/user_register.html", {"form": form})


# ----------------------------
# پروفایل کاربر وارد شده
# ----------------------------
@login_required
def profile_view(request):
    return render(request, "accounts/profile.html", {"user": request.user})


# ----------------------------
# مدیریت کاربران (CRUD)
# ----------------------------

class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    permission_required = "accounts.view_user"
    paginate_by = 10

    def get_queryset(self):
        return User.objects.filter(is_active=True).select_related("role").order_by('-date_joined')


class UserDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = User
    template_name = "accounts/user_detail.html"
    context_object_name = "user_obj"
    permission_required = "accounts.view_user"


class UserCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = "accounts/user_form.html"
    permission_required = "accounts.add_user"
    success_url = reverse_lazy("accounts:user-list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "کاربر جدید با موفقیت ساخته شد.")
        return super().form_valid(form)


class UserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "accounts/user_form.html"
    permission_required = "accounts.change_user"

    def get_success_url(self):
        # 👈 اصلاح: هدایت به صفحه جزئیات همان کاربر
        return self.object.get_absolute_url()

    def form_valid(self, form):
        messages.success(self.request, "اطلاعات کاربر با موفقیت ویرایش شد.")
        return super().form_valid(form)


class UserSoftDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = User
    template_name = "accounts/user_confirm_delete.html"
    success_url = reverse_lazy("accounts:user-list")
    permission_required = "accounts.delete_user"

    def form_valid(self, form):
        # 👈 اصلاح: استفاده از متد soft_delete مدل
        self.object.soft_delete()
        messages.warning(self.request, f"کاربر {self.object.get_full_name()} غیرفعال شد.")
        return redirect(self.success_url)
