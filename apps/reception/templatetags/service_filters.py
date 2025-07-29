# service_filters.py
from django import template

register = template.Library()

@register.filter
def get_service(services, service_type):
    """
    از بین queryset خدمات، اولین خدمتی که نوعش برابر با service_type باشد را برمی‌گرداند.
    """
    return services.filter(service_type=service_type).first()

@register.filter
def status_badge(service):
    status = service.status
    if status == "done":
        return '<span class="badge bg-success">انجام‌شده</span>'
    elif status == "cancelled":
        return '<span class="badge bg-danger">کنسل‌شده</span>'
    elif status == "paid":
        return '<span class="badge bg-info text-dark">پرداخت‌شده</span>'
    else:
        return '<span class="badge bg-warning text-dark">در انتظار</span>'