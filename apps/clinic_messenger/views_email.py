# # apps/clinic_messenger/views_email.py
#
# from django.contrib import messages
# from django.contrib.auth.decorators import login_required, permission_required
# from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
# from django.core.mail import send_mail
# from django.shortcuts import render, redirect
# from django.urls import reverse_lazy
# from django.views.generic import ListView, CreateView, UpdateView, DeleteView
#
# from .forms import EmailMessageForm, EmailConfigForm
# from .models import EmailMessage, EmailConfig
#
#
# # --- ارسال و وضعیت ایمیل ---
#
# @login_required
# @permission_required("clinic_messenger.add_emailmessage", raise_exception=True)
# def email_send_view(request):
#     """
#     ارسال ایمیل به صورت دستی.
#     """
#     if request.method == "POST":
#         form = EmailMessageForm(request.POST)
#         if form.is_valid():
#             email = form.save(commit=False)
#             email.requested_by = request.user
#
#             config = EmailConfig.objects.filter(is_active=True).first()
#             if not config:
#                 messages.error(request, "هیچ تنظیمات ایمیل فعالی یافت نشد.")
#                 return redirect("clinic_messenger:email_send")
#
#             email.config = config
#             try:
#                 # ❗️ نکته: برای ارسال واقعی، باید تنظیمات SMTP در settings.py
#                 # به صورت داینامیک از آبجکت config خوانده شود.
#                 # این بخش نیاز به یک سرویس ایمیل سفارشی دارد.
#                 send_mail(
#                     email.subject,
#                     email.body,
#                     config.from_email,
#                     [email.to_email],
#                     fail_silently=False,
#                 )
#                 email.status = "sent"
#                 messages.success(request, "ایمیل با موفقیت ارسال شد.")
#             except Exception as e:
#                 email.status = "failed"
#                 email.response_message = str(e)
#                 messages.error(request, f"ارسال ایمیل ناموفق بود: {e}")
#
#             email.save()
#             return redirect("clinic_messenger:email_send")
#     else:
#         form = EmailMessageForm()
#
#     return render(request, "clinic_messenger/email_send.html", {"form": form})
#
#
# @login_required
# @permission_required("clinic_messenger.view_emailconfig", raise_exception=True)
# def email_status_view(request):
#     """
#     نمایش وضعیت کلی سرویس ایمیل بر اساس اولین تنظیمات فعال.
#     """
#     config = EmailConfig.objects.filter(is_active=True).first()
#     context = {"config": config}
#     return render(request, "clinic_messenger/email_status.html", context)
#
#
# # --- مدیریت تنظیمات ایمیل (EmailConfig CRUD) ---
#
# class EmailConfigListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
#     model = EmailConfig
#     template_name = "clinic_messenger/email_config_list.html"
#     context_object_name = "configs"
#     permission_required = "clinic_messenger.view_emailconfig"
#
#
# class EmailConfigCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
#     model = EmailConfig
#     form_class = EmailConfigForm
#     template_name = "clinic_messenger/email_config_form.html"
#     permission_required = "clinic_messenger.add_emailconfig"
#     success_url = reverse_lazy("clinic_messenger:email_config_list")
#
#     def form_valid(self, form):
#         messages.success(self.request, "تنظیمات ایمیل جدید با موفقیت ایجاد شد.")
#         return super().form_valid(form)
#
#
# class EmailConfigUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
#     model = EmailConfig
#     form_class = EmailConfigForm
#     template_name = "clinic_messenger/email_config_form.html"
#     permission_required = "clinic_messenger.change_emailconfig"
#     success_url = reverse_lazy("clinic_messenger:email_config_list")
#
#     def form_valid(self, form):
#         messages.success(self.request, "تنظیمات ایمیل با موفقیت ویرایش شد.")
#         return super().form_valid(form)
#
#
# class EmailConfigDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
#     model = EmailConfig
#     template_name = "clinic_messenger/confirm_delete.html"
#     permission_required = "clinic_messenger.delete_emailconfig"
#     success_url = reverse_lazy("clinic_messenger:email_config_list")
#
#     def form_valid(self, form):
#         messages.warning(self.request, f"تنظیمات ایمیل '{self.object}' حذف شد.")
#         return super().form_valid(form)
