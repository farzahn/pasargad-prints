import django_filters
from django.db.models import Q
from .models import Order


class OrderFilter(django_filters.FilterSet):
    """Advanced filtering for orders."""
    
    # Date range filters
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Created after'
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Created before'
    )
    
    # Price range filters
    min_total = django_filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='gte',
        label='Minimum total'
    )
    max_total = django_filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='lte',
        label='Maximum total'
    )
    
    # Status filters with multiple choice
    status = django_filters.MultipleChoiceFilter(
        choices=Order.ORDER_STATUS_CHOICES,
        label='Order status'
    )
    
    # Search filter
    search = django_filters.CharFilter(method='search_filter', label='Search')
    
    class Meta:
        model = Order
        fields = {
            'status': ['exact'],
            'fulfillment_method': ['exact'],
            'tracking_number': ['exact', 'icontains'],
        }
    
    def search_filter(self, queryset, name, value):
        """Custom search across multiple fields."""
        return queryset.filter(
            Q(order_number__icontains=value) |
            Q(shipping_name__icontains=value) |
            Q(shipping_email__icontains=value) |
            Q(billing_email__icontains=value)
        )