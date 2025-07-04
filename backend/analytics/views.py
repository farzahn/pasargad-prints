from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q, F
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import random
import hashlib
from decimal import Decimal

from .models import (
    PageView, UserBehavior, ProductView, CartAbandonment,
    Conversion, ABTestExperiment, ABTestParticipant, Report
)
from .serializers import (
    PageViewSerializer, UserBehaviorSerializer, ProductViewSerializer,
    CartAbandonmentSerializer, ConversionSerializer, ABTestExperimentSerializer,
    ABTestParticipantSerializer, ReportSerializer, AdminPageViewSerializer,
    AdminUserBehaviorSerializer, AdminProductViewSerializer,
    AdminCartAbandonmentSerializer, AdminConversionSerializer,
    DashboardMetricsSerializer, ProductPerformanceSerializer,
    CustomerAnalyticsSerializer
)
from products.models import Product
from orders.models import Order, OrderItem
from cart.models import Cart, CartItem
from .utils import parse_user_agent, get_client_ip, generate_report_pdf

User = get_user_model()


# Analytics Data Collection Views
class PageViewCreateView(generics.CreateAPIView):
    """Track page views"""
    serializer_class = PageViewSerializer
    permission_classes = []  # Public endpoint
    
    def perform_create(self, serializer):
        # Parse user agent
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        device_info = parse_user_agent(user_agent)
        
        # Get client IP
        ip_address = get_client_ip(self.request)
        
        # Get session ID
        session_id = self.request.session.session_key or self.request.data.get('session_id', '')
        
        serializer.save(
            user=self.request.user if self.request.user.is_authenticated else None,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=device_info.get('device_type', ''),
            browser=device_info.get('browser', ''),
            os=device_info.get('os', '')
        )


class UserBehaviorCreateView(generics.CreateAPIView):
    """Track user behavior events"""
    serializer_class = UserBehaviorSerializer
    permission_classes = []  # Public endpoint
    
    def perform_create(self, serializer):
        session_id = self.request.session.session_key or self.request.data.get('session_id', '')
        
        serializer.save(
            user=self.request.user if self.request.user.is_authenticated else None,
            session_id=session_id
        )
        
        # Handle specific events
        event_type = serializer.validated_data.get('event_type')
        event_data = serializer.validated_data.get('event_data', {})
        
        if event_type == 'add_to_cart' and 'product_id' in event_data:
            # Track product view when added to cart
            ProductView.objects.create(
                user=self.request.user if self.request.user.is_authenticated else None,
                session_id=session_id,
                product_id=event_data['product_id'],
                source='add_to_cart'
            )


class ProductViewCreateView(generics.CreateAPIView):
    """Track product views"""
    serializer_class = ProductViewSerializer
    permission_classes = []  # Public endpoint
    
    def perform_create(self, serializer):
        session_id = self.request.session.session_key or self.request.data.get('session_id', '')
        
        serializer.save(
            user=self.request.user if self.request.user.is_authenticated else None,
            session_id=session_id
        )


class TrackCartAbandonmentView(generics.GenericAPIView):
    """Track cart abandonment"""
    permission_classes = []  # Public endpoint
    
    def post(self, request):
        session_id = request.session.session_key or request.data.get('session_id', '')
        user = request.user if request.user.is_authenticated else None
        
        # Get cart data
        if user:
            cart = Cart.objects.filter(user=user).first()
        else:
            cart = Cart.objects.filter(session_key=session_id).first()
        
        if not cart or not cart.items.exists():
            return Response({'message': 'No cart to track'}, status=status.HTTP_200_OK)
        
        # Calculate cart value
        cart_value = sum(
            item.product.price * item.quantity 
            for item in cart.items.all()
        )
        
        # Prepare cart data
        cart_data = {
            'items': [
                {
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'price': str(item.product.price)
                }
                for item in cart.items.all()
            ],
            'total_value': str(cart_value)
        }
        
        # Create or update abandonment record
        abandonment, created = CartAbandonment.objects.update_or_create(
            user=user,
            session_id=session_id,
            recovered=False,
            defaults={
                'cart_data': cart_data,
                'cart_value': cart_value,
                'abandoned_at': timezone.now()
            }
        )
        
        return Response({'message': 'Cart abandonment tracked'}, status=status.HTTP_200_OK)


