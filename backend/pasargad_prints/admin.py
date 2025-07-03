from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from products.models import Product, Category, Order
from django.db.models import Count, Sum, Q
from datetime import datetime, timedelta

# Customize admin site header and title
admin.site.site_header = "Pasargad Prints Admin"
admin.site.site_title = "Pasargad Prints"
admin.site.index_title = "Store Management"


class DashboardView(TemplateView):
    template_name = 'admin/dashboard.html'
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Product statistics
        context['total_products'] = Product.objects.count()
        context['active_products'] = Product.objects.filter(is_active=True).count()
        context['out_of_stock'] = Product.objects.filter(stock_quantity=0).count()
        context['low_stock'] = Product.objects.filter(stock_quantity__gt=0, stock_quantity__lt=10).count()
        
        # Recent orders (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        try:
            recent_orders = Order.objects.filter(created_at__gte=week_ago)
            context['recent_orders_count'] = recent_orders.count()
            context['recent_revenue'] = recent_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        except:
            context['recent_orders_count'] = 0
            context['recent_revenue'] = 0
        
        # Low stock products
        context['low_stock_products'] = Product.objects.filter(
            stock_quantity__gt=0, 
            stock_quantity__lt=10,
            is_active=True
        ).order_by('stock_quantity')[:5]
        
        # Out of stock products
        context['out_of_stock_products'] = Product.objects.filter(
            stock_quantity=0,
            is_active=True
        ).order_by('-created_at')[:5]
        
        return context