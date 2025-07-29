# apps/inventory/urls.py

from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    # ------------------ مدیریت کالاها (Items) ------------------
    # URL اصلی منو (استاتیک): '/inventory/items/' که به 'item_list' اشاره می‌کند.
    path('items/', views.ItemListView.as_view(), name='item_list'),
    path('items/create/', views.ItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/', views.ItemDetailView.as_view(), name='item_detail'),

    # ------------------ عملیات روی هر کالا (Item Operations) ------------------
    # این URLها معمولاً از صفحه جزئیات کالا فراخوانی می‌شوند.
    path('items/<int:pk>/maintenance/', views.ItemMaintenanceView.as_view(), name='item_maintenance'),
    path('items/<int:pk>/pm/', views.ItemPMView.as_view(), name='item_pm'),  # PM: Preventive Maintenance

    # ------------------ گزارش‌ها و لیست‌های کلی (Reports & Lists) ------------------
    # URL اصلی منو: 'inventory:inventory_list'
    path('reports/inventory/', views.InventoryListView.as_view(), name='inventory_list'),

    # سایر گزارش‌ها که در منو با لینک استاتیک مشخص شده‌اند.
    path('reports/stock-in/', views.StockInListView.as_view(), name='stockin_list'),
    path('reports/stock-out/', views.StockOutListView.as_view(), name='stockout_list'),
    path('reports/loans/', views.LoanListView.as_view(), name='loan_list'),
    path('reports/maintenance/', views.MaintenanceListView.as_view(), name='maintenance_list'),
    path('reports/pm/', views.PMListView.as_view(), name='pm_list'),
]