class TrackConversionView(generics.GenericAPIView):
    """Track conversion when order is completed"""
    permission_classes = []  # Public endpoint
    
    def post(self, request):
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({'error': 'Order ID required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        session_id = request.session.session_key or request.data.get('session_id', '')
        
        # Get attribution data from session or request
        attribution_data = {
            'source': request.data.get('source', request.session.get('utm_source', '')),
            'medium': request.data.get('medium', request.session.get('utm_medium', '')),
            'campaign': request.data.get('campaign', request.session.get('utm_campaign', '')),
            'referrer': request.data.get('referrer', request.META.get('HTTP_REFERER', '')),
            'landing_page': request.data.get('landing_page', request.session.get('landing_page', ''))
        }
        
        # Create conversion record
        conversion = Conversion.objects.create(
            user=order.user,
            session_id=session_id,
            order=order,
            source=attribution_data['source'],
            medium=attribution_data['medium'],
            campaign=attribution_data['campaign'],
            referrer=attribution_data['referrer'],
            landing_page=attribution_data['landing_page'],
            conversion_value=order.total_amount,
            attribution_data=attribution_data
        )
        
        # Mark cart abandonment as recovered if exists
        CartAbandonment.objects.filter(
            user=order.user,
            session_id=session_id,
            recovered=False
        ).update(
            recovered=True,
            recovered_at=timezone.now(),
            recovery_order=order
        )
        
        return Response({'message': 'Conversion tracked'}, status=status.HTTP_200_OK)


# A/B Testing Views
class ABTestExperimentViewSet(viewsets.ModelViewSet):
    """Admin viewset for managing A/B test experiments"""
    queryset = ABTestExperiment.objects.all()
    serializer_class = ABTestExperimentSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate an experiment"""
        experiment = self.get_object()
        experiment.is_active = True
        experiment.save()
        return Response({'message': 'Experiment activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate an experiment"""
        experiment = self.get_object()
        experiment.is_active = False
        experiment.save()
        return Response({'message': 'Experiment deactivated'})
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get experiment results"""
        experiment = self.get_object()
        
        results = []
        for variant in experiment.variants:
            participants = experiment.participants.filter(variant=variant['name'])
            converted = participants.filter(converted=True)
            
            results.append({
                'variant': variant['name'],
                'participants': participants.count(),
                'conversions': converted.count(),
                'conversion_rate': (converted.count() / participants.count() * 100) if participants.count() > 0 else 0,
                'average_conversion_value': converted.aggregate(avg=Avg('conversion_value'))['avg'] or 0
            })
        
        return Response(results)


class GetABTestVariantView(generics.GenericAPIView):
    """Get A/B test variant for a user"""
    permission_classes = []  # Public endpoint
    
    def post(self, request):
        feature = request.data.get('feature')
        if not feature:
            return Response({'error': 'Feature name required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get active experiment for feature
        experiment = ABTestExperiment.objects.filter(
            feature=feature,
            is_active=True,
            start_date__lte=timezone.now()
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=timezone.now())
        ).first()
        
        if not experiment:
            return Response({'variant': 'control'})
        
        # Check if user should be included in test
        if random.randint(1, 100) > experiment.traffic_percentage:
            return Response({'variant': 'control'})
        
        # Get or create participant
        session_id = request.session.session_key or request.data.get('session_id', '')
        user = request.user if request.user.is_authenticated else None
        
        participant, created = ABTestParticipant.objects.get_or_create(
            experiment=experiment,
            user=user,
            session_id=session_id,
            defaults={
                'variant': self._assign_variant(experiment, session_id)
            }
        )
        
        return Response({
            'variant': participant.variant,
            'experiment_id': experiment.id
        })
    
    def _assign_variant(self, experiment, session_id):
        """Assign variant based on consistent hashing"""
        # Use session ID for consistent assignment
        hash_value = int(hashlib.md5(f"{experiment.id}-{session_id}".encode()).hexdigest(), 16)
        
        # Distribute evenly among variants
        variant_count = len(experiment.variants)
        variant_index = hash_value % variant_count
        
        return experiment.variants[variant_index]['name']


class RecordABTestConversionView(generics.GenericAPIView):
    """Record A/B test conversion"""
    permission_classes = []  # Public endpoint
    
    def post(self, request):
        experiment_id = request.data.get('experiment_id')
        conversion_value = request.data.get('conversion_value', 0)
        conversion_data = request.data.get('conversion_data', {})
        
        if not experiment_id:
            return Response({'error': 'Experiment ID required'}, status=status.HTTP_400_BAD_REQUEST)
        
        session_id = request.session.session_key or request.data.get('session_id', '')
        user = request.user if request.user.is_authenticated else None
        
        # Update participant conversion
        participant = ABTestParticipant.objects.filter(
            experiment_id=experiment_id,
            user=user,
            session_id=session_id
        ).first()
        
        if participant:
            participant.converted = True
            participant.conversion_value = conversion_value
            participant.conversion_data = conversion_data
            participant.save()
            
            return Response({'message': 'Conversion recorded'})
        
        return Response({'error': 'Participant not found'}, status=status.HTTP_404_NOT_FOUND)


# Admin Dashboard Views
class AdminDashboardView(generics.GenericAPIView):
    """Admin dashboard metrics"""
    permission_classes = [IsAdminUser]
    serializer_class = DashboardMetricsSerializer
    
    def get(self, request):
        # Get date range from query params
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Calculate metrics
        metrics = {
            'total_page_views': PageView.objects.filter(timestamp__gte=start_date).count(),
            'unique_visitors': PageView.objects.filter(timestamp__gte=start_date).values('session_id').distinct().count(),
            'conversion_rate': self._calculate_conversion_rate(start_date),
            'average_order_value': self._calculate_average_order_value(start_date),
            'cart_abandonment_rate': self._calculate_cart_abandonment_rate(start_date),
            'top_products': self._get_top_products(start_date),
            'revenue_by_day': self._get_revenue_by_day(start_date),
            'traffic_sources': self._get_traffic_sources(start_date)
        }
        
        serializer = self.get_serializer(data=metrics)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.data)
    
    def _calculate_conversion_rate(self, start_date):
        sessions = PageView.objects.filter(timestamp__gte=start_date).values('session_id').distinct().count()
        conversions = Conversion.objects.filter(timestamp__gte=start_date).count()
        
        if sessions == 0:
            return 0
        
        return (conversions / sessions) * 100
    
    def _calculate_average_order_value(self, start_date):
        avg_value = Order.objects.filter(
            created_at__gte=start_date
        ).aggregate(avg=Avg('total_amount'))['avg']
        
        return avg_value or 0
    
    def _calculate_cart_abandonment_rate(self, start_date):
        abandoned = CartAbandonment.objects.filter(
            abandoned_at__gte=start_date,
            recovered=False
        ).count()
        
        completed = Order.objects.filter(created_at__gte=start_date).count()
        
        total = abandoned + completed
        if total == 0:
            return 0
        
        return (abandoned / total) * 100
    
    def _get_top_products(self, start_date):
        top_products = OrderItem.objects.filter(
            order__created_at__gte=start_date
        ).values('product__id', 'product__name').annotate(
            total_sold=Sum('quantity'),
            revenue=Sum(F('quantity') * F('price'))
        ).order_by('-revenue')[:10]
        
        return list(top_products)
    
    def _get_revenue_by_day(self, start_date):
        revenue_data = Order.objects.filter(
            created_at__gte=start_date
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            revenue=Sum('total_amount')
        ).order_by('day')
        
        return list(revenue_data)
    
    def _get_traffic_sources(self, start_date):
        sources = Conversion.objects.filter(
            timestamp__gte=start_date
        ).exclude(source='').values('source').annotate(
            count=Count('id')
        )
        
        return {item['source']: item['count'] for item in sources}


class AdminProductPerformanceView(generics.ListAPIView):
    """Product performance analytics for admin"""
    permission_classes = [IsAdminUser]
    serializer_class = ProductPerformanceSerializer
    
    def get_queryset(self):
        days = int(self.request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        products = Product.objects.all()
        performance_data = []
        
        for product in products:
            views = ProductView.objects.filter(
                product=product,
                timestamp__gte=start_date
            )
            
            view_count = views.count()
            avg_duration = views.aggregate(avg=Avg('view_duration'))['avg'] or 0
            
            # Calculate add to cart rate
            add_to_cart_events = UserBehavior.objects.filter(
                event_type='add_to_cart',
                event_data__product_id=product.id,
                timestamp__gte=start_date
            ).count()
            
            add_to_cart_rate = (add_to_cart_events / view_count * 100) if view_count > 0 else 0
            
            # Calculate conversion rate and revenue
            order_items = OrderItem.objects.filter(
                product=product,
                order__created_at__gte=start_date
            )
            
            conversions = order_items.values('order').distinct().count()
            conversion_rate = (conversions / view_count * 100) if view_count > 0 else 0
            
            revenue = order_items.aggregate(
                total=Sum(F('quantity') * F('price'))
            )['total'] or 0
            
            performance_data.append({
                'product_id': product.id,
                'product_name': product.name,
                'views': view_count,
                'add_to_cart_rate': add_to_cart_rate,
                'conversion_rate': conversion_rate,
                'revenue': revenue,
                'average_view_duration': avg_duration
            })
        
        # Sort by revenue
        performance_data.sort(key=lambda x: x['revenue'], reverse=True)
        
        return performance_data
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AdminCustomerAnalyticsView(generics.ListAPIView):
    """Customer analytics for admin"""
    permission_classes = [IsAdminUser]
    serializer_class = CustomerAnalyticsSerializer
    
    def get_queryset(self):
        days = int(self.request.query_params.get('days', 365))
        start_date = timezone.now() - timedelta(days=days)
        
        customers = User.objects.filter(
            orders__created_at__gte=start_date
        ).distinct()
        
        customer_data = []
        
        for customer in customers:
            orders = customer.orders.filter(created_at__gte=start_date)
            
            total_orders = orders.count()
            lifetime_value = orders.aggregate(total=Sum('total_amount'))['total'] or 0
            avg_order_value = lifetime_value / total_orders if total_orders > 0 else 0
            last_order = orders.order_by('-created_at').first()
            
            # Get favorite categories
            favorite_categories = OrderItem.objects.filter(
                order__user=customer,
                order__created_at__gte=start_date
            ).values('product__category').annotate(
                count=Count('id')
            ).order_by('-count')[:3]
            
            customer_data.append({
                'customer_id': customer.id,
                'customer_email': customer.email,
                'total_orders': total_orders,
                'lifetime_value': lifetime_value,
                'average_order_value': avg_order_value,
                'last_order_date': last_order.created_at if last_order else None,
                'favorite_categories': [cat['product__category'] for cat in favorite_categories]
            })
        
        # Sort by lifetime value
        customer_data.sort(key=lambda x: x['lifetime_value'], reverse=True)
        
        return customer_data
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# Report Generation Views
class GenerateReportView(generics.CreateAPIView):
    """Generate various business reports"""
    serializer_class = ReportSerializer
    permission_classes = [IsAdminUser]
    
    def create(self, request):
        report_type = request.data.get('report_type')
        parameters = request.data.get('parameters', {})
        
        if report_type not in dict(Report.REPORT_TYPES):
            return Response(
                {'error': 'Invalid report type'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate report data based on type
        report_data = self._generate_report_data(report_type, parameters)
        
        # Create report record
        report = Report.objects.create(
            report_type=report_type,
            name=f"{dict(Report.REPORT_TYPES)[report_type]} - {timezone.now().strftime('%Y-%m-%d')}",
            parameters=parameters,
            data=report_data,
            generated_by=request.user
        )
        
        # Generate PDF if requested
        if request.data.get('generate_pdf', False):
            pdf_file = generate_report_pdf(report)
            report.file_path = pdf_file
            report.save()
        
        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def _generate_report_data(self, report_type, parameters):
        """Generate report data based on type"""
        start_date = datetime.fromisoformat(parameters.get('start_date', (timezone.now() - timedelta(days=30)).isoformat()))
        end_date = datetime.fromisoformat(parameters.get('end_date', timezone.now().isoformat()))
        
        if report_type == 'sales':
            return self._generate_sales_report(start_date, end_date)
        elif report_type == 'inventory':
            return self._generate_inventory_report()
        elif report_type == 'customer':
            return self._generate_customer_report(start_date, end_date)
        elif report_type == 'product':
            return self._generate_product_report(start_date, end_date)
        elif report_type == 'marketing':
            return self._generate_marketing_report(start_date, end_date)
        elif report_type == 'financial':
            return self._generate_financial_report(start_date, end_date)
        
        return {}
    
    def _generate_sales_report(self, start_date, end_date):
        """Generate sales report data"""
        orders = Order.objects.filter(
            created_at__range=[start_date, end_date]
        )
        
        return {
            'total_orders': orders.count(),
            'total_revenue': float(orders.aggregate(total=Sum('total_amount'))['total'] or 0),
            'average_order_value': float(orders.aggregate(avg=Avg('total_amount'))['avg'] or 0),
            'orders_by_status': dict(orders.values('status').annotate(count=Count('id'))),
            'top_selling_products': list(
                OrderItem.objects.filter(
                    order__created_at__range=[start_date, end_date]
                ).values('product__name').annotate(
                    quantity_sold=Sum('quantity'),
                    revenue=Sum(F('quantity') * F('price'))
                ).order_by('-revenue')[:10]
            )
        }
    
    def _generate_inventory_report(self):
        """Generate inventory report data"""
        products = Product.objects.all()
        
        return {
            'total_products': products.count(),
            'low_stock_products': list(
                products.filter(stock__lt=10).values('id', 'name', 'stock')
            ),
            'out_of_stock_products': list(
                products.filter(stock=0).values('id', 'name')
            ),
            'inventory_value': float(
                products.aggregate(
                    total=Sum(F('stock') * F('price'))
                )['total'] or 0
            )
        }
    
    def _generate_customer_report(self, start_date, end_date):
        """Generate customer report data"""
        new_customers = User.objects.filter(
            date_joined__range=[start_date, end_date]
        ).count()
        
        active_customers = User.objects.filter(
            orders__created_at__range=[start_date, end_date]
        ).distinct().count()
        
        return {
            'new_customers': new_customers,
            'active_customers': active_customers,
            'customer_retention_rate': self._calculate_retention_rate(start_date, end_date),
            'top_customers': list(
                User.objects.filter(
                    orders__created_at__range=[start_date, end_date]
                ).annotate(
                    total_spent=Sum('orders__total_amount')
                ).order_by('-total_spent')[:10].values(
                    'id', 'email', 'total_spent'
                )
            )
        }
    
    def _generate_product_report(self, start_date, end_date):
        """Generate product performance report"""
        return {
            'product_views': ProductView.objects.filter(
                timestamp__range=[start_date, end_date]
            ).count(),
            'conversion_metrics': self._calculate_product_conversions(start_date, end_date),
            'category_performance': self._calculate_category_performance(start_date, end_date)
        }
    
    def _generate_marketing_report(self, start_date, end_date):
        """Generate marketing report data"""
        conversions = Conversion.objects.filter(
            timestamp__range=[start_date, end_date]
        )
        
        return {
            'total_conversions': conversions.count(),
            'conversion_by_source': dict(
                conversions.values('source').annotate(count=Count('id'))
            ),
            'conversion_by_campaign': dict(
                conversions.values('campaign').annotate(count=Count('id'))
            ),
            'revenue_by_source': dict(
                conversions.values('source').annotate(
                    revenue=Sum('conversion_value')
                )
            )
        }
    
    def _generate_financial_report(self, start_date, end_date):
        """Generate financial report data"""
        orders = Order.objects.filter(
            created_at__range=[start_date, end_date],
            status='delivered'
        )
        
        return {
            'gross_revenue': float(orders.aggregate(total=Sum('total_amount'))['total'] or 0),
            'total_orders': orders.count(),
            'revenue_by_category': self._calculate_revenue_by_category(start_date, end_date),
            'daily_revenue': self._calculate_daily_revenue(start_date, end_date)
        }
    
    def _calculate_retention_rate(self, start_date, end_date):
        """Calculate customer retention rate"""
        # Implementation depends on business logic
        return 75.5  # Placeholder
    
    def _calculate_product_conversions(self, start_date, end_date):
        """Calculate product conversion metrics"""
        # Implementation
        return {}
    
    def _calculate_category_performance(self, start_date, end_date):
        """Calculate category performance"""
        # Implementation
        return {}
    
    def _calculate_revenue_by_category(self, start_date, end_date):
        """Calculate revenue by category"""
        # Implementation
        return {}
    
    def _calculate_daily_revenue(self, start_date, end_date):
        """Calculate daily revenue"""
        # Implementation
        return []


class ReportListView(generics.ListAPIView):
    """List generated reports"""
    serializer_class = ReportSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = Report.objects.all()
        report_type = self.request.query_params.get('report_type')
        
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        
        return queryset


# Admin ViewSets for managing analytics data
class AdminPageViewViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin viewset for page views"""
    queryset = PageView.objects.all()
    serializer_class = AdminPageViewSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['user', 'page_url', 'device_type', 'browser']
    search_fields = ['page_url', 'user__username', 'user__email']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']


class AdminUserBehaviorViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin viewset for user behavior"""
    queryset = UserBehavior.objects.all()
    serializer_class = AdminUserBehaviorSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['user', 'event_type', 'session_id']
    search_fields = ['event_name', 'user__username', 'user__email']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']


class AdminProductViewViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin viewset for product views"""
    queryset = ProductView.objects.all()
    serializer_class = AdminProductViewSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['user', 'product', 'source']
    search_fields = ['product__name', 'user__username', 'user__email']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']


class AdminCartAbandonmentViewSet(viewsets.ModelViewSet):
    """Admin viewset for cart abandonment"""
    queryset = CartAbandonment.objects.all()
    serializer_class = AdminCartAbandonmentSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['user', 'recovered', 'email_sent']
    search_fields = ['user__username', 'user__email']
    ordering_fields = ['abandoned_at']
    ordering = ['-abandoned_at']
    
    @action(detail=True, methods=['post'])
    def send_recovery_email(self, request, pk=None):
        """Send cart recovery email"""
        abandonment = self.get_object()
        
        if not abandonment.user or not abandonment.user.email:
            return Response(
                {'error': 'No user email available'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Send recovery email (implement email sending logic)
        # from utils.email import send_cart_recovery_email
        # send_cart_recovery_email(abandonment)
        
        abandonment.email_sent = True
        abandonment.email_sent_at = timezone.now()
        abandonment.save()
        
        return Response({'message': 'Recovery email sent'})


class AdminConversionViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin viewset for conversions"""
    queryset = Conversion.objects.all()
    serializer_class = AdminConversionSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['user', 'source', 'medium', 'campaign']
    search_fields = ['user__username', 'user__email', 'order__order_number']
    ordering_fields = ['timestamp', 'conversion_value']
    ordering = ['-timestamp']
